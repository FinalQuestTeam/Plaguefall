// Eight playable mission prototypes. State, props and reinforcements are
// isolated from the campaign; all combat uses the normal production pools.
#include "levels/operations.h"
#include "levels/test.h"
#include "core/game.h"
#include "core/objective.h"
#include "core/stats.h"
#include "actors/player.h"
#include "actors/dinorah.h"
#include "actors/shots.h"
#include "enemies/enemies.h"
#include "system/video/markers.h"
#include "system/video/objectivegfx.h"
#include "system/video/projection.h"
#include "system/video/spritelist.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/sfx.h"

OperationsState operations;
static const u8 roster[]={ENEMY_SQ_RED,ENEMY_TRI_RED,ENEMY_TRI_YEL,ENEMY_TRI_ORG,ENEMY_SQ_PUR};
static LevelDef definition;
static u8 cachedRoom=255,cachedPressure=255;
static const s16 points[3][2]={{96,144},{400,144},{256,304}};
static const ArenaRect shortcut={224,208,16,64,TRUE};
static const ArenaRect trap={248,160,64,64,FALSE};
static const ArenaRect heat[3]={{184,112,32,192,FALSE},{320,112,32,192,FALSE},{224,224,96,32,FALSE}};
static u16 timer,hudClock;
static u8 hot,warning,lastVisual;
static s16 visualX,visualY;
static char lastHud[3][39];
static bool meterCold;
static u8 meterField;
static u16 meterLast[6];
static u32 objectiveSignature;
static const char *lastHint;
static void meter(void);
static u8 visualDone,visualDelivered,visualPhase,visualGateHp[3],visualPostHp,visualCargoOpen,visualHeld;
static void visualsStart(void);
static void visualsSync(void);
#ifdef OPS_PROFILE
volatile u16 operationsProfile[4];
#define OP_CLOCK() u32 opClock=getSubTick()
#define OP_MARK(i) do{u32 now=getSubTick();operationsProfile[i]=now-opClock;opClock=now;}while(0)
#else
#define OP_CLOCK()
#define OP_MARK(i)
#endif

bool OPS_active(void){return !currentLevel && testStage>=OPS_FIRST_ROOM && testStage<OPS_FIRST_ROOM+OPS_COUNT;}
static u8 mission(void){return testStage-OPS_FIRST_ROOM;}
static u8 countDone(void){return (operations.done&1)+((operations.done>>1)&1)+((operations.done>>2)&1);}
static bool overlaps(const ArenaRect *r,s16 x,s16 y,u16 w,u16 h)
{return x<r->x+r->w && x+(s16)w>r->x && y<r->y+r->h && y+(s16)h>r->y;}
static bool near(s16 x,s16 y){return abs(px+8-x)<=22 && abs(py+8-y)<=22;}
static bool atExit(void){return near(448,304);}
static TestSettings *settings(void){return &testSettings[testStage-1];}

const LevelDef *OPS_def(u8 room)
{
    // Called before LEVEL_load changes currentLevel: use the explicit room.
    const u8 index=room-OPS_FIRST_ROOM;
    if(cachedRoom==room && cachedPressure==testSettings[room-1].attacks)return &definition;
    cachedRoom=room;cachedPressure=testSettings[room-1].attacks;
    definition=(LevelDef){.arena=&OPS_arenas[index],.spawnSeconds=3,.enemyCap=4,.shotCap=6,
        .enemyTypes=roster,.enemyTypeCount=sizeof roster,.musicTrack=MUSIC_TRACK_BREU};
    if(index==2)definition.musicTrack=MUSIC_TRACK_ENTARDECER;
    if(index==5){definition.objective=OBJ_ESCORT;definition.route=&OPS_evacRoute;}
    if(testSettings[room-1].attacks==2){definition.enemyCap=4;definition.shotCap=6;}
    if(index==5)definition.enemyCap=3; // reserve combat budget for Dinorah and her two shots
    return &definition;
}

