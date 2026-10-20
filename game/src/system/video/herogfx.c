// Human protagonist: one 32x48 frame in the existing player VRAM reservation.
#include "system/video/herogfx.h"
#include "system/video/chars.h"
#include "system/video/enemygfx.h"
#include "system/video/actor_animation.h"
#include "core/game.h"
#include "heroi.h"

static const u8 CANON[8]={0,1,2,3,4,3,2,1};
static const u8 MIRROR[8]={0,0,0,0,0,1,1,1};
static s16 lastX,lastY;
static u16 animTick;
static u8 loadedDir,loadedPose,motion;
static bool running,loaded;

static const u32 *frameData(u8 dir,u8 pose)
{
    return (const u32 *)heroi_frames+(CANON[dir]*ACTOR_VIEW_FRAMES+pose)*192;
}

void HERO_load(void)
{
    PAL_setColors(PAL2*16,(const u16 *)heroi_palette,16,DMA);
    VDP_loadTileData(frameData(2,0),TILE_USER_INDEX+CHARS_TILE_BASE,24,DMA);
    loadedDir=2;loadedPose=0;loaded=TRUE;
    lastX=px;lastY=py;animTick=0;motion=0;running=FALSE;
}

void HERO_prepare(u8 dir)
{
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
                    (TILE_USER_INDEX+CHARS_TILE_BASE)*32,384,2))return;
    loadedDir=dir;loadedPose=pose;loaded=TRUE;
}

u16 HERO_tile(void){return CHARS_TILE_BASE;}
u8 HERO_flipH(void){return MIRROR[loadedDir];}

void HERO_loadPreview(void)
{
    // Menus can borrow 120 of the 384 enemy cache tiles for all five views.
    ENEMYGFX_reset();
    PAL_setColors(PAL2*16,(const u16 *)heroi_palette,16,DMA);
    for(u8 d=0;d<5;d++)
        VDP_loadTileData(frameData(d,0),TILE_USER_INDEX+ENEMY_ROT_BASE+d*24,24,DMA);
}
u16 HERO_previewTile(u8 dir){return ENEMY_ROT_BASE+CANON[dir]*24;}
u8 HERO_previewFlipH(u8 dir){return MIRROR[dir];}
