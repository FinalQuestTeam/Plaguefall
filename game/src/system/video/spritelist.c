// Hardware sprite list with global and per-scanline admission limits.
#include "system/video/spritelist.h"
#include "system/video/sprites/tiles.h"
#include "system/video/herogfx.h"
#include "system/video/enemygfx.h"
#include "system/video/combatgfx.h"
#include "system/video/projection.h"
#include "system/video/floor.h"
#include "system/video/chainfx.h"
#include "core/game.h"
#include "actors/player.h"
#include "actors/shots.h"
#include "enemies/enemies.h"
#include "items/items.h"
#include "actors/npc.h"
#include "actors/dinorah.h"
#include "core/objective.h"
#include "levels/arena.h"
#include "levels/levels.h"
#include "levels/test.h"
#include "levels/operations.h"
#include "levels/campaign_resistance.h"
#include "levels/graph.h"
#include "system/video/screens/hud.h"

// Conservative 8px scanline bands. Each band reserves the full width of
// every intersecting sprite, so real scanline limits can never be exceeded.
static u16 bandLoad[28],widthBound;
static void beginSprites(void){memset(bandLoad,0,sizeof bandLoad);widthBound=0;}
#ifdef RENDER_PROFILE
volatile u16 renderProfileTicks[4];
#define PROFILE_START() u32 profileClock=getSubTick()
#define PROFILE_MARK(i) do {u32 now=getSubTick();renderProfileTicks[i]=now-profileClock;profileClock=now;}while(0)
#else
#define PROFILE_START()
#define PROFILE_MARK(i)
#endif
static bool reserve(u16 n,s16 x,s16 y,u16 w,u16 h,u16 pieces)
{
    if(n+pieces>80 || x>=320 || x+(s16)w<=0 || y>=224 || y+(s16)h<=0)return FALSE;
    const u16 first=(y<0 ? 0 : y)>>3,last=((y+(s16)h>224 ? 224 : y+h)-1)>>3;
    const u16 load=(pieces==4 ? 0x200 : 0x100)+(w>>3);
    u16 *start=bandLoad+first,*end=bandLoad+last+1;
    if(n+pieces>20 || widthBound+(w>>3)>40)
        for(u16 *p=start;p<end;p++)if((u16)(*p+load+0x6b57u)&0x8080u)return FALSE;
    for(u16 *p=start;p<end;p++)*p+=load;
    widthBound+=w>>3;
    return TRUE;
}
__attribute__((always_inline)) static inline void writeSprite(u16 n,s16 x,s16 y,u8 size,u16 attr)
{
    VDPSprite *sprite=&vdpSpriteCache[n];
    sprite->y=y+128;sprite->size_link=((u16)size<<8)|(n+1);
    sprite->attribut=attr;sprite->x=x+128;
}
static bool emitSmall(u16 *n,s16 x,s16 y,u16 attr)
{
    x-=cameraX;y-=cameraY;
    if(*n>=80 || x>=320 || x+8<=0 || y>=224 || y+8<=0)return FALSE;
    const u16 first=(y<0 ? 0 : y)>>3,last=(y+7>223 ? 223 : y+7)>>3;
    if(((u16)(bandLoad[first]+0x6c58u)|(u16)(bandLoad[last]+0x6c58u))&0x8080u)return FALSE;
    bandLoad[first]+=0x101;if(first!=last)bandLoad[last]+=0x101;
    widthBound++;
    writeSprite(*n,x,y,SPRITE_SIZE(1,1),attr&0x7fff);(*n)++;return TRUE;
}
bool SPRITES_emit(u16 *n,s16 x,s16 y,u8 size,u16 attr)
{
    if(!size)return emitSmall(n,x,y,attr);
    x-=cameraX;y-=cameraY;
    const u16 w=(((size>>2)&3)+1)*8,h=((size&3)+1)*8;
    if(!reserve(*n,x,y,w,h,1))return FALSE;
    writeSprite(*n,x,y,size,attr&0x7fff);(*n)++;return TRUE;
}
static bool emitActor(u16 *n,s16 x,s16 y,u16 attr)
{
    x-=cameraX;y-=cameraY;
    if(!reserve(*n,x,y,32,48,2))return FALSE;
    attr&=0x7fff;
    writeSprite(*n,x,y,SPRITE_SIZE(4,4),attr);
    writeSprite(*n+1,x,y+32,SPRITE_SIZE(4,2),attr+16);
    *n+=2;return TRUE;
}
static u16 writeBoss(u16 n,s16 x,s16 y,u16 attr)
{
    const bool flip=(attr&(1u<<11))!=0;
    const s16 left=x+(flip?16:0),right=x+(flip?0:32);
    writeSprite(n++,left,y,SPRITE_SIZE(4,4),attr);
    writeSprite(n++,left,y+32,SPRITE_SIZE(4,2),attr+16);
    writeSprite(n++,right,y,SPRITE_SIZE(2,4),attr+24);
    writeSprite(n++,right,y+32,SPRITE_SIZE(2,2),attr+32);
    return n;
}
static bool emitBoss(u16 *n,s16 x,s16 y,u16 attr)
{
    x-=cameraX;y-=cameraY;
    if(!reserve(*n,x,y,48,48,4))return FALSE;
    *n=writeBoss(*n,x,y,attr&0x7fff);return TRUE;
}
static u16 finishSprites(u16 count){return count;}

