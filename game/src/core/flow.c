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
#include "system/video/combatgfx.h"
#include "system/video/actordeath.h"
#include "system/video/floor.h"
#include "system/video/flash.h"
#include "system/video/screens/hud.h"
#include "system/video/screens/pause.h"
#include "system/video/screens/panel.h"
#include "system/video/screens/result.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/routemap.h"
#include "system/video/screens/story.h"
#include "system/video/screens/loading.h"
#include "core/inventory.h"
#include "core/death.h"
#include "core/objective.h"
#include "actors/npc.h"
#include "actors/dinorah.h"
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
#include "levels/operations.h"
#include "levels/campaign_resistance.h"
#include "levels/campaign_launch.h"
#include "core/campaign_state.h"
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
static u8 settleKind;       //1 stage result,2 boss dialogue,3 defeat,4 fail exit,5 training failure
static u16 settleTimer;
static volatile u16 freezeTimer; // diagnostic: zero; preparation owns the only countdown
static u16 prevJoy;             // estado anterior do joypad (detecção de borda)
static volatile bool transitioning; // observable while blocking screen loads run

// Keep audio running through one fade on each side of a complete screen load.
// Screen owners preserve the disabled display until the next screen is ready.
static void transitionFrames(void)
{
    while(PAL_isDoingFade())
    {
        AUDIO_frameBegin();MUSIC_update();SFX_update();AUDIO_frameEnd();
        SYS_doVBlankProcess();
    }
}
static void beginTransition(void)
{
    LOADING_workBegin();
    transitioning=TRUE;
    PAL_fadeOutAll((fps+9)/10,TRUE);transitionFrames();
    VDP_setEnable(FALSE);
}
static void endTransition(void)
{
    u16 colors[64];PAL_getColors(0,colors,64);
    PAL_setColors(0,palette_black,64,DMA);VDP_setEnable(TRUE);
    PAL_fadeInAll(colors,(fps+9)/10,TRUE);transitionFrames();
    prevJoy=JOY_readJoypad(JOY_1);
    transitioning=FALSE;
    LOADING_workEnd();
}
static void beginContentTransition(void)
{
    LOADING_workBegin();transitioning=TRUE;
}
static void endContentTransition(void)
{
    prevJoy=JOY_readJoypad(JOY_1);transitioning=FALSE;LOADING_workEnd();
}

// ---------------------------------------------------------------------------
// Telas e fluxo de fases
// ---------------------------------------------------------------------------

// tela de preparação: condições da fase, começa com A
static void showPrep(u8 level)
{
    DINORAH_clear();
    if(!PANEL_isMission())ARENA_leave();
    pendingLevel = level;
    state = ST_PREP;
    SFX_silence();
    MUSIC_setEnemies(0);        // preparação: música calma

    // some com os sprites da fase anterior ANTES da limpeza e da geração de
    // arte (LEVEL_loadGfx é pesado): sem o flush, os inimigos congelados
    // ficariam visíveis sobre a tela preta durante toda a carga
    SPRITES_hide();
    SYS_doVBlankProcess();      // aplica a lista vazia já neste quadro

    if(PANEL_beginMission(NULL))MISSION_show(level);
}

// mapa de rotas (após a fase concluída/história): destaca o pendingLevel
static void showMap(void)
{
    DINORAH_clear();
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
    // The final dialogue has released its full-screen panel. Rebuild only
    // the empty native chamber, without respawning actors or resetting stats.
    VDP_clearPlane(BG_A,TRUE);FLOOR_clear();
    LEVEL_draw(currentLevel);FLOOR_draw(LEVEL_current()->floor);
    RESULT_victory();state = ST_END;
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
    settleKind=0;settleTimer=0;
    PANEL_end();
    if(!LOADING_active())AUDIO_silenceAll();
    DINORAH_clear();
    LEVEL_load(level);
    FLOOR_draw(LEVEL_current()->floor);     // chão configurado por fase (def)
    ENEMIES_clear();
    ITEMS_clear();
    DEATH_startPhase(level);
    SHOTS_clear();
    ARENA_camera();
    HERO_load();               // human protagonist: streamed 32x48 frame + PAL2

    kills = 0;
    gameOver = FALSE;
    bossDefeated = FALSE;
    STATS_reset();              // estatísticas da fase (condições de saída do grafo)
    ROUTEMAP_markVisited(level);    // caminho percorrido (mapa de rotas)
    if (GRAPH_isFinal(level))   // nó final = fase do chefe (gerado uma vez)
        ENEMIES_spawnAt(ENEMY_BOSS, 140, arenaMinY);
    spawnTimer = FIRST_SPAWN_S * fps;   // 1º inimigo aparece logo no início
    freezeTimer = 0;            // preparation already counted 3/2/1

    if(!LOADING_active())SFX_silence();
    FLASH_stop();
    const LevelDef *def = LEVEL_current();
    OBJECTIVE_start(def);                    // objetivo da fase (timer/NPC/contagem)
    MUSIC_selectTrack(def->musicTrack);
    MUSIC_setRamp(def->musCalmUntil, def->musEnemyMax,   // curva de BPM da fase
                  def->musStepCalm,  def->musStepHot);
    OBJECTIVE_drawHUD(kills);LOADING_poll();
    HUD_drawLife(hp);LOADING_poll();
    HUD_drawInventory();LOADING_poll();
    if(!LOADING_active())state=ST_PLAY;
}

