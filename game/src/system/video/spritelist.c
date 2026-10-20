// Hardware sprite list with global and per-scanline admission limits.
#include "system/video/spritelist.h"
#include "system/video/sprites/tiles.h"
#include "system/video/chars.h"
#include "system/video/herogfx.h"
#include "system/video/enemygfx.h"
#include "system/video/projection.h"
#include "system/video/chainfx.h"
#include "core/game.h"
#include "actors/player.h"
#include "actors/shots.h"
#include "enemies/enemies.h"
#include "items/items.h"
#include "actors/npc.h"

static const u8 FACE_DIR[3][3]={{7,0,1},{6,0,2},{5,4,3}};
// Four exact scanlines per 32-bit word: each byte is an independent lane.
// Counts stay <=20 and widths (in8px units) <=40, so packed adds never carry
// into the next scanline. This preserves exact pixel-row limits without
// scanning every row three times for each32x48 actor on the68000.
#define LINE_WORDS (224/4)
static u32 lineSprites[LINE_WORDS];
static u32 linePixels[LINE_WORDS];
static u32 usedSpriteBits,usedPixelBits;
// Stage a frame, then certify its combined scanline load with one prefix sum.
// Only overloaded frames need the detailed priority-preserving admission pass.
typedef struct { s16 x,y; u16 attr; u8 size,pieces; } PendingSprite;
static PendingSprite pending[80];
static u16 lineDelta[225];
static u16 totalWidths,firstLine,lastLine;
static bool deferred;

static void beginSprites(void)
{
    memset(lineDelta,0,sizeof lineDelta);
    totalWidths=0;firstLine=224;lastLine=0;deferred=TRUE;
}

#ifdef RENDER_PROFILE
volatile u16 renderProfileTicks[4];
#define PROFILE_START() u32 profileClock=getSubTick()
#define PROFILE_MARK(index) do {u32 now=getSubTick();renderProfileTicks[index]=now-profileClock;profileClock=now;}while(0)
#else
#define PROFILE_START()
#define PROFILE_MARK(index)
#endif


static bool reserve(u16 n,s16 x,s16 y,u16 w,u16 h,u16 pieces)
{
    if(n+pieces>80 || x>=320 || x+(s16)w<=0 || y>=224 || y+(s16)h<=0)return FALSE;
    const u16 first=y<0 ? 0 : y;
    const u16 last=y+(s16)h>224 ? 224 : y+h;
    const u16 begin=first>>2,end=(last-1)>>2;
    const u32 firstMask=0x80808080UL<<((first&3)*8);
    const u32 lastMask=0x80808080UL>>((3-((last-1)&3))*8);
    const u16 rowCount=pieces==4 ? 2 : 1;
    const u32 countBias=pieces==4 ? 0x6d6d6d6dUL : 0x6c6c6c6cUL;
    const u32 countStep=pieces==4 ? 0x02020202UL : 0x01010101UL;
    const u32 pixels=w==48 ? 0x06060606UL : w==32 ? 0x04040404UL : w==24 ? 0x03030303UL :
                     w==16 ? 0x02020202UL : 0x01010101UL;
    const u32 pixelBias=0x57575757UL+pixels;
    // OR is a conservative upper bound for each byte lane. Most ordinary
    // frames are far below the limits, so no per-word admission scan is needed.
    if(((usedSpriteBits+countBias)|(usedPixelBits+pixelBias))&0x80808080UL)
    {
        for(u16 i=begin;i<=end;i++)
        {
            u32 mask=0x80808080UL;
            if(i==begin)mask&=firstMask;
            if(i==end)mask&=lastMask;
            if(((lineSprites[i]+countBias)|(linePixels[i]+pixelBias))&mask)return FALSE;
        }
    }
    // Commit only after the whole interval passes. Handle partial edge words
    // once; the interior is a straight packed add with advancing pointers.
    u32 countBits=usedSpriteBits,pixelBits=usedPixelBits;
    u32 lanes=(firstMask&(begin==end ? lastMask : 0x80808080UL))>>7;
    u32 bytes=(lanes<<8)-lanes;
    u32 count=lineSprites[begin]+lanes*rowCount;
    u32 width=linePixels[begin]+(pixels&bytes);
    lineSprites[begin]=count;linePixels[begin]=width;
    countBits|=count;pixelBits|=width;
    if(begin!=end)
    {
        u32 *counts=&lineSprites[begin+1],*widths=&linePixels[begin+1];
        u16 remaining=end-begin-1;
        while(remaining--)
        {
            count=*counts+countStep;width=*widths+pixels;
            *counts++=count;*widths++=width;
            countBits|=count;pixelBits|=width;
        }
        lanes=lastMask>>7;bytes=(lanes<<8)-lanes;
        count=lineSprites[end]+lanes*rowCount;width=linePixels[end]+(pixels&bytes);
        lineSprites[end]=count;linePixels[end]=width;
        countBits|=count;pixelBits|=width;
    }
    usedSpriteBits=countBits;usedPixelBits=pixelBits;
    return TRUE;
}