bool OPS_blocked(s16 x,s16 y,u16 w,u16 h)
{
    if(!OPS_active())return FALSE;
    if(mission()==0 && !(operations.done&1) && overlaps(&shortcut,x,y,w,h))return TRUE;
    if(mission()==5)for(u8 i=0;i<3;i++)
        if(operations.gateHp[i] && overlaps(&OPS_evacGates[i],x,y,w,h))return TRUE;
    return FALSE;
}
bool OPS_shotBlocked(s16 x,s16 y,bool player)
{
    if(!OPS_active())return FALSE;
    if(mission()==0 && !(operations.done&1) && overlaps(&shortcut,x,y,8,8))return TRUE;
    if(mission()==5)for(u8 i=0;i<3;i++)if(operations.gateHp[i] && overlaps(&OPS_evacGates[i],x,y,8,8)) {
        if(player){operations.gateHp[i]--;SFX_playerHit();if(!operations.gateHp[i])sfxItemPickup();lastVisual=255;}
        return TRUE;
    }
    return FALSE;
}

static void spawnAt(u8 type,s16 x,s16 y)
{ENEMIES_spawnAt(type,x,y);}
void OPS_begin(void)
{
    memset(&operations,0,sizeof operations);operations.cargo=255;operations.postHp=60;
    for(u8 i=0;i<3;i++)operations.gateHp[i]=4;
    if(mission()==7)operations.clock=fps*25;
    timer=fps;hudClock=0;hot=warning=0;lastVisual=255;visualX=visualY=-1;
    memset(lastHud,0,sizeof lastHud);MARKERS_load();playerSlowPct=0;
    if(mission()==3)for(u8 i=0;i<3;i++) {
        spawnAt(ENEMY_SQ_RED,points[i][0]-12,points[i][1]-12);
        enemies[i].hp=4;
    }
    if(mission()==6)for(u8 i=0;i<4;i++)spawnAt(ENEMY_TRI_YEL,208+(i%2)*16,176+(i/2)*24);
    for(u8 i=0;i<settings()->dummyHp;i++)SHOTS_addPower();
    for(u8 i=0;i<settings()->status;i++)PLAYER_addSpeed();
    visualsStart();
    OPS_restoreView();
}
void OPS_restoreView(void)
{
    if(!OPS_active())return;
    VDP_setWindowOnTop(HUD_ROWS+4);
    VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX),0,HUD_ROWS,40,4);
    memset(lastHud,0,sizeof lastHud);lastVisual=255;hudClock=0;
    meterCold=TRUE;meterField=0;memset(meterLast,255,sizeof meterLast);
    objectiveSignature=0xFFFFFFFFUL;lastHint=NULL;
    OPS_drawHUD();
}

void OPS_beforeUpdate(void)
{
    playerSlowPct=mission()==2 && operations.cargo!=255 ? 20 : 0;
}
static bool atWorkPoint(u8 i)
{
    const s16 dy=py+8-points[i][1];
    return abs(px+8-points[i][0])<=26 && dy>=16 && dy<=40;
}
// Operate from the visible front/south face, preserving progress on retreat.
static bool work(u8 i,u16 frames)
{
    if((operations.done&(1u<<i)) || !atWorkPoint(i) ||
       (JOY_readJoypad(JOY_1)&BUTTON_A))return FALSE;
    if(operations.work[i]<frames)operations.work[i]++;
    if(operations.work[i]<frames)return FALSE;
    operations.done|=1u<<i;sfxItemPickup();lastVisual=255;return TRUE;
}