// Training: directly selectable rooms, outside the campaign graph.
static void startTest(u8 stage, bool retry)
{
    testCampaignMode=FALSE;
    const bool retryRules=retry && stage==TEST_RULE_ROOM;
    if(retryRules)DEATH_retry(TEST_ruleNode(),px,py);
    else DEATH_reset();
    settleKind=0;settleTimer=0;
    AUDIO_silenceAll();         // cala o PSG antes da carga pesada (sem nota presa)
    testStage = stage;
    SPRITES_hide();SYS_doVBlankProcess();ENEMYGFX_reset();
    DINORAH_clear();
    LEVEL_load(0);              // arena + HUD "FASE TESTE n"
    FLOOR_draw(LEVEL_current()->floor);     // chão configurado por fase (def)
    ENEMIES_clear();
    ITEMS_clear();
    SHOTS_clear();
    ARENA_camera();
    HERO_load();               // human protagonist: streamed 32x48 frame + PAL2
    if(!retryRules) {
        PLAYER_fullHp();
        BOMB_reset();
        SHOTS_resetPower();
        SHOTS_resetChain();
        PLAYER_resetSpeed();
        INV_clear();
    }

    kills = 0;
    gameOver = FALSE;
    STATS_reset();             // cada sala começa com estatísticas novas
    freezeTimer = 0;           // sem contagem regressiva no teste

    SFX_silence();
    FLASH_stop();
    const LevelDef *def = LEVEL_current();
    OBJECTIVE_start(def);
    MUSIC_selectTrack(def->musicTrack);
    MUSIC_setRamp(def->musCalmUntil, def->musEnemyMax,   // curva de BPM da fase
                  def->musStepCalm,  def->musStepHot);
    ARENA_gameView();
    if(TEST_objectiveRoom())OBJECTIVE_drawHUD(kills);
    TEST_begin(retryRules);
    HUD_drawLife(hp);
    HUD_drawInventory();
    state = ST_PLAY;
}

static void finishSettled(void)
{
    const u8 kind=settleKind;settleKind=0;settleTimer=0;
    SFX_silence();FLASH_stop();
    if(currentLevel && (kind==1 || kind==2 || kind==4))CAMPAIGN_record(currentLevel,kind==4);
    if(kind==2)
    {
        LOADING_workBegin();
        MUSIC_selectTrack(MUSIC_TRACK_ENTARDECER);
        if(STORYSCR_start(currentLevel,DEPOIS)){storyThen=STORY_TO_END;state=ST_STORY;}
        else showEnd();
        LOADING_workEnd();
    }
    else if(kind==3)
    {
        RESULT_defeat(kills);state=ST_OVER;
    }
    else if(kind==4)
    {
        phaseStats.objFailed=TRUE;state=ST_DONE;
        ITEMS_clear();NPC_clear();RESULT_complete(kills,TRUE);
    }
    else if(kind==5)
    {
        TEST_finish(OBJ_LOST);
    }
    else
    {
        state=ST_DONE;ITEMS_clear();NPC_clear();RESULT_complete(kills,FALSE);
    }
}
static void settleDeath(u8 kind)
{
    if(kind==3) {
        const u8 node=currentLevel ? currentLevel : testStage==TEST_RULE_ROOM ? TEST_ruleNode() : 0;
        if(node)DEATH_capture(node,px,py);
    }
    if(kind>=3) {
        SFX_silence();FLASH_stop();
        if(hp<=0)ACTORDEATH_start(ACTOR_DEATH_HERO,faceX<0);
    }
    settleKind=kind;settleTimer=COMBATGFX_remaining();
    if(!settleTimer && !ACTORDEATH_pending())finishSettled();
}

