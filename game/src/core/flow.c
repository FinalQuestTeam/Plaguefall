// Fluxo do jogo: máquina de estados e laço principal. Ficava no main.c; foi
// movido para cá para que o main tenha só o mínimo. As telas específicas vivem
// em seus módulos (title, help, splash, pause, test); aqui só a orquestração.

#include <genesis.h>

#include "core/flow.h"
#include "core/game.h"
#include "system/video/screens/title.h"
#include "system/video/screens/splash.h"
#include "system/video/tilegen.h"
#include "system/video/spritelist.h"
#include "system/video/chars.h"
#include "system/video/enemygfx.h"
#include "system/video/floor.h"
#include "system/video/flash.h"
#include "system/video/screens/hud.h"
#include "system/video/screens/pause.h"
#include "core/inventory.h"
#include "core/objective.h"
#include "actors/npc.h"
#include "system/audio/sfx.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "actors/player.h"
#include "actors/shots.h"
#include "actors/bomb.h"
#include "levels/levels.h"
#include "levels/test.h"
#include "enemies/enemies.h"
#include "items/items.h"

// estados do jogo (a tela-título/splash rodam antes)
typedef enum { ST_PREP, ST_PLAY, ST_PAUSE, ST_OVER, ST_DONE, ST_END } GameState;

bool bossDefeated;      // chefe morto (fase 16) — dispara a tela de fim

#define FIRST_SPAWN_S   1   // atraso do 1º inimigo da fase (s); demais = intervalo da fase

// estado compartilhado (declarado em game.h)
bool gameOver;
u16 fps;
u16 ENEMY_CD;                   // 1 tiro inimigo a cada 2 s

static GameState state;
static u8 pendingLevel;         // fase mostrada na tela de preparação

static u16 kills;
static u16 spawnTimer;
static u16 freezeTimer;         // fase congelada ao começar (3 s de contagem)
static u16 doneTimer;           // fase concluída: espera antes da próxima tela
static u16 prevJoy;             // estado anterior do joypad (detecção de borda)

// ---------------------------------------------------------------------------
// Telas e fluxo de fases
// ---------------------------------------------------------------------------

// tela de preparação: condições da fase, começa com A
static void showPrep(u8 level)
{
    pendingLevel = level;
    state = ST_PREP;
    SFX_silence();
    MUSIC_setEnemies(0);        // preparação: música calma

    // some com os sprites da fase anterior ANTES da limpeza e da geração de
    // arte (LEVEL_loadGfx é pesado): sem o flush, os inimigos congelados
    // ficariam visíveis sobre a tela preta durante toda a carga
    SPRITES_hide();
    SYS_doVBlankProcess();      // aplica a lista vazia já neste quadro

    VDP_clearPlane(BG_A, TRUE);
    FLOOR_clear();              // tela de preparação sem o chão

    LEVEL_loadGfx(level);               // gera a arte dos inimigos desta fase (VRAM)

    char buf[12];
    sprintf(buf, "FASE %d", level);
    VDP_drawText(buf, 17, 5);
    LEVEL_drawInfo(level, 8, 8);        // inclui os sprites dos inimigos (linha y+8)
    VDP_drawText("APERTE A PARA COMECAR", 9, 20);
}

// começa (ou recomeça) uma fase; a vida NÃO reseta (persiste entre fases)
static void startPhase(u8 level)
{
    AUDIO_silenceAll();         // cala o PSG antes da carga pesada (sem nota presa)
    LEVEL_load(level);
    FLOOR_draw(LEVEL_current()->floor);     // chão configurado por fase (def)
    ENEMIES_clear();
    ITEMS_clear();
    SHOTS_clear();
    PLAYER_reset();
    CHARS_load(PLAYER_CHAR);    // mech do jogador: 3 direções na VRAM + paleta (PAL2)

    kills = 0;
    gameOver = FALSE;
    bossDefeated = FALSE;
    if (level == LEVEL_COUNT)   // fase 16: só o chefe (gerado uma vez)
        ENEMIES_spawnAt(ENEMY_BOSS, 140, 40);
    spawnTimer = FIRST_SPAWN_S * fps;   // 1º inimigo aparece logo no início
    freezeTimer = fps * 3;      // 3 s de contagem antes de o jogador assumir

    SFX_silence();
    FLASH_stop();
    const LevelDef *def = LEVEL_current();
    OBJECTIVE_start(def);                    // objetivo da fase (timer/NPC/contagem)
    MUSIC_setRamp(def->musCalmUntil, def->musEnemyMax,   // curva de BPM da fase
                  def->musStepCalm,  def->musStepHot);
    OBJECTIVE_drawHUD(kills);
    HUD_drawLife(hp);
    HUD_drawInventory();
    state = ST_PLAY;
}