static void reinforcement(void)
{
    if(timer){timer--;return;}
    const u8 kind=mission();
    const bool required=kind==6 && operations.captured<6;
    if(!settings()->attacks && !required){timer=fps;return;}
    u16 period=settings()->attacks==2 ? fps : fps*3;
    if(kind==0 && (operations.done&2))period+=fps*2; // a destroyed feed stops a vent
    if(kind==3)period+=countDone()*fps;
    timer=period;
    const u8 batch=settings()->attacks==2 ? 2 : 1;
    for(u8 i=0;i<batch;i++) {
        if(kind==6) {
            if(ENEMIES_activeCount()<definition.enemyCap)spawnAt(ENEMY_TRI_YEL,208,176+(random()&1)*24);
        } else ENEMIES_trySpawn(roster,sizeof roster);
    }
}

static void updateHunt(void)
{
    for(u8 i=0;i<3;i++)if(!(operations.done&(1u<<i))) {
        Enemy *e=&enemies[i];
        if(!e->active){operations.done|=1u<<i;lastVisual=255;sfxItemPickup();continue;}
        // Existing Torreão art/attack; marked transmitters retreat at close range.
        if(!e->frozen && abs(e->x-px)+abs(e->y-py)<144) {
            const s16 dx=e->x>=px ? 24 : -24,dy=e->y>=py ? 24 : -24;
            ARENA_move(&e->fx,&e->fy,dx,dy,ENEMY_SIZE(e));
            e->x=e->fx>>6;e->y=e->fy>>6;
        }
    }
    if(operations.done==7)operations.outcome=OBJ_WON;
}

static void updateTrap(void)
{
    operations.held=0;
    for(u8 i=0;i<MAX_ENEMIES;i++) {
        Enemy *e=&enemies[i];const u16 bit=1u<<i;
        if(!e->active){operations.trappedMask&=~bit;continue;}
        const s16 x=e->x+ENEMY_SIZE(e)/2,y=e->y+ENEMY_SIZE(e)/2;
        if(!operations.work[1] && x>=trap.x+8 && x<trap.x+trap.w-8 && y>=trap.y+16 && y<trap.y+trap.h-8)
            operations.trappedMask|=bit;
        if(operations.trappedMask&bit) {
            // The field visibly pulls each entrant onto an interior holding
            // pad, freeing the doorway for the next insect instead of piling
            // frozen bodies across the entrance.
            const s16 dx=trap.x+16+(i&1)*20-e->x,dy=trap.y+16+((i>>1)&1)*20-e->y;
            e->x+=dx>2 ? 2 : dx< -2 ? -2 : dx;e->y+=dy>2 ? 2 : dy< -2 ? -2 : dy;
            e->fx=(s32)e->x*64;e->fy=(s32)e->y*64;e->vx=e->vy=0;
            e->frozen=fps*2;operations.held++;
        }
    }
    if(operations.work[1])operations.work[1]--;
    if(!operations.phase && !operations.work[1]) {
        if(operations.held>=2 && near(216,240) && !(JOY_readJoypad(JOY_1)&BUTTON_A)) {
            if(++operations.work[0]>=fps){
                operations.phase=1;operations.clock=fps*3/2;SFX_countPulse(FALSE);
            }
        } else operations.work[0]=0;
    } else if(operations.phase==1 && !operations.clock) {
        for(u8 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active && (operations.trappedMask&(1u<<i))) {
            if(ENEMIES_testKill(i)){operations.captured++;}
        }
        if(overlaps(&trap,px,py,16,16))damagePlayer(40);
        SFX_bombBlast();operations.phase=0;operations.work[0]=0;operations.work[1]=fps*2;
        operations.trappedMask=0;operations.held=0;
        if(operations.captured>6)operations.captured=6;
        if(operations.captured>=6)operations.outcome=OBJ_WON;
    }
}

static void updatePost(void)
{
    if(operations.phase)return;
    if(!operations.clock){operations.phase=1;sfxItemPickup();return;}
    const ArenaRect post={240,184,32,32,FALSE};
    for(u8 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active && overlaps(&post,enemies[i].x,enemies[i].y,ENEMY_SIZE(&enemies[i]),ENEMY_SIZE(&enemies[i]))) {
        if(!operations.damageTimer){
            operations.postHp=operations.postHp>6 ? operations.postHp-6 : 0;
            operations.damageTimer=fps;SFX_playerHit();
        }
        ENEMIES_knockbackFrom(&enemies[i],256,200);
    }
    if(!operations.postHp)operations.outcome=OBJ_LOST;
}