// ---------------------------------------------------------------------------
// Um quadro de jogo ativo (ST_PLAY, fora do congelamento)
// ---------------------------------------------------------------------------
#ifdef OPS_PROFILE
volatile u16 playProfileTicks[4];
#define PLAY_PROFILE_START() u32 playClock=getSubTick()
#define PLAY_PROFILE_MARK(i) do{u32 now=getSubTick();playProfileTicks[i]=now-playClock;playClock=now;}while(0)
#else
#define PLAY_PROFILE_START()
#define PLAY_PROFILE_MARK(i)
#endif
static void updatePlay(u16 joy, u16 pressed)
{
    if(currentLevel==0) {
        if(testResult){COMBATGFX_update();if(OPS_active())OPS_animateResult();return;}
        if(testStage==TEST_DEATH_ROOM)TEST_deathInput(pressed);
        else if(testStage==TEST_RULE_ROOM)TEST_ruleInput(pressed);
        TEST_beforeUpdate();
    }
    if(currentLevel || TEST_effectTick())COMBATGFX_update();
    if(!currentLevel && testStage==TEST_DEATH_ROOM){TEST_afterUpdate();return;}
    STATS_tick();               // tempo de fase (condições de saída por tempo)
    if(currentLevel)CAMPAIGN_RESISTANCE_beforeUpdate();
    PLAYER_update(joy);
    if(hp<=0){gameOver=TRUE;return;}
    PLAY_PROFILE_START();
    kills+=DINORAH_update();
    PLAY_PROFILE_MARK(0);
    ARENA_camera();
    LEVEL_update();                 // elementos da fase (ex.: lava/lama)
    PLAY_PROFILE_MARK(1);
    if (gameOver) return;

    // alvo da perseguição dos inimigos: o aliado no PROTEGER, senão o jogador
    s16 objectiveX,objectiveY;
    if(CL_target(&objectiveX,&objectiveY))ENEMIES_setChaseTarget(objectiveX,objectiveY);
    else if (OPS_active() && testStage==18 && !operations.phase)
        ENEMIES_setChaseTarget(256,200);
    else if (LEVEL_current()->objective == OBJ_PROTECT && NPC_active())
        ENEMIES_setChaseTarget(npcX + NPC_size() / 2, npcY + NPC_size() / 2);
    else if(DINORAH_alive())
        ENEMIES_setChaseTarget(dinorahX+8,dinorahY+8);
    else
        ENEMIES_setChaseTarget(px + 8, py + 8);

    kills += SHOTS_updatePlayer();
    SHOTS_updateEnemy();
    kills += ENEMIES_update();      // + mortes pela queimadura (fogo)
    MUSIC_setEnemies(ENEMIES_activeCount());   // + inimigos = BPM sobe (perigo)
    PLAY_PROFILE_MARK(2);
    if (gameOver) return; // um golpe fatal não pode recolher a bolsa ou outros itens
    ITEMS_update();

    if (gameOver) return;

    // Training rooms keep their own spawners and never advance the graph.
    if (currentLevel == 0)
    {
        TEST_afterUpdate();
        PLAY_PROFILE_MARK(3);

        // Objective rooms freeze on success/failure until restarted.
        if (TEST_objectiveRoom())
        {
            const u8 st = OBJECTIVE_update(kills);
            OBJECTIVE_drawHUD(kills);
            if (st == OBJ_LOST && ACTORDEATH_pending())settleDeath(5);
            else if (st != OBJ_ONGOING) TEST_finish(st);
        }
        return;
    }

    // NÓ FINAL (chefe): vencer = derrotar o chefe → tela de fim e volta ao
    // título. Sem meta por contagem nem spawn regular (só o chefe e lacaios).
    if (GRAPH_isFinal(currentLevel))
    {
        CL_update();
        OBJECTIVE_drawHUD(kills);
        if (bossDefeated)
        {
            settleDeath(2);
        }
        return;
    }

    // objetivo da fase (matar N / sobreviver / coletar / proteger o aliado)
    const u8 obj = OBJECTIVE_update(kills);
    OBJECTIVE_drawHUD(kills);
    if (obj == OBJ_WON)
    {
        settleDeath(1);
        return;
    }
    if (obj == OBJ_LOST)
    {
        if(ACTORDEATH_pending()) {
            if(!GRAPH_hasFailExit(currentLevel))gameOver=TRUE;
            settleDeath(GRAPH_hasFailExit(currentLevel) ? 4 : 3);return;
        }
        SFX_silence();FLASH_stop();
        if (GRAPH_hasFailExit(currentLevel))
        {
            phaseStats.objFailed = TRUE;CAMPAIGN_record(currentLevel,TRUE);state = ST_DONE;
            ITEMS_clear();NPC_clear();RESULT_complete(kills,TRUE);
            return;
        }
        gameOver = TRUE;
        return;
    }

    if(CAMPAIGN_RESISTANCE_managesSpawn())return;
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

static void resetCampaign(void)
{
    testCampaignMode=FALSE;
    CAMPAIGN_reset();
    DEATH_reset();
    PLAYER_fullHp();BOMB_reset();SHOTS_resetPower();SHOTS_resetChain();
    PLAYER_resetSpeed();INV_clear();ROUTEMAP_reset();STORYSCR_reset();STATS_reset();
}

static void startTestSelection(u8 selection)
{
    if(selection<=TEST_ROOMS){resetCampaign();startTest(selection,FALSE);return;}
    const u8 node=selection-TEST_ROOMS;
    if(node>NODE_COUNT)return;
    resetCampaign();testCampaignMode=TRUE;
    if(node==N_2B)campaignFlags|=CAMPAIGN_CHURCH_RUINED;
    if(node==N_6B)campaignFlags|=CAMPAIGN_RESCUE_PARTIAL;
    if(node==N_13B)campaignFlags|=CAMPAIGN_DINORAH_DEAD;
    SPRITES_hide();SYS_doVBlankProcess();ENEMYGFX_reset();
    MUSIC_selectTrack(GRAPH[node].def->musicTrack);
    // Direct access keeps the mission guide and native countdown, skipping the arrival dialogue.
    LOADING_workBegin();showPrep(node);LOADING_workEnd();
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
        DINORAH_clear();
        ARENA_leave();
        MUSIC_selectTrack(MUSIC_DEFAULT_TRACK);
        FLOOR_clear();          // menu/título sem o chão da arena
        MUSIC_setEnemies(0);    // título/menu: música calma
        const u8 choice = TITLE_run();

        VDP_setTextPlane(BG_A);
        VDP_setTextPalette(PAL0);
        resetCampaign();

        if (choice == TITLE_TEST) {
            TEST_defaults();const u8 room=TEST_chooseRoom(1);
            if(!room)continue;
            startTestSelection(room);
        }
        else {LOADING_workBegin();gotoPrep(1);LOADING_workEnd();} // novo jogo

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
                    if (MISSION_update(pressed)){
                        beginContentTransition();SFX_silence();
                        if(!LOADING_begin(fps*3,pendingLevel))
                        {
                            showPrep(pendingLevel);endContentTransition();break;
                        }
                        startPhase(pendingLevel);
                        LOADING_end();HUD_present();ARENA_gameView();state=ST_PLAY;endContentTransition();
                    }
#ifdef DEV_SHORTCUTS
                    else if (pressed & BUTTON_C)    // C: percorre os nós (debug)
                        showPrep((pendingLevel % NODE_COUNT) + 1);
#endif
                    SPRITES_hide();
                    break;

                case ST_PLAY:
                    if(settleKind)
                    {
                        if(pressed & BUTTON_START)
                        {
                            AUDIO_silenceAll();
                            if(PAUSE_show(kills))state=ST_PAUSE;
                            break;
                        }
                        COMBATGFX_update();
                        ACTORDEATH_update();
                        if(settleTimer)--settleTimer;
                        if(!settleTimer && !ACTORDEATH_pending())finishSettled();
                        if(state==ST_PLAY)SPRITES_draw();else SPRITES_hide();
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
                        if ((currentLevel || (!testResult && testStage!=TEST_DEATH_ROOM && testStage!=TEST_RULE_ROOM)) && (pressed & BUTTON_C)) INV_cycle();
                        if ((currentLevel || (!testResult && testStage!=TEST_DEATH_ROOM && testStage!=TEST_RULE_ROOM)) && (pressed & BUTTON_B))
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
                    if(gameOver && !settleKind)
                    {
                        settleDeath(3);
                    }
                    if(state==ST_PLAY){HUD_drawInventoryIfDirty();SPRITES_draw();}
                    else SPRITES_hide();
                    break;

                case ST_PAUSE:
                {
                    const u8 action=PAUSE_update(pressed);
                    if(action==PAUSE_RESUME){state=ST_PLAY;if(!currentLevel)TEST_resume();}
                    else if(action==PAUSE_EXIT)backToTitle=TRUE;
                    else if(action==PAUSE_TEST_RESTART) {
                        if(testCampaignMode)startTestSelection(TEST_ROOMS+currentLevel);
                        else startTest(testStage,FALSE);
                    }
                    else if(action==PAUSE_TEST_CONFIG) {
                        if(TEST_configure())startTest(testStage,FALSE);else{state=ST_PLAY;TEST_resume();}
                        prevJoy=JOY_readJoypad(JOY_1);
                    }
                    else if(action==PAUSE_TEST_ROOM) {
                        const u8 room=TEST_chooseRoom(testCampaignMode ? TEST_ROOMS+currentLevel : testStage);
                        if(room)startTestSelection(room);else{state=ST_PLAY;if(!currentLevel)TEST_resume();}
                        prevJoy=JOY_readJoypad(JOY_1);
                    }
                    SPRITES_hide();
                    break;
                }

                case ST_OVER:
                {
                    const u8 action=RESULT_update(joy,pressed);
                    if(action==RESULT_TITLE){RESULT_close();backToTitle=TRUE;}
                    else if(action==RESULT_RETRY)
                    {
                        beginTransition();
                        RESULT_close();
                        if(currentLevel==0)startTest(testStage,TRUE);
                        else
                        {
                            DEATH_retry(currentLevel,px,py);
                            gotoPrep(currentLevel);
                        }
                        endTransition();
                    }
                    SPRITES_hide();
                    break;
                }

                case ST_DONE:
                    if(RESULT_update(joy,pressed)==RESULT_RETRY)
                    {
                        pendingLevel=GRAPH_resolve(currentLevel);
                        if(!pendingLevel)pendingLevel=1;
                        ROUTEMAP_prepare(currentLevel,pendingLevel);
                        beginTransition();
                        RESULT_close();
                        if(STORYSCR_start(currentLevel,DEPOIS))
                        {storyThen=STORY_TO_MAP;state=ST_STORY;}
                        else showMap();
                        endTransition();
                    }
                    SPRITES_hide();
                    break;

                case ST_STORY:
                    // cena de diálogo; ao terminar (ou pular), segue o destino
                    if (STORYSCR_update(pressed))
                    {
                        if(storyThen==STORY_TO_PREP)
                        {
                            beginContentTransition();
                            if(STORYSCR_closeToMission())
                            {
                                showPrep(pendingLevel);endContentTransition();break;
                            }
                            endContentTransition();
                        }
                        if(storyThen==STORY_TO_MAP)ROUTEMAP_prepare(currentLevel,pendingLevel);
                        beginTransition();STORYSCR_close();
                        if (storyThen == STORY_TO_PREP)     showPrep(pendingLevel);
                        else if (storyThen == STORY_TO_MAP) showMap();
                        else                                showEnd();
                        endTransition();
                    }
                    SPRITES_hide();
                    break;

                case ST_MAP:
                    // mapa de rotas: A (ou START) segue (história de ANTES,
                    // se o nó destino tiver, e então a preparação)
                    if (ROUTEMAP_update(pressed))
                    {
                        beginTransition();
                        ROUTEMAP_release();
                        gotoPrep(pendingLevel);
                        endTransition();
                    }
                    break;

                case ST_END:
                {
                    const u8 action=RESULT_update(joy,pressed);
                    if(action==RESULT_TITLE){RESULT_close();backToTitle=TRUE;}
                    else if(action==RESULT_REPLAY)
                    {beginTransition();RESULT_close();resetCampaign();gotoPrep(1);endTransition();}
                    SPRITES_hide();
                    break;
                }
            }

            AUDIO_frameBegin();     // árbitro: música e SFX só REQUISITAM voz...
            MUSIC_update();
            SFX_update();
            AUDIO_frameEnd();       // ...e o árbitro escreve o PSG (1x por canal)
            // All opaque cards and panels own stable palettes while frozen.
            if(frameState==ST_PLAY && state==ST_PLAY)FLASH_update();
            SYS_doVBlankProcess();
        }
    }
}