// FASE TESTE (currentLevel == 0): sandbox no estágio dado (1/2). A lógica do
// sandbox (porta, inimigos, infos) fica em levels/test.c.
static void startTest(u8 stage)
{
    AUDIO_silenceAll();         // cala o PSG antes da carga pesada (sem nota presa)
    testStage = stage;
    LEVEL_load(0);              // arena + HUD "FASE TESTE n"
    FLOOR_draw(LEVEL_current()->floor);     // chão configurado por fase (def)
    ENEMIES_clear();
    ITEMS_clear();
    SHOTS_clear();
    PLAYER_reset();
    CHARS_load(PLAYER_CHAR);    // mech do jogador: 3 direções na VRAM + paleta (PAL2)
    PLAYER_fullHp();
    BOMB_reset();
    SHOTS_resetPower();
    SHOTS_resetChain();
    PLAYER_resetSpeed();

    kills = 0;
    gameOver = FALSE;
    freezeTimer = 0;           // sem contagem regressiva no teste

    SFX_silence();
    FLASH_stop();
    TEST_draw();               // porta + timer de aparição dos alvos
    const LevelDef *def = LEVEL_current();
    OBJECTIVE_start(def);                    // estágios 4/5/6 têm objetivo
    MUSIC_setRamp(def->musCalmUntil, def->musEnemyMax,   // curva de BPM da fase
                  def->musStepCalm,  def->musStepHot);
    OBJECTIVE_drawHUD(kills);
    HUD_drawLife(hp);
    HUD_drawInventory();
    state = ST_PLAY;
}

// contagem regressiva do início da fase; devolve TRUE enquanto congelado
static bool tickFreeze(void)
{
    if (freezeTimer == 0) return FALSE;

    freezeTimer--;
    if (freezeTimer == 0)
    {
        VDP_clearTextArea(14, 2, 12, 1);
    }
    else
    {
        char buf[16];
        sprintf(buf, "PREPARE-SE %d", (freezeTimer + fps - 1) / fps);
        VDP_drawText(buf, 14, 2);
    }
    return TRUE;
}

