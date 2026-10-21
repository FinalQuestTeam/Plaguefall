// Fluxo do jogo: máquina de estados e laço principal. Ficava no main.c; foi
// movido para cá para que o main tenha só o mínimo. As telas específicas vivem
// em seus módulos (title, help, splash, pause, test); aqui só a orquestração.

#include <genesis.h>

#include "core/flow.h"
#include "core/game.h"
#include "system/video/screens/title.h"
#include "system/video/screens/splash.h"
#include "system/video/screens/intro.h"
#include "system/video/screens/titlecard.h"
#include "system/video/tilegen.h"
#include "system/video/spritelist.h"
#include "system/video/herogfx.h"
#include "system/video/enemygfx.h"
#include "system/video/floor.h"
#include "system/video/flash.h"
#include "system/video/screens/hud.h"
#include "system/video/screens/pause.h"
#include "system/video/screens/panel.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/routemap.h"
#include "system/video/screens/story.h"
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
#include "levels/graph.h"
#include "core/stats.h"
#include "levels/test.h"
#include "enemies/enemies.h"
#include "items/items.h"

// estados do jogo (a tela-título/splash rodam antes)
typedef enum { ST_PREP, ST_PLAY, ST_PAUSE, ST_OVER, ST_DONE, ST_MAP, ST_STORY, ST_END } GameState;

// para onde ir quando a cena de história terminar (ST_STORY)
#define STORY_TO_PREP   0   // preparação do pendingLevel (cena de ANTES)
#define STORY_TO_MAP    1   // mapa de rotas (cena de DEPOIS)
#define STORY_TO_END    2   // tela de fim (cena após o chefe)

bool bossDefeated;      // chefe morto (fase 16) — dispara a tela de fim

#define FIRST_SPAWN_S   1   // atraso do 1º inimigo da fase (s); demais = intervalo da fase

// estado compartilhado (declarado em game.h)
bool gameOver;
u16 fps;
u16 ENEMY_CD;                   // 1 tiro inimigo a cada 2 s

static GameState state;
static u8 pendingLevel;         // nó do grafo mostrado na tela de preparação
static u8 storyThen;            // STORY_TO_*: destino ao fim da cena de história

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
    ARENA_leave();
    pendingLevel = level;
    state = ST_PREP;
    SFX_silence();
    MUSIC_setEnemies(0);        // preparação: música calma

    // some com os sprites da fase anterior ANTES da limpeza e da geração de
    // arte (LEVEL_loadGfx é pesado): sem o flush, os inimigos congelados
    // ficariam visíveis sobre a tela preta durante toda a carga
    SPRITES_hide();
    SYS_doVBlankProcess();      // aplica a lista vazia já neste quadro

    if(PANEL_begin())MISSION_show(level);
}

// mapa de rotas (após a fase concluída/história): destaca o pendingLevel
static void showMap(void)
{
    ARENA_leave();
    SPRITES_hide();
    SYS_doVBlankProcess();      // aplica a lista vazia já neste quadro
    VDP_clearPlane(BG_A, TRUE);
    FLOOR_clear();
    ROUTEMAP_show(currentLevel, pendingLevel);
    state = ST_MAP;
}

// tela de fim de jogo (chefe derrotado)
static void showEnd(void)
{
    ARENA_leave();
    FLOOR_clear();
    VDP_clearPlane(BG_A, TRUE);
    VDP_drawText("PARABENS! FIM", 13, 9);
    VDP_drawText("VOCE DERROTOU O ESCORPIAO!", 7, 12);
    VDP_drawText("APERTE START", 14, 15);
    state = ST_END;
}

// vai para a preparação do nó — tocando antes a HISTÓRIA de chegada, se o nó
// tem cena de ANTES inédita neste run (levels/story.c)
static void gotoPrep(u8 node)
{
    ARENA_leave();
    MUSIC_selectTrack(GRAPH[node].def->musicTrack);
    pendingLevel = node;
    if (STORYSCR_start(node, ANTES)) { storyThen = STORY_TO_PREP; state = ST_STORY; }
    else showPrep(node);
}