// Keep the two dense projectile loops outside the large scene renderer.
__attribute__((noinline)) static u16 drawShots(u16 n,FShot *shot,u16 count,bool enemy)
{
    const s16 cx=cameraX,cy=cameraY+VIDEO_HEIGHT_OFFSET;
    const u16 *table=COMBATGFX_shotTable();
    VDPSprite *sprite=&vdpSpriteCache[n];
    for(FShot *end=shot+count;shot<end;shot++) {
        if(!shot->active)continue;
        const s16 x=(shot->x>>6)-cx,y=(shot->y>>6)-cy;
        if(n>=80)break;
        if((u16)(x+7)>=327 || (u16)(y+7)>=231)continue;
        const u16 first=(u16)(y<0?0:y)>>3,last=(u16)(y+7>223?223:y+7)>>3;
        if(((u16)(bandLoad[first]+0x6c58u)|(u16)(bandLoad[last]+0x6c58u))&0x8080u)continue;
        bandLoad[first]+=0x101;if(first!=last)bandLoad[last]+=0x101;
        widthBound++;
        const u16 attr=table && shot->renderPose ? table[shot->renderPose] : COMBATGFX_cachedShotAttr(shot,enemy?(shot->mode?shot->mode:1):0);
        sprite->y=y+128;sprite->size_link=++n;sprite->attribut=attr&0x7fff;sprite->x=x+128;sprite++;

    }
    return n;
}