// ---------------------------------------------------------------------------
// Um quadro de jogo ativo (ST_PLAY, fora do congelamento)
// ---------------------------------------------------------------------------
static void updatePlay(u16 joy, u16 pressed)
{
    (void) pressed;             // B (bomba) agora é ativação do inventário (flow)

    PLAYER_update(joy);
    LEVEL_update();                 // elementos da fase (ex.: lava/lama)
    if (gameOver) return;

    // alvo da perseguição dos inimigos: o aliado no PROTEGER, senão o jogador
    if (LEVEL_current()->objective == OBJ_PROTECT && NPC_active())
        ENEMIES_setChaseTarget(npcX + NPC_SIZE / 2, npcY + NPC_SIZE / 2);
    else
        ENEMIES_setChaseTarget(px + 8, py + 8);

    kills += SHOTS_updatePlayer();
    SHOTS_updateEnemy();
    kills += ENEMIES_update();      // + mortes pela queimadura (fogo)
    MUSIC_setEnemies(ENEMIES_activeCount());   // + inimigos = BPM sobe (perigo)
    ITEMS_update();

    if (gameOver) return;

    // FASE TESTE: lógica do sandbox vive em levels/test.c; se o jogador cruzou
    // a porta, TEST_update devolve o estágio a (re)carregar
    if (currentLevel == 0)
    {
        const u8 next = TEST_update();
        if (next) { startTest(next); return; }

        // estágios de objetivo (4/5/6): roda a meta e reinicia o estágio ao
        // concluir/falhar (é uma demonstração em loop, sem prep nem game over)
        if (LEVEL_current()->objective != OBJ_KILL)
        {
            const u8 st = OBJECTIVE_update(kills);
            OBJECTIVE_drawHUD(kills);
            if (st != OBJ_ONGOING) startTest(testStage);
        }
        return;
    }

    // FASE 16 (chefe): vencer = derrotar o chefe → tela de fim e volta ao título.
    // Sem meta por contagem nem spawn regular (só o chefe e seus lacaios).
    if (currentLevel == LEVEL_COUNT)
    {
        if (bossDefeated)
        {
            SFX_silence();
            FLOOR_clear();
            VDP_clearPlane(BG_A, TRUE);
            VDP_drawText("PARABENS! FIM", 13, 9);
            VDP_drawText("VOCE DERROTOU A LACRAIA!", 8, 12);
            VDP_drawText("APERTE START", 14, 15);
            state = ST_END;
        }
        return;
    }

    // objetivo da fase (matar N / sobreviver / coletar / proteger o aliado)
    const u8 obj = OBJECTIVE_update(kills);
    OBJECTIVE_drawHUD(kills);
    if (obj == OBJ_WON)
    {
        // fase completa: mensagem por 3 s antes da próxima tela; os itens no
        // chão somem na hora (não dá mais para coletar na cena congelada)
        state = ST_DONE;
        doneTimer = fps * 3;
        SFX_silence();
        ITEMS_clear();
        NPC_clear();
        VDP_drawText("FASE CONCLUIDA!", 12, 13);
        return;
    }
    if (obj == OBJ_LOST)            // aliado caiu: falha (recomeça a fase pelo START)
    {
        SFX_silence();
        VDP_drawText("O ALIADO CAIU!", 13, 12);
        VDP_drawText("APERTE START", 14, 14);
        gameOver = TRUE;            // o laço ST_PLAY vê gameOver e vai p/ ST_OVER
        return;
    }

    if (spawnTimer) spawnTimer--;
    else
    {
        const LevelDef *def = LEVEL_current();
        const u16 batch = def->spawnCount ? def->spawnCount : 1;
        for (u16 i = 0; i < batch; i++)
            ENEMIES_trySpawn(def->enemyTypes, def->enemyTypeCount);
        spawnTimer = def->spawnSeconds * fps;
    }
}