static void hazards(void)
{
    hot=warning=0;
    if(mission()==1 && operations.done && operations.done!=7) {
        hot=(operations.phase&1) ? 1 : 2;
    } else if(mission()==4 && operations.done!=7) {
        const u16 cycle=fps*6,t=operations.clock;
        const u8 lane=divu(t,cycle)%3;
        const u16 step=t%cycle;
        if(step<fps*3/2)warning=lane+1;
        else if(step<fps*4-countDone()*(fps/3))hot=lane+1;
    }
    if(hot && overlaps(&heat[hot-1],px,py,16,16) && !operations.damageTimer) {
        damagePlayer(5);operations.damageTimer=fps/2;SFX_ambient(SFX_AMB_LAVA);
    }
}

const char *OPS_hint(void)
{
    if(operations.outcome)return "START: REINICIAR OU TROCAR SALA";
    switch(mission()) {
        case 0:return operations.done==7 ? "CARGAS ARMADAS! VÁ PARA A SAÍDA." : "AO SUL DO NINHO: PARE 2 S SEM TIRO.";
        case 1:return (operations.done&3)==3 ? "ATIVE O PAINEL 3 PELO LADO SUL." : "AO SUL: LIGUE 1 E 2 SEM ATIRAR.";
        case 2:return operations.cargo!=255 ? "LEVE A SACOLA AO DEPÓSITO A OESTE." : operations.delivered>=2 ? "SAÍDA LIVRE. 3A SACOLA: CURA+ESCUDO." : "ABRA O BAÚ E PEGUE A SACOLA AO LADO.";
        case 3:return "DESTRUA OS 3 TRANSMISSORES MARCADOS.";
        case 4:return operations.done==7 ? "PRESSÃO ZERADA. ALCANCE A SAÍDA." : "AO SUL: ABRA 3 VÁLVULAS. EVITE CALOR.";
        case 5:return !DINORAH_alive() ? "DINORAH CAIU. REINICIE A ESCOLTA." : dinorahState==DIN_ARRIVED ? "REÚNA-SE COM DINORAH NA SAÍDA." : "CUBRA DINORAH. ABRA AS 3 PORTAS.";
        case 6:return operations.phase ? "PROCESSANDO! AFASTE-SE DA GAIOLA." : operations.work[1] ? "RESFRIANDO. PREPARE OUTRA CAPTURA." : operations.held>=2 ? "2+ PRESOS. PARE NO PAINEL C AO SUL." : operations.held ? "1 PRESO. ATRAIA MAIS UM INSETO." : "ENTRE ATÉ O FUNDO. ATRAIA SEM TIRO.";
        default:return operations.phase ? "RETIRADA AUTORIZADA! VOLTE A OESTE." : "DEFENDA O RÁDIO ATÉ A AUTORIZAÇÃO.";
    }
}