// começa (ou recomeça) uma fase; a vida NÃO reseta (persiste entre fases)
static void startPhase(u8 level)
{
    PANEL_end();
    AUDIO_silenceAll();         // cala o PSG antes da carga pesada (sem nota presa)
    LEVEL_load(level);
    FLOOR_draw(LEVEL_current()->floor);     // chão configurado por fase (def)
    ENEMIES_clear();
    ITEMS_clear();
    SHOTS_clear();
    PLAYER_reset();
    ARENA_camera();
    HERO_load();               // human protagonist: streamed 32x48 frame + PAL2

    kills = 0;
    gameOver = FALSE;
    bossDefeated = FALSE;
    STATS_reset();              // estatísticas da fase (condições de saída do grafo)
    ROUTEMAP_markVisited(level);    // caminho percorrido (mapa de rotas)
    if (GRAPH_isFinal(level))   // nó final = fase do chefe (gerado uma vez)
        ENEMIES_spawnAt(ENEMY_BOSS, 140, 40);
    spawnTimer = FIRST_SPAWN_S * fps;   // 1º inimigo aparece logo no início
    freezeTimer = fps * 3;      // 3 s de contagem antes de o jogador assumir

    SFX_silence();
    FLASH_stop();
    const LevelDef *def = LEVEL_current();
    OBJECTIVE_start(def);                    // objetivo da fase (timer/NPC/contagem)
    MUSIC_selectTrack(def->musicTrack);
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
    ARENA_camera();
    HERO_load();               // human protagonist: streamed 32x48 frame + PAL2
    PLAYER_fullHp();
    BOMB_reset();
    SHOTS_resetPower();
    SHOTS_resetChain();
    PLAYER_resetSpeed();

    kills = 0;
    gameOver = FALSE;
    STATS_reset();             // os estágios de objetivo (4/5/6) também zeram
    freezeTimer = 0;           // sem contagem regressiva no teste

    SFX_silence();
    FLASH_stop();
    TEST_draw();               // porta + timer de aparição dos alvos
    const LevelDef *def = LEVEL_current();
    OBJECTIVE_start(def);                    // estágios 4/5/6 têm objetivo
    MUSIC_selectTrack(def->musicTrack);
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
        ARENA_gameView();
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

    STATS_tick();               // tempo de fase (condições de saída por tempo)
    PLAYER_update(joy);
    ARENA_camera();
    LEVEL_update();                 // elementos da fase (ex.: lava/lama)
    if (gameOver) return;

    // alvo da perseguição dos inimigos: o aliado no PROTEGER, senão o jogador
    if (LEVEL_current()->objective == OBJ_PROTECT && NPC_active())
        ENEMIES_setChaseTarget(npcX + NPC_size() / 2, npcY + NPC_size() / 2);
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

    // NÓ FINAL (chefe): vencer = derrotar o chefe → tela de fim e volta ao
    // título. Sem meta por contagem nem spawn regular (só o chefe e lacaios).
    if (GRAPH_isFinal(currentLevel))
    {
        if (bossDefeated)
        {
            SFX_silence();
            // história do fim (se inédita) antes da tela de parabéns
            MUSIC_selectTrack(MUSIC_TRACK_ENTARDECER);
            if (STORYSCR_start(currentLevel, DEPOIS))
            { storyThen = STORY_TO_END; state = ST_STORY; }
            else showEnd();
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
        ARENA_overlay();
        state = ST_DONE;
        doneTimer = fps * 3;
        SFX_silence();
        ITEMS_clear();
        NPC_clear();
        VDP_drawText("FASE CONCLUIDA!", 12, 13);
        return;
    }
    if (obj == OBJ_LOST)            // objetivo falhou (ex.: aliado caiu)
    {
        SFX_silence();
        ARENA_overlay();
        VDP_drawText("O ALIADO CAIU!", 13, 12);

        // se o nó tem rota de falha (EXIT OBJ_FALHOU no grafo), a falha NÃO é
        // game over: a fase encerra e o GRAPH_resolve segue por essa saída
        if (GRAPH_hasFailExit(currentLevel))
        {
            VDP_drawText("A MISSAO CONTINUA...", 10, 14);
            phaseStats.objFailed = TRUE;
            state = ST_DONE;
            doneTimer = fps * 3;
            ITEMS_clear();
            NPC_clear();
            return;
        }

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
    if (!TITLECARD_run())       // START skips from APRESENTA or the Plaguefall logo
        INTRO_run();                // monologo ilustrado: uma vez no boot, antes do menu

    // tiles e paleta dos objetos (uma vez; título/pausa usam texto em PAL0).
    // A arte dos inimigos é gerada POR FASE (LEVEL_loadGfx), não aqui — start
    // instantâneo e menos VRAM.
    TILEGEN_init();
    // O menu cobre os tiles do chao; TITLEBG_release os gera ao sair do titulo.
    // Evita uma geracao inutil na transicao entre o monologo e o menu.
    VDP_resetSprites();

    // música só DEPOIS de toda a geração de tiles do boot: o driver PCM (DAC via
    // Z80) é sensível à DMA — iniciá-la antes desregulava/embolava a reprodução
    MUSIC_init();
    MUSIC_start();

    // laço externo: TÍTULO → JOGO → (volta ao título pela pausa) → ...
    while (TRUE)
    {
        ARENA_leave();
        MUSIC_selectTrack(MUSIC_DEFAULT_TRACK);
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
        ROUTEMAP_reset();                       // novo run: caminho do mapa zerado
        STORYSCR_reset();                       // novo run: cenas de história de novo

        if (choice == TITLE_TEST) startTest(1); // fase teste (começa no estágio 1)
        else gotoPrep(1);                       // novo jogo (história + fase 1)

        // sincroniza o joypad: o START/A usado no menu não vaza como toque novo
        prevJoy = JOY_readJoypad(JOY_1);

        // C troca a seleção do inventário; B ativa o item selecionado.
        // Atalhos de desenvolvimento exigem DEV_SHORTCUTS; ausentes no release.
#ifdef DEV_SHORTCUTS
        bool comboDone = FALSE;
#endif

        bool backToTitle = FALSE;
        while (!backToTitle)
        {
            const u16 joy = JOY_readJoypad(JOY_1);
            const u16 pressed = joy & ~prevJoy;
            prevJoy = joy;

            // por padrão sem ambiente; lava/lama religam durante o jogo ativo
            SFX_ambient(SFX_AMB_NONE);

            const GameState frameState=state;
            switch (state)
            {
                case ST_PREP:
                    if (pressed & BUTTON_A) startPhase(pendingLevel);
#ifdef DEV_SHORTCUTS
                    else if (pressed & BUTTON_C)    // C: percorre os nós (debug)
                        showPrep((pendingLevel % NODE_COUNT) + 1);
#endif
                    SPRITES_hide();
                    break;

                case ST_PLAY:
                    if (tickFreeze())               // contagem regressiva de 3 s
                    {
                        SPRITES_draw();
                        break;
                    }

#ifdef DEV_SHORTCUTS
                    // pular fase (debug): combo A+B+C segurados (uma vez por combo)
                    if ((joy & BUTTON_A) && (joy & BUTTON_B) && (joy & BUTTON_C))
                    {
                        if (!comboDone)
                        {
                            comboDone = TRUE;
                            // segue a rota padrão (SENAO); do nó final volta ao 1
                            const u8 nx = GRAPH_defaultNext(currentLevel);
                            startPhase(nx ? nx : 1);
                            break;
                        }
                    }
                    else
                    {
                        comboDone = FALSE;
#else
                    {
#endif
                        // inventário: C troca a seleção; B ativa o selecionado
                        if (pressed & BUTTON_C) INV_cycle();
                        if (pressed & BUTTON_B)
                        {
                            const u16 bk = INV_activate();      // bomba devolve mortes
                            // o HUD do objetivo se atualiza no updatePlay
                            // deste mesmo quadro (não desenhar mortes aqui:
                            // a fase pode ter objetivo de tempo/coleta)
                            if (bk) kills += bk;
                        }
                    }

                    if (pressed & BUTTON_START)     // pausa com as infos da fase
                    {
                        AUDIO_silenceAll();         // sem nota presa enquanto desenha a pausa
                        if(PAUSE_show(kills))state = ST_PAUSE;
                        break;
                    }

                    updatePlay(joy, pressed);
                    if (gameOver) { ARENA_overlay(); state = ST_OVER; }
                    HUD_drawInventoryIfDirty();      // só redesenha quando muda
                    SPRITES_draw();
                    break;

                case ST_PAUSE:
                {
                    const u8 action=PAUSE_update(pressed);
                    if(action==PAUSE_RESUME)state=ST_PLAY;
                    else if(action==PAUSE_EXIT)backToTitle=TRUE;
                    SPRITES_hide();
                    break;
                }

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
                            gotoPrep(currentLevel);     // cena já vista: vai direto
                        }
                    }
                    SPRITES_draw();
                    break;

                case ST_DONE:
                    // cena congelada com a mensagem de conclusão; no quadro da
                    // transição NÃO redesenha (showPrep acabou de esconder tudo)
                    if (doneTimer) { doneTimer--; SPRITES_draw(); }
                    else
                    {
                        // saída do grafo conforme as estatísticas da fase
                        // (bomba/dano/tempo/falha); nó final não passa por aqui
                        pendingLevel = GRAPH_resolve(currentLevel);
                        if (!pendingLevel) pendingLevel = 1;

                        // história do DEPOIS (se inédita), depois o mapa
                        if (STORYSCR_start(currentLevel, DEPOIS))
                        { storyThen = STORY_TO_MAP; state = ST_STORY; }
                        else showMap();
                    }
                    break;

                case ST_STORY:
                    // cena de diálogo; ao terminar (ou pular), segue o destino
                    if (STORYSCR_update(pressed))
                    {
                        if (storyThen == STORY_TO_PREP)     showPrep(pendingLevel);
                        else if (storyThen == STORY_TO_MAP) showMap();
                        else                                showEnd();
                    }
                    SPRITES_hide();
                    break;

                case ST_MAP:
                    // mapa de rotas: A (ou START) segue (história de ANTES,
                    // se o nó destino tiver, e então a preparação)
                    if (ROUTEMAP_update(pressed))
                    {
                        ROUTEMAP_release();
                        gotoPrep(pendingLevel);
                    }
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
            // Pause/guide/panel palettes stay stable; gameplay feedback still
            // decays on the frozen victory and game-over views.
            if((frameState==ST_PLAY && state==ST_PLAY) || state==ST_DONE || state==ST_OVER)FLASH_update();
            SYS_doVBlankProcess();
        }
    }
}
