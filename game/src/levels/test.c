// Training runtime. Never changes campaign definitions or save state.
#include "levels/test.h"
#include "levels/levels.h"
#include "system/video/actor_animation.h"
#include "system/video/actordeath.h"
#include "system/video/herogfx.h"
#include "system/video/combatgfx.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "core/stats.h"
#include "core/objective.h"
#include "actors/player.h"
#include "actors/npc.h"
#include "actors/dinorah.h"
#include "actors/shots.h"
#include "actors/bomb.h"
#include "core/death.h"
#include "core/inventory.h"
#include "levels/graph.h"
#include "enemies/enemies.h"
#include "items/items.h"

TestSettings testSettings[TEST_ROOMS];
u32 testTicks;
u8 testResult;
static const u8 roster[13]={0,1,2,3,4,5,6,7,8,9,10,11,ENEMY_BOSS};
static const u8 counts[4]={1,4,8,16},shotCounts[3]={0,6,16};
static const u8 lifeValues[3]={25,50,100},dummyValues[3]={1,20,100};
static u16 respawn[MAX_ENEMIES],testSpawnTimer,repeatTimer,hudTimer;
static bool wasAlive[MAX_ENEMIES],deathRequested;
static u8 galleryDirection,galleryPose;
static u32 meterVblank,meterTicks,meterWarmTicks;
static u16 measuredFps,peakCpu;
static u16 ruleDeaths;
static const RoutePoint deathPoint[]={{232,168,0}};
static const RouteDef deathRoute={.points=deathPoint,.count=1};