void SPRITES_draw(void)
{
    static u16 frame;
    u16 n=0;
    frame++;
    PROFILE_START();
    HUD_flush();
    beginSprites();
    CHAINFX_update();
    const u8 dir=HERO_direction(faceX,faceY);
    PROFILE_MARK(0);
    HERO_prepare(dir);
    PROFILE_MARK(1);
    DINORAH_prepare();
    ENEMYGFX_prepare(frame);
    PROFILE_MARK(2);
    // Both actors are admitted before enemies/effects; nearest feet first.
    if(!DINORAH_hidden() && dinorahY>=py)
        emitActor(&n,dinorahX-8,dinorahY-31,TILE_ATTR_FULL(PAL2,TRUE,FALSE,DINORAH_flip(),DINORAH_tile()));
    if (!PLAYER_hidden())
    {
        const u16 tile=TILE_USER_INDEX+HERO_tile();
        emitActor(&n,px-8,py-31,
            TILE_ATTR_FULL(PAL2,TRUE,FALSE,HERO_flipH(),tile));
    }

    if(!DINORAH_hidden() && dinorahY<py)
        emitActor(&n,dinorahX-8,dinorahY-31,TILE_ATTR_FULL(PAL2,TRUE,FALSE,DINORAH_flip(),DINORAH_tile()));
    if (NPC_active() && ARENA_npcInMap())
    {
        // The mapped Santa is the one protected object. Its own image reacts
        // to damage; a readable life bar replaces the ambiguous floating icon.
        ARENA_showNpc(NPC_alive() && !NPC_hidden());
        if (NPC_alive())
        {
            const ArenaNpcVisual *visual=ARENA_npcVisual();
            // Red/yellow crown sparkle, with no opaque white or black pixels.
            // Use the regional rate so PAL and NTSC share a one-second cycle.
            if(visual && !NPC_hidden())
                SPRITES_emit(&n,visual->crownX,visual->crownY,SPRITE_SIZE(1,1),
                    TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+FLOOR_TILE_BASE+
                        visual->crownTile+(frame%fps>=fps/2)));
            const u16 bar=ARENA_npcBar(npcHp,npcHpMax);
            if(bar)
            {
                const s16 barY=npcY-48<cameraY+HUD_HEIGHT+4 ? cameraY+HUD_HEIGHT+4 : npcY-48;
                SPRITES_emit(&n,npcX+4,barY,SPRITE_SIZE(4,1),
                    TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
            }
        }
    }

    typedef struct { s16 x,y; u8 size,parent,flags; } StatusMarker;
    StatusMarker statuses[MAX_ENEMIES+1];
    u16 statusCount=0;
    // Share enemy shield artwork, positioning and scanline admission rules.
    if(PLAYER_shieldRemaining())
        statuses[statusCount++]=(StatusMarker){px-8,py-31,32,0,1};
    for (u16 k=0;k<MAX_ENEMIES;k++)
    {
        const u16 i=(k+frame)&(MAX_ENEMIES-1);
        const Enemy *e=&enemies[i];
        if (!e->active || CAMPAIGN_RESISTANCE_hideEnemy(i)) continue;
        // Mission transmitters own their authored32px bodies and destruction.
        if(!currentLevel && testStage==14 && i<3 && !(operations.done&(1u<<i)))continue;
        const EnemyDef *d=ENEMY_DEF(e);
        const u16 pal=e->hitFlash ? PAL0 : PAL1;
        const bool target=e->type==ENEMY_DUMMY || e->type==ENEMY_TARGET;
        if (!target && !ENEMYGFX_ready(i)) continue;
        // Native art and the unchanged ground hitbox have identical sizes.
        // Bodies and projectiles use the same projection, including all facings.
        const u16 size=d->size;
        const s16 x=e->x,y=VIDEO_PROJECT_Y(e->y);
        const u16 tile=TILE_USER_INDEX+(target ? ENEMYGFX_dirTile(e->type,4,0) : ENEMYGFX_entityTile(i));
        const u8 flip=target ? FALSE : ENEMYGFX_entityFlipH(i);
        const u16 attr=TILE_ATTR_FULL(pal,TRUE,FALSE,flip,tile);
        const u16 bodyIndex=n;
        if(size<=32)
        {
            if(!SPRITES_emit(&n,x,y,SPRITE_SIZE(size/8,size/8),attr))continue;
        }
        else if(!emitBoss(&n,x,y,attr))continue;
        if((e->shielded && d->color!=COLOR_PURPLE) || e->burn || e->frozen) {
            statuses[statusCount++]=(StatusMarker){x,y,size,bodyIndex+1,
                (e->shielded && d->color!=COLOR_PURPLE ? 1 : 0)|(e->burn ? 2 : 0)|(e->frozen ? 4 : 0)};
        }
        // Status marks use the existing checkerboard, subject to the same limits.
        if (e->frozen || e->burnFlash)
        {
            const u16 statusPal=e->frozen ? PAL1 : PAL0;
            SPRITES_emit(&n,x,y,SPRITE_SIZE((size>32?32:size)/8,(size>32?32:size)/8),
                TILE_ATTR_FULL(statusPal,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_STATUS));
        }
    }
    if (NPC_active() && currentLevel!=N_15 && !ARENA_npcInMap() && !NPC_hidden())
    {
            if ((frame%60)>=30)
                SPRITES_emit(&n,npcX+8,npcY,SPRITE_SIZE(1,1),
                    TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_SAINT_GLOW));
            SPRITES_emit(&n,npcX,npcY,SPRITE_SIZE(3,3),
                TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_SAINT));
    }
    for(u16 i=0;i<2;i++)if(allyShots[i].active)
        SPRITES_emit(&n,allyShots[i].x>>6,VIDEO_PROJECT_Y(allyShots[i].y>>6),SPRITE_SIZE(1,1),COMBATGFX_shotAttr(0,allyShots[i].vx,allyShots[i].vy));
    OBJECTIVE_drawMarkers(&n);
    if(!currentLevel && testStage>=OPS_FIRST_ROOM)OPS_draw(&n);
    n=drawShots(n,pshots,MAX_PSHOTS,FALSE);
    n=drawShots(n,eshots,MAX_ESHOTS,TRUE);
    // Admit bodies and projectiles before optional status markers. Crowded
    // scanlines may shed a marker, never an actor to make room for its icon.
    const StatusMarker *marker=statuses;
    for(u16 k=0;k<statusCount;k++,marker++)
    {
        const s16 size=marker->size,bodyY=marker->y;
        const u8 flags=marker->flags;
        if(flags==1) {
            s16 x=marker->x+(size-8)/2,y=bodyY-10;
            if(y<cameraY+HUD_HEIGHT+2) {
                y=bodyY+(size-8)/2;x=marker->x+size+2;
                if(x+8>cameraX+320)x=marker->x-10;
            }
            if(x<cameraX)x=cameraX;if(x>cameraX+312)x=cameraX+312;
            if(y<cameraY+HUD_HEIGHT+2)y=cameraY+HUD_HEIGHT+2;
            emitSmall(&n,x,y,TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_ENEMY_SHIELD));
            continue;
        }
        const u16 count=((flags&1)!=0)+((flags&2)!=0)+((flags&4)!=0);
        const s16 width=count*10-2;
        s16 x=marker->x+(size-width)/2,y=bodyY-10;
        // Concurrent statuses form one row. At the north edge, move beside
        // the body; clamp the entire row so no icon is hidden under the HUD.
        if(y<cameraY+HUD_HEIGHT+2) {
            y=bodyY+(size-8)/2;
            x=marker->x+size+2;
            if(x+width>cameraX+320)x=marker->x-width-2;
        }
        if(x<cameraX)x=cameraX;
        if(x>cameraX+320-width)x=cameraX+320-width;
        if(y<cameraY+HUD_HEIGHT+2)y=cameraY+HUD_HEIGHT+2;
        static const u16 tiles[3]={TILE_ENEMY_SHIELD,TILE_ENEMY_FIRE,TILE_ENEMY_ICE};
        for(u16 status=0;status<3;status++)if(flags&(1u<<status)) {
            SPRITES_emit(&n,x,y,SPRITE_SIZE(1,1),
                TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+tiles[status]));
            x+=10;
        }
    }
    n=CHAINFX_draw(n);
    if(currentLevel==0 && testStage==1) {
        const Enemy *e=&enemies[testSettings[0].selected];
        SPRITES_emit(&n,e->x+(ENEMY_SIZE(e)-8)/2,VIDEO_PROJECT_Y(e->y)-10,SPRITE_SIZE(1,1),
            TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_TEST_MARKER));
    }
    // Cosmetic corpses come after live bodies, bullets and combat markers.
    for(u16 i=0;i<COMBAT_DEATH_CAP;i++)
    {
        const CombatDeath *d=&combatDeaths[i];if(!d->active || !d->ready)continue;
        const u16 pal=d->age<(fps*4+99)/100 ? PAL0 : PAL1;
        const u16 attr=TILE_ATTR_FULL(pal,TRUE,FALSE,FALSE,TILE_USER_INDEX+d->tile);
        if(d->size<=32)SPRITES_emit(&n,d->x,VIDEO_PROJECT_Y(d->y),SPRITE_SIZE(d->size/8,d->size/8),attr);
        else emitBoss(&n,d->x,VIDEO_PROJECT_Y(d->y),attr);
    }
    // A drop is already collectible, but must not cover its own dying body.
    // Cosmetic corpses still enter after every live body and projectile.
    n=ITEMS_draw(n);
    if (!PLAYER_hidden())
        SPRITES_emit(&n,px,py+4,SPRITE_SIZE(2,2),
            TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_SHADOW));
    if(!DINORAH_hidden())SPRITES_emit(&n,dinorahX,dinorahY+4,SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_SHADOW));
    n=finishSprites(n);
    if (n)
    {
        VDP_setSpriteLink(n-1,0);
        VDP_updateSprites(n,DMA_QUEUE);
    }
    else SPRITES_hide();
    HERO_endFrame();
    PROFILE_MARK(3);
}

void SPRITES_hide(void)
{
    VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),
        TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_PSHOT),0);
    VDP_updateSprites(1,DMA_QUEUE);
}