__attribute__((always_inline)) static inline bool admit(u16 n,s16 x,s16 y,u16 w,u16 h,u16 pieces,u8 size,u16 attr)
{
    if(!deferred)return reserve(n,x,y,w,h,pieces);
    const s16 right=x+w,bottom=y+h;
    if((u16)(n+pieces)>80 || x>=320 || right<=0 || y>=224 || bottom<=0)return FALSE;
    const u16 first=y<0 ? 0 : y,last=bottom>224 ? 224 : bottom;
    const u16 load=(pieces==4 ? 0x200 : 0x100)+(w>>3);
    lineDelta[first]+=load;lineDelta[last]-=load;
    if(first<firstLine)firstLine=first;
    if(last>lastLine)lastLine=last;
    totalWidths+=w>>3;
    pending[n]=(PendingSprite){x,y,attr,size,pieces};
    return TRUE;
}

bool SPRITES_emit(u16 *n,s16 x,s16 y,u8 size,u16 attr)
{
    const u16 w=(((size>>2)&3)+1)*8,h=((size&3)+1)*8;
    if(!admit(*n,x,y,w,h,1,size,attr))return FALSE;
    if(!deferred)VDP_setSpriteFull(*n,x,y,size,attr,*n+1);
    (*n)++;
    return TRUE;
}

static bool emitActor(u16 *n,s16 x,s16 y,u16 attr)
{
    // The two hardware pieces occupy disjoint rows: one count per row.
    if(!admit(*n,x,y,32,48,2,SPRITE_SIZE(4,4),attr))return FALSE;
    if(!deferred)
    {
        VDP_setSpriteFull(*n,x,y,SPRITE_SIZE(4,4),attr,*n+1);
        VDP_setSpriteFull(*n+1,x,y+32,SPRITE_SIZE(4,2),attr+16,*n+2);
    }
    *n+=2;
    return TRUE;
}

static u16 writeBoss(u16 n,s16 x,s16 y,u16 attr)
{
    const bool flip=(attr&(1u<<11))!=0;
    const s16 left=x+(flip?16:0),right=x+(flip?0:32);
    VDP_setSpriteFull(n,left,y,SPRITE_SIZE(4,4),attr,n+1);n++;
    VDP_setSpriteFull(n,left,y+32,SPRITE_SIZE(4,2),attr+16,n+1);n++;
    VDP_setSpriteFull(n,right,y,SPRITE_SIZE(2,4),attr+24,n+1);n++;
    VDP_setSpriteFull(n,right,y+32,SPRITE_SIZE(2,2),attr+32,n+1);n++;
    return n;
}

static bool emitBoss(u16 *n,s16 x,s16 y,u16 attr)
{
    // Reserve the whole 48x48 box atomically. Both columns count on each
    // scanline; retaining one atomic group avoids partially rendered bosses.
    if(!admit(*n,x,y,48,48,4,SPRITE_SIZE(4,4),attr))return FALSE;
    if(!deferred)writeBoss(*n,x,y,attr);
    *n+=4;return TRUE;
}

static u16 finishSprites(u16 count)
{
    bool overloaded=FALSE;
    if(count>20 || totalWidths>40)
    {
        u16 load=0;
        for(u16 y=firstLine;y<lastLine;y++)
        {
            load+=lineDelta[y];
            // Byte lanes: >20 entries or >40 eight-pixel units. A width
            // carry requires >=64 entries, which already fails the count lane.
            if((u16)(load+0x6b57u)&0x8080u){overloaded=TRUE;break;}
        }
    }
    if(overloaded)
    {
        memset(lineSprites,0,sizeof lineSprites);memset(linePixels,0,sizeof linePixels);
        usedSpriteBits=usedPixelBits=0;
    }
    deferred=FALSE;
    u16 n=0;
    for(u16 i=0;i<count;)
    {
        const PendingSprite *s=&pending[i];
        const u16 w=s->pieces==4 ? 48 : (((s->size>>2)&3)+1)*8,h=s->pieces>=2 ? 48 : ((s->size&3)+1)*8;
        i+=s->pieces;
        if(overloaded && !reserve(n,s->x,s->y,w,h,s->pieces))continue;
        if(s->pieces==4){n=writeBoss(n,s->x,s->y,s->attr);continue;}
        VDP_setSpriteFull(n,s->x,s->y,s->size,s->attr,n+1);n++;
        if(s->pieces==2)
        {
            VDP_setSpriteFull(n,s->x,s->y+32,SPRITE_SIZE(4,2),s->attr+16,n+1);n++;
        }
    }
    return n;
}