static void fill(const ArenaRect *r,u16 tile)
{
    // Clip to the resident viewport. ARENA streaming restores cleared decals.
    s16 l=r->x/8,t=r->y/8,rr=(r->x+r->w)/8,bb=(r->y+r->h)/8;
    const s16 cx=cameraX/8,cy=cameraY/8;
    if(l<cx)l=cx;if(rr>cx+40)rr=cx+40;if(t<cy)t=cy;if(bb>cy+28)bb=cy+28;
    if(rr<=l || bb<=t)return;
    u16 data[40];for(s16 i=0;i<rr-l;i++)data[i]=tile;
    for(s16 y=t;y<bb;y++)VDP_setTileMapDataRow(BG_A,data,y&31,l&63,rr-l,DMA_QUEUE_COPY);
}
u16 OPS_backgroundAttr(s16 col,s16 row)
{
    const s16 x=col*8,y=row*8;const u8 kind=mission();
    if(kind==0 && !(operations.done&1) && overlaps(&shortcut,x,y,8,8))
        return TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_WALL);
    if(kind==1 || kind==4)for(u8 i=0;i<3;i++)if(overlaps(&heat[i],x,y,8,8)) {
        if(hot==i+1)return TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_LAVA);
        if(warning==i+1)return TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_SPARK);
    }
    return 0;
}
static void scenery(void)
{
    const u8 signature=hot|(warning<<2)|(operations.done<<4);
    if(lastVisual==signature && visualX==cameraX/8 && visualY==cameraY/8)return;
    if(mission()==1 || mission()==4)for(u8 i=0;i<3;i++) {
        const bool active=hot==i+1 || warning==i+1;
        if(active || lastVisual==255 || ((lastVisual&3)==i+1 || ((lastVisual>>2)&3)==i+1))
            fill(&heat[i],hot==i+1 ? TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_LAVA) :
                 warning==i+1 ? TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_SPARK) : 0);
    }
    if(mission()==0)fill(&shortcut,(operations.done&1) ? 0 : TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_WALL));
    lastVisual=signature;visualX=cameraX/8;visualY=cameraY/8;
}

static void visualsStart(void)
{
    const u8 kind=mission();OBJECTIVEGFX_start(kind);
    visualDone=visualDelivered=visualPhase=visualCargoOpen=visualHeld=0;visualPostHp=60;
    for(u8 i=0;i<3;i++)visualGateHp[i]=4;
    if(kind==0 || kind==1 || kind==2 || kind==4) {
        const u8 art=kind==0 ? OART_NEST : kind==1 ? OART_GENERATOR : kind==2 ? OART_CARGO : OART_VALVE;
        for(u8 i=0;i<3;i++)OBJECTIVEGFX_place(i,art,points[i][0],points[i][1],TRUE);
        if(kind==2){OBJECTIVEGFX_place(3,OART_CARGO,64,304,TRUE);objectiveVisuals[3].mode=2;objectiveVisuals[3].frame=5;}
    } else if(kind==3) {
        for(u8 i=0;i<3;i++)OBJECTIVEGFX_place(i,OART_TRANSMITTER,enemies[i].x+8,VIDEO_PROJECT_Y(enemies[i].y)+8,FALSE);
    } else if(kind==5) {
        for(u8 i=0;i<3;i++) {
            const ArenaRect *gate=&OPS_evacGates[i];
            // The 64px canvas includes two permanent 8px jambs around the leaf.
            OBJECTIVEGFX_place(i,OART_GATE,gate->x+gate->w/2,gate->y+gate->h,TRUE);
        }
    } else if(kind==6) {
        OBJECTIVEGFX_place(0,OART_TRAP,216,240,TRUE);
        OBJECTIVEGFX_place(1,OART_CAGE,280,216,TRUE);
    } else OBJECTIVEGFX_place(0,OART_RADIO,256,200,TRUE);
    OBJECTIVEGFX_ground(TRUE);
}

