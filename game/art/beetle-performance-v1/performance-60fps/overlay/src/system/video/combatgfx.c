#include "system/video/combatgfx.h"
#include "system/video/sprites/tiles.h"
#include "system/video/combat_art_layout.h"
#include "enemies/enemies.h"
#include "core/game.h"
#include "combat_art.h"

// Last fifteen menu-icon tiles, outside the countdown's first180tiles.
#define SHOT_BASE (ENEMY_ICON_BASE+15*ENEMY_ICON_TILES-15)
typedef char shots_outside_countdown[(SHOT_BASE>=ENEMY_ICON_BASE+180)?1:-1];
typedef char death_scratch_fits[(BOSS_ROT_COUNT>=68)?1:-1];
CombatDeath combatDeaths[COMBAT_DEATH_CAP];
static bool shotsReady,bossLayout;
static u8 deathCursor,deathActiveCount;
static u16 duration(u8 type) {return (fps*(type==ENEMY_BOSS ? 5 : 3)+9)/10;}
void COMBATGFX_clear(void)
{
    memset(combatDeaths,0,sizeof combatDeaths);bossLayout=FALSE;deathCursor=0;deathActiveCount=0;shotsReady=FALSE;
}
void COMBATGFX_invalidate(void)
{
    shotsReady=FALSE;
    for(u16 i=0;i<COMBAT_DEATH_CAP;i++)combatDeaths[i].ready=FALSE;
}
void COMBATGFX_spawn(u8 type,s16 x,s16 y)
{
    if(type>=ENEMY_TYPES || !COMBAT_DEATH_ART[type].tiles)return;
    if(type==ENEMY_BOSS)
    {
        // A boss uses36tiles. Reclaim normal effects, never live enemy frames.
        memset(combatDeaths,0,sizeof combatDeaths);deathActiveCount=0;bossLayout=TRUE;
    }
    const u16 first=bossLayout && type!=ENEMY_BOSS ? 1 : 0;
    const u16 cap=bossLayout ? (type==ENEMY_BOSS ? 1 : 3) : COMBAT_DEATH_CAP;
    for(u16 i=first;i<cap;i++)
    {
        CombatDeath *d=&combatDeaths[i];if(d->active)continue;
        const u16 offset=bossLayout ? (i ? 36+(i-1)*16 : 0) : i*16;
        deathActiveCount++;
        *d=(CombatDeath){x,y,0,BOSS_ROT_BASE+offset,type,ENEMY_DEFS[type]->size,255,TRUE,FALSE,0};
        return;
    }
    // Saturation falls back to the existing BG_A residue created by enemyDie.
}
void COMBATGFX_update(void)
{
    if(!deathActiveCount)return;
    bool any=FALSE;
    for(u16 i=0;i<COMBAT_DEATH_CAP;i++)
    {
        CombatDeath *d=&combatDeaths[i];if(!d->active)continue;
        if(++d->age>=duration(d->type)){d->active=FALSE;deathActiveCount--;continue;}
        any=TRUE;
    }
    if(!any)bossLayout=FALSE;
}
u16 COMBATGFX_remaining(void)
{
    if(!deathActiveCount)return 0;
    u16 left=0;
    for(u16 i=0;i<COMBAT_DEATH_CAP;i++)if(combatDeaths[i].active)
    {
        u16 n=duration(combatDeaths[i].type)-combatDeaths[i].age;if(n>left)left=n;
    }
    return left;
}
void COMBATGFX_prepare(u16 transfers)
{
    if(!shotsReady)
    {
        // Immutable ROM source is valid until DMA completes. No per-shot DMA.
        if(DMA_getQueueTransferSize()+480+1024<=DMA_TRANSFER_CAPACITY_NTSC &&
           DMA_getQueueSize()+3<DMA_getMaxQueueSize() &&
           DMA_queueDma(DMA_VRAM,(void *)combat_shots,(TILE_USER_INDEX+SHOT_BASE)*32,240,2))shotsReady=TRUE;
    }
    if(!deathActiveCount)return;
    for(u16 k=0;k<COMBAT_DEATH_CAP && transfers<ENEMY_DMA_FRAMES;k++)
    {
        CombatDeath *d=&combatDeaths[(deathCursor+k)%COMBAT_DEATH_CAP];if(!d->active)continue;
        const CombatDeathArt *a=&COMBAT_DEATH_ART[d->type];
        // Recoil40..120ms, folding120..200ms, collapsed until expiry.
        const u16 recoil=(fps*12+99)/100,fold=(fps*20+99)/100;
        const u8 wanted=d->age<recoil ? 0 : d->age<fold ? 1 : 2;
        if(d->ready && d->frame==wanted)continue;
        const u16 bytes=a->tiles*32;
        if(DMA_getQueueTransferSize()+bytes+1024>DMA_TRANSFER_CAPACITY_NTSC ||
           DMA_getQueueSize()+3>=DMA_getMaxQueueSize())break;
        const u32 *src=(const u32 *)combat_deaths+a->offset+wanted*a->tiles*8;
        if(!DMA_queueDma(DMA_VRAM,(void *)src,(TILE_USER_INDEX+d->tile)*32,a->tiles*16,2))break;
        d->ready=TRUE;d->frame=wanted;transfers++;
    }
    deathCursor=(deathCursor+1)%COMBAT_DEATH_CAP;
}
u16 COMBATGFX_shotAttr(u8 style,s32 vx,s32 vy)
{
    const s32 ax=vx<0 ? -vx : vx,ay=vy<0 ? -vy : vy;
    u16 pose;bool h=FALSE,v=FALSE;
    if((!vx && vy) || ax*2<ay){pose=1;v=vy<0;}
    else if((!vy && vx) || ay*2<ax){pose=0;h=vx<0;}
    else {pose=2;h=vx<0;v=vy<0;}
    if(style>4)style=1;
    const u16 tile=shotsReady ? SHOT_BASE+style*3+pose : (style ? TILE_ESHOT : TILE_PSHOT);
    return TILE_ATTR_FULL(PAL1,TRUE,v,h,TILE_USER_INDEX+tile);
}