void SPRITES_draw(void)
{
    static u16 frame;
    u16 n=0;
    frame++;
    PROFILE_START();
    beginSprites();
    CHAINFX_update();
    const u8 dir=FACE_DIR[faceY+1][faceX+1];
    PROFILE_MARK(0);
    HERO_prepare(dir);
    PROFILE_MARK(1);
    ENEMYGFX_prepare(frame);
    PROFILE_MARK(2);
    if (!PLAYER_hidden())
    {
        const u16 tile=TILE_USER_INDEX+HERO_tile();
        emitActor(&n,px-8,py-31,
            TILE_ATTR_FULL(PAL2,TRUE,FALSE,HERO_flipH(),tile));
    }

    for (u16 k=0;k<MAX_ENEMIES;k++)
    {
        const u16 i=(k+frame)&(MAX_ENEMIES-1);
        const Enemy *e=&enemies[i];
        if (!e->active || (e->shielded && ((frame>>2)&1))) continue;
        const EnemyDef *d=ENEMY_DEF(e);
        const u16 pal=e->hitFlash ? PAL0 : PAL1;
        if (e->type==ENEMY_DUMMY || e->type==ENEMY_TARGET)
        {
            SPRITES_emit(&n,e->x,VIDEO_PROJECT_Y(e->y),SPRITE_SIZE(3,3),
                TILE_ATTR_FULL(pal,TRUE,FALSE,FALSE,TILE_USER_INDEX+ENEMYGFX_dirTile(e->type,4,0)));
            continue;
        }
        if (!ENEMYGFX_ready(i)) continue;
        // Native art and the unchanged ground hitbox have identical sizes.
        // Bodies and projectiles use the same projection, including all facings.
        const u16 size=d->size;
        const s16 x=e->x,y=VIDEO_PROJECT_Y(e->y);
        const u16 tile=TILE_USER_INDEX+ENEMYGFX_entityTile(i);
        const u8 flip=ENEMYGFX_entityFlipH(i);
        const u16 attr=TILE_ATTR_FULL(pal,TRUE,FALSE,flip,tile);
        if(size<=32)
        {
            if(!SPRITES_emit(&n,x,y,SPRITE_SIZE(size/8,size/8),attr))continue;
        }
        else if(!emitBoss(&n,x,y,attr))continue;
        // Status marks use the existing checkerboard, subject to the same limits.
        if (e->frozen || e->burnFlash)
        {
            const u16 statusPal=e->frozen ? PAL1 : PAL0;
            SPRITES_emit(&n,x,y,SPRITE_SIZE((size>32?32:size)/8,(size>32?32:size)/8),
                TILE_ATTR_FULL(statusPal,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_STATUS));
        }
    }
    if (NPC_active() && !NPC_hidden())
    {
        if ((frame%60)>=30)
            SPRITES_emit(&n,npcX+8,npcY,SPRITE_SIZE(1,1),
                TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_SAINT_GLOW));
        SPRITES_emit(&n,npcX,npcY,SPRITE_SIZE(3,3),
            TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_SAINT));
    }
    n=ITEMS_draw(n);
    for (u16 i=0;i<MAX_PSHOTS;i++)
        if (pshots[i].active)
            // Shot simulation remains in ground coordinates; draw at gun height.
            SPRITES_emit(&n,pshots[i].x>>6,(pshots[i].y>>6)-VIDEO_HEIGHT_OFFSET,SPRITE_SIZE(1,1),
                TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_PSHOT));
    for (u16 i=0;i<MAX_ESHOTS;i++)
        if (eshots[i].active)
            SPRITES_emit(&n,eshots[i].x>>6,VIDEO_PROJECT_Y(eshots[i].y>>6),SPRITE_SIZE(1,1),
                TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_ESHOT));
    n=CHAINFX_draw(n);
    if (!PLAYER_hidden())
        SPRITES_emit(&n,px,py+4,SPRITE_SIZE(2,2),
            TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_SHADOW));
    n=finishSprites(n);
    if (n)
    {
        VDP_setSpriteLink(n-1,0);
        VDP_updateSprites(n,DMA_QUEUE);
    }
    else SPRITES_hide();
    PROFILE_MARK(3);
}

void SPRITES_hide(void)
{
    VDP_setSpriteFull(0,0,-32,SPRITE_SIZE(1,1),
        TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,TILE_USER_INDEX+TILE_PSHOT),0);
    VDP_updateSprites(1,DMA_QUEUE);
}
