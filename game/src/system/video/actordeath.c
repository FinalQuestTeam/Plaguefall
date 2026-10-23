// Four authored collapse poses streamed into each actor's existing 24 tiles.
#include "system/video/actordeath.h"
#include "core/game.h"
#include <actor_deaths.h>
ActorDeath actorDeaths[2];
static u16 hold(u8 pose){return pose==ACTOR_DEATH_FRAMES-1 ? fps/2 : (fps*15+99)/100;}
void ACTORDEATH_clear(u8 actor){memset(&actorDeaths[actor],0,sizeof(ActorDeath));}
bool ACTORDEATH_active(u8 actor){return actorDeaths[actor].active;}
bool ACTORDEATH_flip(u8 actor){return actorDeaths[actor].flip;}
void ACTORDEATH_start(u8 actor,bool flip)
{
    if(ACTORDEATH_active(actor))return;
    actorDeaths[actor]=(ActorDeath){0,0,0xff,TRUE,flip};
}
void ACTORDEATH_update(void)
{
    for(u16 i=0;i<2;i++) {
        ActorDeath *d=&actorDeaths[i];
        // A pose receives its full hold even if DMA had to defer its upload.
        if(!d->active || d->loadedPose!=d->pose || d->tick>=hold(d->pose))continue;
        if(++d->tick==hold(d->pose) && d->pose<ACTOR_DEATH_FRAMES-1){d->pose++;d->tick=0;}
    }
}
bool ACTORDEATH_pending(void)
{
    for(u16 i=0;i<2;i++) {
        const ActorDeath *d=&actorDeaths[i];
        if(d->active && (d->pose<ACTOR_DEATH_FRAMES-1 || d->loadedPose!=d->pose || d->tick<hold(d->pose)))return TRUE;
    }
    return FALSE;
}
void ACTORDEATH_prepare(u8 actor,u16 tile)
{
    ActorDeath *d=&actorDeaths[actor];
    if(!d->active || d->loadedPose==d->pose)return;
    if(DMA_getQueueTransferSize()+768+1024>DMA_TRANSFER_CAPACITY_NTSC || DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return;
    const u32 *src=(const u32 *)actor_death_frames+(actor*ACTOR_DEATH_FRAMES+d->pose)*192;
    if(DMA_queueDma(DMA_VRAM,(void *)src,tile*32,384,2))d->loadedPose=d->pose;
}