static void visualsSync(void)
{
    const u8 kind=mission(),changed=operations.done&~visualDone;
    if(kind==0 || kind==1 || kind==4)for(u8 i=0;i<3;i++) {
        if(changed&(1u<<i)){OBJECTIVEGFX_activate(i);if(kind==0)SFX_bombBlast();}
        else OBJECTIVEGFX_prime(i,operations.work[i]!=0);
    }
    if(kind==2)for(u8 i=0;i<3;i++) {
        if((operations.cargoOpen&~visualCargoOpen)&(1u<<i))OBJECTIVEGFX_activate(i);
        if(changed&(1u<<i))OBJECTIVEGFX_settle(i,5);
    }
    if(kind==2 && operations.delivered!=visualDelivered)OBJECTIVEGFX_activate(3);
    if(kind==3)for(u8 i=0;i<3;i++) {
        if(changed&(1u<<i))OBJECTIVEGFX_activate(i);
        else if(!(operations.done&(1u<<i))) {
            objectiveVisuals[i].x=enemies[i].x+8;
            objectiveVisuals[i].y=VIDEO_PROJECT_Y(enemies[i].y)+8;
        }
    }
    if(kind==5)for(u8 i=0;i<3;i++) {
        if(visualGateHp[i] && !operations.gateHp[i]) {
            OBJECTIVEGFX_activate(i);
        } else OBJECTIVEGFX_prime(i,operations.gateHp[i]<4);
        visualGateHp[i]=operations.gateHp[i];
    }
    if(kind==6) {
        if(operations.held>visualHeld){objectiveAnimationEvents[OART_CAGE]++;SFX_countPulse(FALSE);}
        for(u8 i=0;i<2;i++) {
            if(visualPhase && !operations.phase && operations.work[1])OBJECTIVEGFX_activate(i);
            else if(!operations.work[1] && objectiveVisuals[i].mode==2)OBJECTIVEGFX_idle(i);
            OBJECTIVEGFX_prime(i,i==1 ? operations.held!=0 : operations.held>=2 || operations.work[0]);
        }
    }
    if(kind==7) {
        if(!visualPhase && operations.phase)OBJECTIVEGFX_activate(0);
        if(visualPostHp && !operations.postHp) {
            objectiveVisuals[0].mode=3;objectiveVisuals[0].age=0;
            objectiveAnimationEvents[OART_RADIO]++;
        }
    }
    visualDone=operations.done;visualDelivered=operations.delivered;
    visualPhase=operations.phase;visualPostHp=operations.postHp;visualCargoOpen=operations.cargoOpen;visualHeld=operations.held;
}

void OPS_animateResult(void)
{
    // Freeze mission timers/combat while allowing the last destruction or
    // activation to finish. Animation ages stop in the ordinary pause state.
    OBJECTIVEGFX_update();OBJECTIVEGFX_ground(FALSE);
}