// ---------------------------------------------------------------------------
// Inicialização e laço principal
// ---------------------------------------------------------------------------
void FLOW_run(void)
{
    fps = IS_PAL_SYSTEM ? 50 : 60;
    ENEMY_CD = fps * 2;

    SPLASH_run();               // abertura: logo da desenvolvedora (sem música ainda)

    // tiles e paleta dos objetos (uma vez; título/pausa usam texto em PAL0).
    // A arte dos inimigos é gerada POR FASE (LEVEL_loadGfx), não aqui — start
    // instantâneo e menos VRAM.
    TILEGEN_init();
    FLOOR_init();               // tiles + paleta (PAL3) do chão; desenhado por fase
    VDP_resetSprites();

    // música só DEPOIS de toda a geração de tiles do boot: o driver PCM (DAC via
    // Z80) é sensível à DMA — iniciá-la antes desregulava/embolava a reprodução
    MUSIC_init();
    MUSIC_start();

    // laço externo: TÍTULO → JOGO → (volta ao título pela pausa) → ...
    while (TRUE)
    {
        FLOOR_clear();          // menu/título sem o chão da arena
        MUSIC_setEnemies(0);    // título/menu: música calma
        const u8 choice = TITLE_run();

        VDP_setTextPlane(BG_A);
        VDP_setTextPalette(PAL0);
        PLAYER_fullHp();
        BOMB_reset();
        SHOTS_resetPower();
        SHOTS_resetChain();
        PLAYER_resetSpeed();
        INV_clear();                            // inventário zerado a cada jogo novo

        if (choice == TITLE_TEST) startTest(1); // fase teste (começa no estágio 1)
        else showPrep(1);                       // novo jogo (fase 1)

        // sincroniza o joypad: o START/A usado no menu não vaza como toque novo
        prevJoy = JOY_readJoypad(JOY_1);

        // C troca a seleção do inventário; B ativa o item selecionado.
        // Pular fase (debug) virou combo A+B+C.
        bool comboDone = FALSE;

        bool backToTitle = FALSE;
        while (!backToTitle)
        {
            const u16 joy = JOY_readJoypad(JOY_1);
            const u16 pressed = joy & ~prevJoy;
            prevJoy = joy;

            // por padrão sem ambiente; lava/lama religam durante o jogo ativo
            SFX_ambient(SFX_AMB_NONE);

            switch (state)
            {
                case ST_PREP:
                    if (pressed & BUTTON_A) startPhase(pendingLevel);
                    else if (pressed & BUTTON_C)    // C: avança de fase na preparação
                        showPrep((pendingLevel % LEVEL_COUNT) + 1);
                    SPRITES_hide();
                    break;

                case ST_PLAY:
                    if (tickFreeze())               // contagem regressiva de 3 s
                    {
                        SPRITES_draw();
                        break;
                    }

                    // pular fase (debug): combo A+B+C segurados (uma vez por combo)
                    if ((joy & BUTTON_A) && (joy & BUTTON_B) && (joy & BUTTON_C))
                    {
                        if (!comboDone)
                        {
                            comboDone = TRUE;
                            startPhase((currentLevel % LEVEL_COUNT) + 1);
                            break;
                        }
                    }
                    else
                    {
                        comboDone = FALSE;
                        // inventário: C troca a seleção; B ativa o selecionado
                        if (pressed & BUTTON_C) INV_cycle();
                        if (pressed & BUTTON_B)
                        {
                            const u16 bk = INV_activate();      // bomba devolve mortes
                            if (bk) { kills += bk; HUD_drawKills(kills, LEVEL_current()->killTarget); }
                        }
                    }

                    if (pressed & BUTTON_START)     // pausa com as infos da fase
                    {
                        AUDIO_silenceAll();         // sem nota presa enquanto desenha a pausa
                        PAUSE_show();
                        state = ST_PAUSE;
                        break;
                    }

                    updatePlay(joy, pressed);
                    if (gameOver) state = ST_OVER;
                    HUD_drawInventoryIfDirty();      // só redesenha quando muda
                    SPRITES_draw();
                    break;

                case ST_PAUSE:
                    if (pressed & BUTTON_START)             // retoma o jogo
                    {
                        PAUSE_resume(kills);
                        state = ST_PLAY;
                    }
                    else if (pressed & BUTTON_B)            // sair ao título
                    {
                        backToTitle = TRUE;
                    }
                    SPRITES_hide();
                    break;

                case ST_OVER:
                    if (pressed & BUTTON_START)
                    {
                        if (currentLevel == 0) startTest(testStage); // reinicia o estágio de teste
                        else
                        {
                            PLAYER_fullHp();        // morreu: vida, bombas e tiros ao início
                            BOMB_reset();
                            SHOTS_resetPower();
                            SHOTS_resetChain();
                            PLAYER_resetSpeed();
                            INV_clear();
                            showPrep(currentLevel);
                        }
                    }
                    SPRITES_draw();
                    break;

                case ST_DONE:
                    // cena congelada com a mensagem de conclusão; no quadro da
                    // transição NÃO redesenha (showPrep acabou de esconder tudo)
                    if (doneTimer) { doneTimer--; SPRITES_draw(); }
                    else showPrep((currentLevel % LEVEL_COUNT) + 1);
                    break;

                case ST_END:
                    // fim de jogo (chefe derrotado): START volta ao título
                    if (pressed & BUTTON_START) backToTitle = TRUE;
                    SPRITES_hide();
                    break;
            }

            AUDIO_frameBegin();     // árbitro: música e SFX só REQUISITAM voz...
            MUSIC_update();
            SFX_update();
            AUDIO_frameEnd();       // ...e o árbitro escreve o PSG (1x por canal)
            FLASH_update();
            SYS_doVBlankProcess();
        }
    }
}
