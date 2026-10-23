// Authored escort: bounded route, two ally bullets, PAL2 shared with Damião.
#include "actors/dinorah.h"
#include "actors/player.h"
#include "enemies/enemies.h"
#include "system/video/herogfx.h"
#include "system/video/sprites/tiles.h"
#include "system/video/actor_animation.h"
#include "system/video/actordeath.h"
#include "system/video/projection.h"
#include "system/audio/sfx.h"
#include "core/game.h"
#include <dinorah.h>
#define BASE (TILE_USER_INDEX+HERO_TILE_BASE+24)
static const u8 CANON[8]={0,1,2,3,4,3,2,1};
static const u8 MIRROR[8]={0,0,0,0,0,1,1,1};
// Idle barrel ends, read from the approved 32x48 Dinorah drawings.
static const u8 MUZZLE[5][2]={{17,11},{29,23},{30,27},{26,43},{21,45}};
s16 dinorahX,dinorahY,dinorahHp;
u8 dinorahState,dinorahNode;
FShot allyShots[2];
static const RouteDef *path;
static s32 dinorahFx,dinorahFy;
static s32 stepStartFx,stepStartFy,stepEndFx,stepEndFy;
static u16 dinorahInvTimer,dinorahPauseTimer,dinorahFireTimer,dinorahAimTimer,dinorahAnimTick;
static u8 dir,loadedDir,loadedPose,aimTarget,runDir;
static bool waiting,loaded,running,stepEndsNode;
void DINORAH_clear(void){path=NULL;dinorahHp=0;memset(allyShots,0,sizeof allyShots);loaded=FALSE;ACTORDEATH_clear(ACTOR_DEATH_DINORAH);}
bool DINORAH_active(void){return path!=NULL;}
bool DINORAH_alive(void){return path && dinorahHp>0;}
bool DINORAH_hidden(void){return !DINORAH_active() || (DINORAH_alive() && dinorahInvTimer && ((dinorahInvTimer>>2)&1));}
void DINORAH_start(const RouteDef *route)
{
    DINORAH_clear();path=route;dinorahHp=100;dinorahNode=1;dinorahState=DIN_MOVING;
    dinorahX=route->points[0].x-8;dinorahY=route->points[0].y-8;
    dinorahFx=(s32)dinorahX*64;dinorahFy=(s32)dinorahY*64;
    dinorahInvTimer=dinorahPauseTimer=dinorahAimTimer=dinorahAnimTick=0;dinorahFireTimer=fps*5/2;dir=loadedDir=2;loadedPose=0;
    waiting=running=stepEndsNode=FALSE;runDir=dir;
    VDP_loadTileData((const u32 *)dinorah_frames+CANON[dir]*ACTOR_VIEW_FRAMES*192,BASE,24,DMA);loaded=TRUE;
}
void DINORAH_damage(u16 damage)
{
    if(!DINORAH_alive() || dinorahInvTimer)return;
    dinorahHp-=damage;if(dinorahHp<0)dinorahHp=0;
    if(!dinorahHp) {
        ACTORDEATH_start(ACTOR_DEATH_DINORAH,MIRROR[loadedDir]);
        dinorahState=DIN_DEAD;running=FALSE;dinorahAimTimer=0;
        memset(allyShots,0,sizeof allyShots);
        dinorahInvTimer=0;return;
    }
    dinorahInvTimer=(fps*3+3)/4;
}
static bool safe(s16 x,s16 y)
{
    if(ARENA_blocked(x,y,16,16))return FALSE;
    const LevelDef *def=LEVEL_current();
    for(u16 i=0;i<def->lavaCount;i++) {
        const TileRect *r=&def->lava[i];
        if(x<r->x*8+r->w*8 && x+16>r->x*8 && y<r->y*8+r->h*8 && y+16>r->y*8)return FALSE;
    }
    return TRUE;
}
// A committed step and its four poses share the same clock. Short route
// segments spread their remaining distance over the whole cycle, so the
// feet reach the waypoint only on the final pose, without overshooting it.
static void moveStep(void)
{
    const u16 length=ACTOR_RUN_TICKS(fps)*ACTOR_RUN_FRAMES;
    const s32 nx=stepStartFx+(stepEndFx-stepStartFx)*(dinorahAnimTick+1)/length;
    const s32 ny=stepStartFy+(stepEndFy-stepStartFy)*(dinorahAnimTick+1)/length;
    if(safe(nx>>6,ny>>6)) {
        dinorahFx=nx;dinorahFy=ny;
        dinorahX=nx>>6;dinorahY=ny>>6;
        dinorahState=DIN_MOVING;
    } else {
        // A blocked step cannot continue through a wall, hole or lava.
        running=FALSE;dinorahAnimTick=0;dinorahState=DIN_WAITING;
    }
}
static bool clearShot(s16 tx,s16 ty)
{
    s16 dx=tx-(dinorahX+8),dy=ty-(dinorahY+8);
    u16 dist=getApproximatedDistance(dx,dy),steps=dist/8+1;
    for(u16 i=1;i<steps;i++)if(ARENA_playerShotBlocked(dinorahX+4+(s32)dx*i/steps,dinorahY+4+(s32)dy*i/steps))return FALSE;
    return TRUE;
}
static void fire(void)
{
    Enemy *e=&enemies[aimTarget];if(!e->active)return;
    const s16 half=ENEMY_SIZE(e)/2;
    s16 dx=e->x+half-(dinorahX+8),dy=e->y+half-(dinorahY+8);
    u16 dist=getApproximatedDistance(dx,dy);if(!dist || dist>112 || !clearShot(e->x+half,e->y+half))return;
    const u8 *anchor=MUZZLE[CANON[loadedDir]];
    const s16 mx=dinorahX-8+(MIRROR[loadedDir] ? 32-anchor[0] : anchor[0]),my=dinorahY-31+anchor[1]+VIDEO_HEIGHT_OFFSET;
    dx=e->x+half-mx;dy=e->y+half-my;dist=getApproximatedDistance(dx,dy);if(!dist)dist=1;
    for(u16 i=0;i<2;i++)if(!allyShots[i].active) {
        allyShots[i]=(FShot){(s32)(mx-4)*64,(s32)(my-4)*64,((s32)dx*180*64/fps)/dist,((s32)dy*180*64/fps)/dist,0,1,TRUE};
        SFX_playerShot();return;
    }
}
u16 DINORAH_update(void)
{
    if(!DINORAH_alive())return 0;
    u16 kills=0;
    if(dinorahInvTimer)dinorahInvTimer--;
    // Contact affects Dinorah only. No Santa shockwave, global flash or inventory.
    for(u16 i=0;i<MAX_ENEMIES;i++) {
        Enemy *e=&enemies[i];if(!e->active || !ENEMY_DEF(e)->contactDmg)continue;
        const u16 size=ENEMY_SIZE(e);
        if(e->x<dinorahX+16 && e->x+size>dinorahX && e->y<dinorahY+16 && e->y+size>dinorahY) {
            DINORAH_damage(12);ENEMIES_knockbackFrom(e,dinorahX+8,dinorahY+8);
        }
    }
    for(u16 i=0;i<2;i++) {
        FShot *s=&allyShots[i];if(!s->active)continue;s->x+=s->vx;s->y+=s->vy;
        s16 x=s->x>>6,y=s->y>>6;
        if(ARENA_playerShotBlocked(x,y)){s->active=FALSE;continue;}
        const u16 hit=ENEMIES_damageBox(x,y,8,8,ENEMY_STATUS_NONE);
        if(hit){s->active=FALSE;if(hit==ENEMY_HIT_KILLED)kills++;}
    }
    if(!DINORAH_alive())return kills;
    if(!running && ++dinorahAnimTick>=ACTOR_IDLE_TICKS(fps)*ACTOR_IDLE_FRAMES)dinorahAnimTick=0;
    const s16 ax=abs(px-dinorahX),ay=abs(py-dinorahY);
    if(waiting){if(ax<80 && ay<48)waiting=FALSE;}
    else if(ax>112 || ay>64)waiting=TRUE;
    if(dinorahFireTimer)dinorahFireTimer--;
    if(running) {
        // Wait for the displayed pose on DMA contention. Position advances
        // with the animation, never independently of the feet.
        if(loadedDir!=runDir || loadedPose!=ACTOR_IDLE_FRAMES+dinorahAnimTick/ACTOR_RUN_TICKS(fps))return kills;
        if(dinorahAnimTick+1<ACTOR_RUN_TICKS(fps)*ACTOR_RUN_FRAMES) {
            dinorahAnimTick++;moveStep();return kills;
        }
        running=FALSE;dinorahAnimTick=0;
        if(stepEndsNode) {
            dinorahPauseTimer=path->points[dinorahNode].pauseSeconds*fps;
            dinorahNode++;
        }
    }
    // Waiting for cover, aiming and waypoint pauses can begin only after
    // the committed step has finished both its movement and animation.
    if(dinorahAimTimer) {
        dinorahState=DIN_AIMING;
        if(!--dinorahAimTimer)fire();
        return kills;
    }
    if(!dinorahFireTimer) {
        u16 nearest=97;u8 target=0xff;
        for(u16 i=0;i<MAX_ENEMIES;i++) {
            Enemy *e=&enemies[i];if(!e->active)continue;
            const s16 half=ENEMY_SIZE(e)/2;const u16 dist=getApproximatedDistance(e->x+half-dinorahX-8,e->y+half-dinorahY-8);
            if(dist<nearest && clearShot(e->x+half,e->y+half)){nearest=dist;target=i;}
        }
        if(target!=0xff) {
            const Enemy *e=&enemies[target];s16 dx=e->x+ENEMY_SIZE(e)/2-dinorahX-8,dy=e->y+ENEMY_SIZE(e)/2-dinorahY-8;
            dir=HERO_direction(dx>4 ? 1 : dx< -4 ? -1 : 0,dy>4 ? 1 : dy< -4 ? -1 : 0);
            aimTarget=target;dinorahAimTimer=fps/6;dinorahFireTimer=fps*5/2;dinorahState=DIN_AIMING;return kills;
        }
    }
    if(waiting){dinorahState=DIN_WAITING;return kills;}
    if(dinorahPauseTimer){dinorahPauseTimer--;dinorahState=DIN_PAUSING;return kills;}
    if(dinorahNode>=path->count){dinorahState=DIN_ARRIVED;return kills;}
    const RoutePoint *p=&path->points[dinorahNode];
    s16 dx=p->x-8-dinorahX,dy=p->y-8-dinorahY;
    const u16 dist=getApproximatedDistance(dx,dy);
    if(dist<=1) {
        dinorahX=p->x-8;dinorahY=p->y-8;dinorahFx=(s32)dinorahX*64;dinorahFy=(s32)dinorahY*64;
        dinorahPauseTimer=p->pauseSeconds*fps;dinorahNode++;return kills;
    }
    dir=HERO_direction(dx>1 ? 1 : dx< -1 ? -1 : 0,dy>1 ? 1 : dy< -1 ? -1 : 0);
    const s32 stride=((36*64)/fps)*ACTOR_RUN_TICKS(fps)*ACTOR_RUN_FRAMES;
    stepStartFx=dinorahFx;stepStartFy=dinorahFy;
    stepEndsNode=(s32)dist*64<=stride;
    if(stepEndsNode) {
        stepEndFx=(s32)(p->x-8)*64;stepEndFy=(s32)(p->y-8)*64;
    } else {
        stepEndFx=dinorahFx+(s32)dx*stride/dist;
        stepEndFy=dinorahFy+(s32)dy*stride/dist;
    }
    running=TRUE;runDir=dir;dinorahAnimTick=0;moveStep();
    return kills;
}
void DINORAH_prepare(void)
{
    if(!DINORAH_active())return;
    if(ACTORDEATH_active(ACTOR_DEATH_DINORAH)) {
        ACTORDEATH_prepare(ACTOR_DEATH_DINORAH,BASE);return;
    }
    const u16 runStep=ACTOR_RUN_TICKS(fps),idleStep=ACTOR_IDLE_TICKS(fps);
    const u8 animDir=running ? runDir : dir;
    const u8 pose=running ? ACTOR_IDLE_FRAMES+dinorahAnimTick/runStep : dinorahAnimTick/idleStep;
    if(loaded && CANON[animDir]==CANON[loadedDir] && pose==loadedPose){loadedDir=animDir;return;}
    if(DMA_getQueueTransferSize()+768+1024>DMA_TRANSFER_CAPACITY_NTSC || DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return;
    if(!DMA_queueDma(DMA_VRAM,(void *)((const u32 *)dinorah_frames+(CANON[animDir]*ACTOR_VIEW_FRAMES+pose)*192),BASE*32,384,2))return;
    loadedDir=animDir;loadedPose=pose;loaded=TRUE;
}
u16 DINORAH_tile(void){return BASE;}
bool DINORAH_flip(void){return ACTORDEATH_active(ACTOR_DEATH_DINORAH) ? ACTORDEATH_flip(ACTOR_DEATH_DINORAH) : MIRROR[loadedDir];}
const char *DINORAH_status(void)
{
    switch(dinorahState){case DIN_DEAD:return "DINORAH CAIU";case DIN_WAITING:return "ME DÁ COBERTURA";case DIN_PAUSING:return "CONFERINDO PASSAGEM";case DIN_AIMING:return "COBRINDO VOCÊ";case DIN_ARRIVED:return "VEM PRA SAÍDA";default:return "AVANÇANDO";}
}