void OPS_update(void)
{
    OP_CLOCK();
    if(operations.outcome)return;
    const u8 kind=mission();
    if(operations.damageTimer)operations.damageTimer--;
    if(kind==4)operations.clock=(operations.clock+1)%(fps*18);
    else if(operations.clock)operations.clock--;
    switch(kind) {
        case 0:
            for(u8 i=0;i<3;i++)if(work(i,fps*2)) {
                if(operations.done==7){operations.phase=1;operations.clock=fps*25;}
                if(settings()->attacks)ENEMIES_trySpawn(roster,sizeof roster);
            }
            if(operations.phase){if(atExit())operations.outcome=OBJ_WON;else if(!operations.clock)operations.outcome=OBJ_LOST;}
            break;
        case 1:
            for(u8 i=0;i<2;i++)if(work(i,fps*3/2)){operations.phase=i+1;operations.damageTimer=fps*2;}
            if((operations.done&3)==3 && work(2,fps*2))operations.outcome=OBJ_WON;
            break;
        case 2:
            if(operations.cargo==255) {
                for(u8 i=0;i<3;i++)if(!(operations.done&(1u<<i))) {
                    const ArenaRect bag={points[i][0]+24,points[i][1]+8,16,16,FALSE};
                    if(!(operations.cargoOpen&(1u<<i)) && near(points[i][0],points[i][1])) {
                        operations.cargoOpen|=1u<<i;sfxItemPickup();
                    } else if((operations.cargoOpen&(1u<<i)) && objectiveVisuals[i].mode==2 &&
                        objectiveVisuals[i].age>=fps/3 && overlaps(&bag,px,py,16,16)) {
                        operations.cargo=i;operations.done|=1u<<i;sfxItemPickup();break;
                    }
                }
            } else if(near(64,304)) {
                operations.cargo=255;operations.delivered++;sfxItemPickup();
                if(operations.delivered==3){operations.bonus=1;healPlayer(15);PLAYER_grantShield();}
            }
            if(operations.delivered>=2 && atExit())operations.outcome=OBJ_WON;
            break;
        case 3:updateHunt();break;
        case 4:
            for(u8 i=0;i<3;i++)work(i,fps*3/2);
            if(operations.done==7 && atExit())operations.outcome=OBJ_WON;
            break;
        case 5:
            for(u8 i=0;i<3;i++)if(!operations.gateHp[i])operations.done|=1u<<i;
            if(!DINORAH_alive())operations.outcome=OBJ_LOST;
            else if(operations.done==7 && dinorahState==DIN_ARRIVED && atExit() &&
                getApproximatedDistance(px-dinorahX,py-dinorahY)<=64)operations.outcome=OBJ_WON;
            break;
        case 6:updateTrap();break;
        default:
            updatePost();if(operations.phase && near(64,304))operations.outcome=OBJ_WON;break;
    }
    OP_MARK(0);
    hazards();visualsSync();OBJECTIVEGFX_update();scenery();OBJECTIVEGFX_ground(FALSE);
    OP_MARK(1);
    if(!operations.outcome)reinforcement();
    u16 player=0,enemy=0;
    for(u8 i=0;i<MAX_PSHOTS;i++){player+=pshots[i].active!=0;enemy+=eshots[i].active!=0;}
    const u16 active=ENEMIES_activeCount();
    if(active>operations.peakEnemies)operations.peakEnemies=active;
    if(player>operations.peakPlayerShots)operations.peakPlayerShots=player;
    if(enemy>operations.peakEnemyShots)operations.peakEnemyShots=enemy;
    if(hudClock)hudClock--;else {OPS_drawHUD();hudClock=fps/5;}
    if((testTicks&3)==0)meter();
    OP_MARK(2);
    if(hp<=0)operations.outcome=OBJ_LOST;
    if(operations.outcome){testResult=operations.outcome;OPS_drawHUD();}
}

