// Human protagonist: one 32x48 frame in the existing player VRAM reservation.
#include "system/video/herogfx.h"
#include "system/video/sprites/tiles.h"
#include "system/video/enemygfx.h"
#include "system/video/actor_animation.h"
#include "system/video/hero_muzzle.h"
#include "system/video/actordeath.h"
#include "core/game.h"
#include "heroi.h"

static const u8 CANON[8]={0,1,2,3,4,3,2,1};
static const u8 MIRROR[8]={0,0,0,0,0,1,1,1};
static s16 lastX,lastY;
static u16 animTick;
static u8 loadedDir,loadedPose,motion;
static bool running,loaded,prepared;

static const u32 *frameData(u8 dir,u8 pose)
{
    return (const u32 *)heroi_frames+(CANON[dir]*ACTOR_VIEW_FRAMES+pose)*192;
}

void HERO_load(void)
{
    ACTORDEATH_clear(ACTOR_DEATH_HERO);
    PAL_setColors(PAL2*16,(const u16 *)heroi_palette,16,DMA);
    VDP_loadTileData(frameData(2,0),TILE_USER_INDEX+HERO_TILE_BASE,24,DMA);
    loadedDir=2;loadedPose=0;loaded=TRUE;
    lastX=px;lastY=py;animTick=0;motion=0;running=FALSE;prepared=FALSE;
}

void HERO_prepare(u8 dir)
{
    if(ACTORDEATH_active(ACTOR_DEATH_HERO)) {
        ACTORDEATH_prepare(ACTOR_DEATH_HERO,TILE_USER_INDEX+HERO_TILE_BASE);
        return;
    }
    // Firing and drawing share one animation/DMA decision per game frame.
    if(prepared)return;
    prepared=TRUE;
    const bool moved=px!=lastX || py!=lastY;
    lastX=px;lastY=py;
    if(moved) motion=3; else if(motion) motion--;
    const bool nextRunning=motion!=0;
    if(nextRunning!=running){running=nextRunning;animTick=0;}
    else animTick++;
    u16 step=running ? ACTOR_RUN_TICKS(fps) : ACTOR_IDLE_TICKS(fps);
    if(step==0)step=1;
    const u16 length=running ? ACTOR_RUN_FRAMES : ACTOR_IDLE_FRAMES;
    if(animTick>=step*length)animTick=0;
    const u8 pose=(running ? ACTOR_IDLE_FRAMES : 0)+animTick/step;
    if(loaded && CANON[dir]==CANON[loadedDir] && pose==loadedPose)
    {loadedDir=dir;return;}
    // Player is submitted before enemy DMA, while reserving SAT/HUD bandwidth.
    if(DMA_getQueueTransferSize()+768+1024>DMA_TRANSFER_CAPACITY_NTSC ||
       DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return;
    if(!DMA_queueDma(DMA_VRAM,(void *)frameData(dir,pose),
                    (TILE_USER_INDEX+HERO_TILE_BASE)*32,384,2))return;
    loadedDir=dir;loadedPose=pose;loaded=TRUE;
}

void HERO_endFrame(void){prepared=FALSE;}

u8 HERO_direction(s16 x,s16 y)
{
    static const u8 dirs[3][3]={{7,0,1},{6,0,2},{5,4,3}};
    return dirs[y+1][x+1];
}

void HERO_muzzle(s16 *x,s16 *y)
{
    const u8 *anchor=HERO_MUZZLE[CANON[loadedDir]][loadedPose];
    *x=px-8+(MIRROR[loadedDir] ? 32-anchor[0] : anchor[0]);
    *y=py-31+anchor[1];
}

u16 HERO_tile(void){return HERO_TILE_BASE;}
u8 HERO_flipH(void){return ACTORDEATH_active(ACTOR_DEATH_HERO) ? ACTORDEATH_flip(ACTOR_DEATH_HERO) : MIRROR[loadedDir];}