static const u16 attrs[80]={
    TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+1),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+2),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+1),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+2),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+1),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+2),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+0),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+1),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+2),
    TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+4),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+5),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+4),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+5),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+4),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+5),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+3),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+4),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+5),
    TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+7),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+8),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+7),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+8),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+7),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+8),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+6),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+7),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+8),
    TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+10),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+11),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+10),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+11),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+10),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+11),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+9),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+10),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+11),
    TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+13),TILE_ATTR_FULL(PAL1,TRUE,0,0,TILE_USER_INDEX+SHOT_BASE+14),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+13),TILE_ATTR_FULL(PAL1,TRUE,0,1,TILE_USER_INDEX+SHOT_BASE+14),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+13),TILE_ATTR_FULL(PAL1,TRUE,1,0,TILE_USER_INDEX+SHOT_BASE+14),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+12),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+13),TILE_ATTR_FULL(PAL1,TRUE,1,1,TILE_USER_INDEX+SHOT_BASE+14)
};

const u16 *COMBATGFX_shotTable(void){return shotsReady?attrs:NULL;}
u16 COMBATGFX_cachedShotAttr(FShot *shot,u8 style)
{
    u8 key=shot->renderPose;
    if(!key) {
        const s32 vx=shot->vx,vy=shot->vy;
        const s32 ax=vx<0?-vx:vx,ay=vy<0?-vy:vy;
        if(ax*2<ay)key=2|(vy<0?8:0);
        else if(ay*2<ax)key=1|(vx<0?4:0);
        else key=3|(vx<0?4:0)|(vy<0?8:0);
        if(style>4)style=1;
        shot->renderPose=key|style<<4;
    }
    if(shotsReady)return attrs[shot->renderPose];
    return TILE_ATTR_FULL(PAL1,TRUE,(key&8)!=0,(key&4)!=0,TILE_USER_INDEX+(style?TILE_ESHOT:TILE_PSHOT));
}