void OPS_draw(u16 *n)
{
    OP_CLOCK();
    if(!OPS_active())return;
    const u8 kind=mission();
    if(kind==3) {
        for(u8 i=0;i<3;i++)if(!(operations.done&(1u<<i)) && enemies[i].active)
            MARKERS_alert(n,enemies[i].x+12,enemies[i].y+12);
    } else if(kind==5) {
        if(DINORAH_alive()) {
            const u16 bar=ARENA_npcBar(dinorahHp,100);
            if(bar)SPRITES_emit(n,dinorahX-8,dinorahY-40,SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
            if(dinorahState==DIN_WAITING)MARKERS_alert(n,dinorahX+8,dinorahY);
        }
    } else if(kind==6) {
        if(operations.phase)MARKERS_alert(n,288,208);
    } else if(kind!=7)for(u8 i=0;i<3;i++) {
        if(kind==2 && (operations.done&(1u<<i)))continue;
        if(atWorkPoint(i) && operations.work[i] && !(operations.done&(1u<<i))) {
            const u16 value=(u32)operations.work[i]*100/(kind==0 || (kind==1 && i==2) ? fps*2 : fps*3/2);
            // Shared 32px progress bar, same palette and perspective as defense.
            const u16 bar=ARENA_npcBar(value-value%5,100);
            if(bar)SPRITES_emit(n,points[i][0]-16,points[i][1]-38,SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
        }
    }
    if(kind==2) {
        for(u8 i=0;i<3;i++)if((operations.cargoOpen&(1u<<i)) && !(operations.done&(1u<<i)) && objectiveVisuals[i].mode==2)
            OBJECTIVEGFX_cargo(n,points[i][0]+32,points[i][1]+16);
        if(operations.cargo!=255)OBJECTIVEGFX_cargo(n,px+20,py-4);
    }
    if(kind==7 && operations.phase)MARKERS_destination(n,64,304);
    else if(kind!=3 && kind!=6 && kind!=1)MARKERS_destination(n,448,304);
    OBJECTIVEGFX_draw(n);
    OP_MARK(3);
}

static void line(u8 row,const char *source)
{
    char text[39];memset(text,' ',38);const u16 length=strlen(source);memcpy(text,source,length>38 ? 38 : length);text[38]=0;
    if(!strcmp(lastHud[row],text))return;
    // Copy queued data: no DMA may refer to this stack buffer after returning.
    u16 tiles[38];for(u8 i=0;i<38;i++)tiles[i]=TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX+(u8)text[i]-32);
    VDP_setTileMapDataRow(WINDOW,tiles,HUD_ROWS+row+1,1,38,DMA_QUEUE_COPY);
    strcpy(lastHud[row],text);
}
void OPS_drawHUD(void)
{
    char value[16],aux[16]="";const u8 kind=mission();
    const u16 seconds=divu(operations.clock+fps-1,fps);
    const u32 signature=(u32)countDone()+((u32)operations.delivered<<3)+((u32)operations.captured<<6)+
        ((u32)seconds<<12)+((u32)operations.postHp<<20)+((u32)operations.outcome<<28)+
        operations.held*977UL+(kind==5 ? dinorahHp*1009UL+dinorahState*32749UL : 0);
    const char *hint=OPS_hint();if(hint!=lastHint){line(0,hint);lastHint=hint;}
    if(meterCold){
        line(1,kind==5 ? "INSETOS:00/03 TIROS PICO:00/00" : "INSETOS:00/04 TIROS PICO:00/00");
        line(2,fps==50 ? "FPS:50/50 CPU:000% PICO:000%" : "FPS:60/60 CPU:000% PICO:000%");
        meterCold=FALSE;
    }
    if(signature==objectiveSignature)return;
    objectiveSignature=signature;
    const char *title=operations.outcome==OBJ_WON ? "CONCLUÍDO" : operations.outcome==OBJ_LOST ? "FALHOU" : TEST_name(testStage);
    if(kind==2)sprintf(value,"%u/2",operations.delivered);
    else if(kind==6){sprintf(value,"%u/6",operations.captured);sprintf(aux,"PRES%u",operations.held);}
    else if(kind==5){sprintf(value,"%u/3",countDone());sprintf(aux,"D%03u",dinorahHp);}
    else if(kind==7){sprintf(value,"%03u",operations.postHp);sprintf(aux,"%02u",seconds);}
    else if(kind==0 && operations.phase)sprintf(value,"%02u S",seconds);
    else sprintf(value,"%u/3",countDone());
    HUD_drawObjective(operations.outcome ? title : kind==2 ? "ENTREGAS" : kind==5 ? "DINORAH" : kind==6 ? "CONTENÇÃO" : kind==7 ? "RÁDIO" : "MISSÃO",TILE_CLOCK,value,kind==7 ? TILE_CLOCK : 0,aux);
}
// Stagger small numeric DMA edits. Formatting three whole lines together used
// most of a frame on the 68000, even though the static labels never changed.
static void meter(void)
{
    const u8 field=meterField;meterField=(meterField+1)%6;
    static const u8 rows[]={2,2,2,1,1,1},cols[]={4,14,24,8,25,28},width[]={2,3,3,2,2,2};
    const u16 values[]={TEST_measuredFps(),SYS_getCPULoad(),TEST_peakCpu(),ENEMIES_activeCount(),operations.peakPlayerShots,operations.peakEnemyShots};
    u16 value=values[field];if(value>999)value=999;
    if(value==meterLast[field])return;
    meterLast[field]=value;
    u16 tiles[3];u8 n=width[field];
    while(n){const u16 q=divu(value,10);tiles[--n]=TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX+'0'-32+value-q*10);value=q;}
    VDP_setTileMapDataRow(WINDOW,tiles,HUD_ROWS+rows[field]+1,cols[field]+1,width[field],DMA_QUEUE_COPY);
}