static TestSettings *settings(void){return &testSettings[testStage-1];}
void TEST_defaults(void)
{
    memset(testSettings,0,sizeof testSettings);
    for(u16 i=0;i<TEST_ROOMS;i++) {
        testSettings[i].direction=8;testSettings[i].dummyHp=1;
        testSettings[i].restock=1;testSettings[i].initialHp=2;
        testSettings[i].kind=1;testSettings[i].attacks=1;
    }
    testSettings[5].kind=0;testSettings[5].count=1;
    testSettings[5].shots=1;testSettings[5].noDefeat=1;
    testSettings[TEST_DEATH_ROOM-1].selected=2;
    testSettings[TEST_DEATH_ROOM-1].direction=0;
    testSettings[TEST_DEATH_ROOM-1].repeat=1;
    TestSettings *rules=&testSettings[TEST_RULE_ROOM-1];
    rules->kind=0;rules->dummyHp=4;rules->status=5;rules->count=3;rules->shots=2;
}
bool TEST_objectiveRoom(void){return testStage==3 || testStage==7 || testStage==8;}
bool TEST_staticEnemies(void){return currentLevel==0 && (testStage==1 || testStage==2);}
bool TEST_noDefeat(void){return currentLevel==0 && settings()->noDefeat;}
bool TEST_effectTick(void){return (testStage!=1 && testStage!=TEST_DEATH_ROOM) || !(testTicks&((1u<<settings()->slow)-1));}
bool TEST_animation(u8 index,u8 *dir,u8 *pose)
{
    if(currentLevel || testStage!=1)return FALSE;
    *dir=galleryDirection;
    *pose=enemies[index].frozen ? 0 : galleryPose;
    return TRUE;
}
u16 TEST_shotLimit(void)
{
    return testStage==6 ? shotCounts[settings()->shots] :
        (LEVEL_current()->shotCap ? LEVEL_current()->shotCap : MAX_PSHOTS);
}
void TEST_requestDeath(void){deathRequested=TRUE;}
void TEST_deathInput(u16 pressed)
{
    if(pressed&BUTTON_C)settings()->selected=(settings()->selected+1)%3;
    if(pressed&(BUTTON_A|BUTTON_C)){TEST_requestDeath();hudTimer=0;}
}
u8 TEST_ruleNode(void)
{
    static const u8 nodes[]={N_1,N_6A,N_12};
    return nodes[testSettings[TEST_RULE_ROOM-1].kind];
}
static void rulesSeed(void)
{
    const TestSettings *s=settings();
    DEATH_reset();ITEMS_clear();SHOTS_clear();
    PLAYER_fullHp();PLAYER_resetSpeed();PLAYER_restoreShield(0);
    SHOTS_resetPower();SHOTS_resetChain();INV_clear();BOMB_clear();
    for(u8 i=0;i<s->dummyHp;i++)SHOTS_addPower();
    for(u8 i=0;i<s->status;i++)PLAYER_addSpeed();
    static const u8 stock[]={ITEM_SHIELD,ITEM_CHAIN,ITEM_ICE};
    for(u8 i=0;i<s->count;i++)INV_add(stock[i]);
    for(u8 i=0;i<s->shots;i++)BOMB_add();
    ruleDeaths=0;hudTimer=0;
}
void TEST_ruleInput(u16 pressed)
{
    if(pressed&BUTTON_C){settings()->kind=(settings()->kind+1)%3;rulesSeed();}
    else if(pressed&BUTTON_B)rulesSeed();
    else if(pressed&BUTTON_A)
    {
        PLAYER_restoreShield(0);
        loseHp(PLAYER_START_HP); // mesma derrota e animação da campanha
    }
}
static void slotPosition(u16 i,u8 type,s16 *x,s16 *y)
{
    if(testStage==1) {
        *x=i==12 ? 248 : 24+(i%4)*48;
        *y=i==12 ? 112 : 88+(i/4)*48;
    } else if(testStage==2) {
        *x=148+i*32;*y=112;
    } else {
        *x=24+(i%4)*68;*y=88+(i/4)*36;
    }
    const s16 size=ENEMY_DEFS[type]->size;
    if(*x>arenaMaxX-size+1)*x=arenaMaxX-size+1;
    if(*y>arenaMaxY-size+1)*y=arenaMaxY-size+1;
}
static void spawnSlot(u16 i,u8 type)
{
    s16 x,y;slotPosition(i,type,&x,&y);
    Enemy *e=&enemies[i];memset(e,0,sizeof *e);
    e->x=x;e->y=y;e->fx=(s32)x<<6;e->fy=(s32)y<<6;
    e->type=type;e->hp=ENEMY_DEFS[type]->hp;e->active=TRUE;
    e->fireTimer=ENEMY_CD/2+(random()%fps);
    if(testStage==2 && i==0)e->hp=dummyValues[settings()->dummyHp];
    if(type==ENEMY_BOSS)bossDefeated=FALSE;
    wasAlive[i]=TRUE;respawn[i]=0;
}
static void ensureSlot(u16 i,u8 type)
{
    if(enemies[i].active){wasAlive[i]=TRUE;return;}
    if(wasAlive[i]){wasAlive[i]=FALSE;respawn[i]=fps*2;}
    if(respawn[i]){respawn[i]--;return;}
    spawnSlot(i,type);
}
static u16 desiredCount(void)
{
    if(testStage==1)return 13;
    if(testStage==2)return settings()->chain ? 3 : 1;
    if(testStage==5 && settings()->kind==13)return 1;
    return counts[settings()->count];
}
static u8 selectedKind(u16 i)
{
    return settings()->kind ? roster[settings()->kind-1] : roster[i%13];
}
void TEST_begin(bool retryRules)
{
    testTicks=0;testResult=0;testSpawnTimer=fps;repeatTimer=fps*2;
    hudTimer=0;deathRequested=FALSE;peakCpu=0;measuredFps=fps;
    memset(respawn,0,sizeof respawn);memset(wasAlive,0,sizeof wasAlive);
    meterVblank=vtimer;meterTicks=meterWarmTicks=0;bossDefeated=FALSE;
    if(!TEST_objectiveRoom()) {
        VDP_setWindowOnTop(HUD_ROWS+4);
        VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX),0,HUD_ROWS,40,4);
        VDP_drawText(TEST_name(testStage),1,HUD_ROWS);
        VDP_drawText("START: PAUSA",27,HUD_ROWS);
        char number[8];sprintf(number,"%u/%u",testStage,TEST_ROOMS);
        HUD_drawObjective("TREINO",0,number,0,"");
    }
    if(testStage==2 || testStage==4)hp=lifeValues[settings()->initialHp];
    if(testStage==1 || testStage==2 || testStage==5 || testStage==6)
        for(u16 i=0;i<desiredCount();i++)spawnSlot(i,testStage==1 ? roster[i] : testStage==2 ? (i ? ENEMY_TARGET : ENEMY_DUMMY) : selectedKind(i));
    if(testStage==TEST_DEATH_ROOM) {
        px=72;py=160;faceX=1;faceY=1;
        DINORAH_start(&deathRoute);ARENA_camera();deathRequested=TRUE;
    }
    if(testStage==TEST_RULE_ROOM) {
        if(retryRules){DEATH_startPhase(TEST_ruleNode());ruleDeaths++;}
        else rulesSeed();
    }
    TEST_drawHUD();
}
void TEST_resume(void)
{
    meterVblank=vtimer;meterTicks=meterWarmTicks=testTicks;hudTimer=0;
    PLAYER_waitFireRelease();
}
static void seedShots(void)
{
    const u16 cap=TEST_shotLimit();
    for(u16 pool=0;pool<2;pool++) {
        FShot *shots=pool ? eshots : pshots;
        for(u16 i=0;i<MAX_PSHOTS;i++) {
            if(i>=cap){shots[i].active=FALSE;continue;}
            if(shots[i].active)continue;
            shots[i]=(FShot){(s32)(24+(i%8)*34)<<6,(s32)(pool ? 88+(i/8)*48 : 172+(i/8)*24)<<6,
                pool ? -128 : 128,0,pool ? 1 : 0,1,TRUE};
        }
    }
}
void TEST_beforeUpdate(void)
{
    testTicks++;
    if(testStage==TEST_DEATH_ROOM) {
        if(TEST_effectTick())ACTORDEATH_update();
        if(deathRequested || !ACTORDEATH_pending()) {
            if(settings()->repeat && repeatTimer)--repeatTimer;
            if(deathRequested || (settings()->repeat && !repeatTimer)) {
                // Restore live frames: death poses reuse each actor's tiles.
                HERO_load();DINORAH_start(&deathRoute);
                for(u8 actor=0;actor<2;actor++)
                    if(settings()->selected==2 || settings()->selected==actor)
                        ACTORDEATH_start(actor,settings()->direction!=0);
                deathRequested=FALSE;repeatTimer=fps;
            }
        }
        return;
    }
    if(testStage==1) {
        const u16 clock=testTicks>>settings()->slow;
        galleryDirection=settings()->direction==8 ? divu(clock,fps)&7 : settings()->direction;
        galleryPose=settings()->animation ? ACTOR_IDLE_FRAMES+(divu(clock,ACTOR_RUN_TICKS(fps))&3) : divu(clock,ACTOR_IDLE_TICKS(fps))&1;
        if(settings()->repeat && repeatTimer)--repeatTimer;
        if(settings()->repeat && !repeatTimer){deathRequested=TRUE;repeatTimer=fps*3;}
        if(deathRequested && !COMBATGFX_remaining()) {
            ENEMIES_testKill(settings()->selected);deathRequested=FALSE;
        }
    }
    if(testStage==1 || testStage==2 || testStage==5 || testStage==6) {
        const u16 count=desiredCount();
        for(u16 i=0;i<count;i++)ensureSlot(i,testStage==1 ? roster[i] : testStage==2 ? (i ? ENEMY_TARGET : ENEMY_DUMMY) : selectedKind(i));
        // Live behaviour keeps its summons. Gallery and load obey fixed slots.
        if(testStage!=5)for(u16 i=count;i<MAX_ENEMIES;i++)enemies[i].active=FALSE;
    }
    if(testStage==6) {
        if(settings()->deaths && !(testTicks%fps) && !COMBATGFX_remaining()) {
            for(u16 i=0;i<desiredCount();i++)if(enemies[i].active){ENEMIES_testKill(i);break;}
        }
        for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active) {
            if(settings()->status==2)enemies[i].frozen=fps;
            if(settings()->status==3){enemies[i].burn=fps;enemies[i].burnTick=fps;enemies[i].burnFlash=2;}
        }
        seedShots();
    }
}
void TEST_afterUpdate(void)
{
    if(testStage==2 && settings()->restock)ITEMS_testEnsure();
    if(TEST_objectiveRoom() && settings()->attacks) {
        if(testSpawnTimer)testSpawnTimer--;
        else {
            const LevelDef *def=LEVEL_current();
            const u16 batch=def->spawnCount ? def->spawnCount : 1;
            for(u16 i=0;i<batch;i++)ENEMIES_trySpawn(def->enemyTypes,def->enemyTypeCount);
            testSpawnTimer=settings()->attacks==2 ? fps : def->spawnSeconds*fps;
        }
    }
    if(testStage==6) {
        const u16 count=desiredCount();
        for(u16 i=count;i<MAX_ENEMIES;i++)enemies[i].active=FALSE;
        if(settings()->status==1)for(u16 i=0;i<count;i++)if(enemies[i].active)enemies[i].shielded=TRUE;
    }
    const u16 cpu=SYS_getCPULoad();if(testTicks-meterWarmTicks>=fps && cpu>peakCpu)peakCpu=cpu;
    const u32 elapsed=vtimer-meterVblank;
    if(elapsed>=fps) {
        measuredFps=divu((testTicks-meterTicks)*fps,elapsed);
        meterVblank=vtimer;meterTicks=testTicks;
    }
    if(hudTimer)hudTimer--;
    else {TEST_drawHUD();hudTimer=fps/5;}
}
void TEST_drawHUD(void)
{
    char text[48];
    if(TEST_objectiveRoom()) {
        if(testResult && testStage!=3) {
            char value[8];sprintf(value,"%03u%%",testResult==OBJ_WON ? 100 : OBJECTIVE_progress());
            HUD_drawObjective(testResult==OBJ_WON ? "CHEGOU" : "FALHOU",
                testStage==8 ? TILE_ICON_SHIELD : 0,value,0,"");
        }
        if(testResult && testStage==3) {
            char value[8];sprintf(value,"%03u",npcHp<0 ? 0 : npcHp);
            HUD_drawObjective(testResult==OBJ_WON ? "SINAL OK" : "SEM SINAL",TILE_ICON_SAINT,value,0,"");
        }
        return;
    }
    VDP_clearText(1,HUD_ROWS+1,38);VDP_clearText(1,HUD_ROWS+2,38);
    switch(testStage) {
        case TEST_RULE_ROOM: {
            static const char *const ranges[]={"1 A 5","6 A 11","12 A 16"};
            bool bag=FALSE;
            for(u8 i=0;i<MAX_ITEMS;i++)if(items[i].active && items[i].type==ITEM_BAG)bag=TRUE;
            sprintf(text,"ETAPAS:%s MORTES:%u%s",ranges[settings()->kind],ruleDeaths,bag ? " BOLSA" : "");
            VDP_drawText(text,1,HUD_ROWS+1);
            u8 count=0,type,charges;
            for(u8 i=1;i<INV_POS;i++){INV_view(i,&type,&charges);if(type!=INV_EMPTY)count++;}
            sprintf(text,"TIRO:%u VEL:+%u%% ITENS:%u BOMBAS:%u",SHOTS_power(),PLAYER_speedBonus(),count,BOMB_count());
            VDP_drawText(text,1,HUD_ROWS+2);
            VDP_clearText(1,HUD_ROWS+3,38);
            VDP_drawText("A:MORRER B:REPOR C:ETAPAS",1,HUD_ROWS+3);
            return;
        }
        case TEST_DEATH_ROOM:
            sprintf(text,"PERSONAGEM: %s",settings()->selected==2 ? "OS DOIS" : settings()->selected ? "DINORAH" : "DAMIÃO");VDP_drawText(text,1,HUD_ROWS+1);
            sprintf(text,"A: REPETIR  C: ALVO  TEMPO:1/%u",1u<<settings()->slow);break;
        case 1:
            sprintf(text,"ALVO: %s",ENEMY_DEFS[roster[settings()->selected]]->name);VDP_drawText(text,1,HUD_ROWS+1);
            sprintf(text,"%s  DIR:%u  TEMPO:1/%u",settings()->animation ? "CAMINHADA" : "REPOUSO",galleryDirection,1u<<settings()->slow);break;
        case 2:
            sprintf(text,"DUMMY:%03u BALAS:%u VELOC:+%u%%",enemies[0].active ? enemies[0].hp : 0,SHOTS_power(),PLAYER_speedBonus());VDP_drawText(text,1,HUD_ROWS+1);
            strcpy(text,"ITENS: COLETE / C: ESCOLHA / B: USE");break;
        case 4:
            VDP_drawText("MURO: BLOQUEIA / AZUL: TIRO PASSA",1,HUD_ROWS+1);
            sprintf(text,"X:%03d Y:%03d VIDA:%03d LENTO:%u%%",px,py,hp,playerSlowPct);break;
        case 5:
            sprintf(text,"TIPO: %s",settings()->kind ? ENEMY_DEFS[roster[settings()->kind-1]]->name : "MISTO");VDP_drawText(text,1,HUD_ROWS+1);
            sprintf(text,"ATIVOS:%02u DANO:%u %s",ENEMIES_activeCount(),phaseStats.damageTaken,settings()->noDefeat ? "SEM DERROTA" : "VIDA NORMAL");break;
        default: {
            sprintf(text,"FPS:%02u CPU:%03u%% PICO:%03u%%",measuredFps,SYS_getCPULoad(),peakCpu);VDP_drawText(text,1,HUD_ROWS+1);
            u16 player=0,enemy=0,deaths=0;
            for(u16 i=0;i<MAX_PSHOTS;i++){player+=pshots[i].active!=0;enemy+=eshots[i].active!=0;}
            for(u16 i=0;i<COMBAT_DEATH_CAP;i++)deaths+=combatDeaths[i].active!=0;
            sprintf(text,"INIMIGOS:%02u TIROS:%02u/%02u MORTES:%u",ENEMIES_activeCount(),player,enemy,deaths);break;
        }
    }
    VDP_drawText(text,1,HUD_ROWS+2);
    if(testStage==2) {
        const Item *near=NULL;
        for(u16 i=0;i<MAX_ITEMS;i++)if(items[i].active && abs(items[i].x-px)+abs(items[i].y-py)<36){near=&items[i];break;}
        VDP_clearText(1,HUD_ROWS+3,38);
        if(near){sprintf(text,"ITEM: %s",ITEM_DEFS[near->type]->name);VDP_drawText(text,1,HUD_ROWS+3);}
    }
}
void TEST_finish(u8 outcome)
{
    testResult=outcome;
    NPC_stopBlink();
    TEST_drawHUD();
}
