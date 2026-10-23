// Five drawn facings + horizontal symmetry, shared by type, facing and pose.
// No vertical flip: south is a separately drawn camera view.
#include "system/video/enemygfx.h"
#include "system/video/actor_animation.h"
#include "system/video/enemy_asset_layout.h"
#include "system/video/sprites/tiles.h"
#include "system/video/sprites/training_target_data.h"
#include "enemies/enemies.h"
#include "actors/player.h"
#include "core/game.h"
#include "insects.h"
#include "system/video/combatgfx.h"
#include "levels/levels.h"
#include "levels/test.h"
#include "system/video/screens/countdown.h"

#define CACHE_BLOCK_TILES 4
#define CACHE_BLOCKS (ENEMY_CACHE_TILES / CACHE_BLOCK_TILES)
static u8 blockOwner[CACHE_BLOCKS];
static u16 pinnedFrames;
static u8 evictionCursor;

typedef char EnemyCapacityMustBePowerOfTwo[((MAX_ENEMIES & (MAX_ENEMIES-1)) == 0) ? 1 : -1];

typedef struct
{
    s16 x, y;
    u8 type, dir, pose, wantedDir, wantedPose, motion;
    bool valid, seen;
    u16 tile;
    u8 block,blocks;
} FrameSlot;

static FrameSlot slots[MAX_ENEMIES];
// Entity state stays separate from immutable cached artwork. Multiple actors
// may reference a queued frame, including opposite facings using an H-flip.
// Zero in frameForKey means absent; entries otherwise store cache index + 1.
typedef struct { u16 tile,key; u8 block,blocks,refs; bool valid; } CachedFrame;
static CachedFrame cachedFrames[MAX_ENEMIES];
static u8 frameForKey[ENEMY_TYPES*32],slotFrame[MAX_ENEMIES];
static bool iconReady[ENEMY_TYPES];
static u8 nextSlot;
static const u8 CANON[8] = {0,1,2,3,4,3,2,1};
static const u8 MIRROR[8] = {0,0,0,0,0,1,1,1};

static bool newArt(u8 type) { return type < ENEMY_DUMMY || type == ENEMY_BOSS; }

static u16 iconTile(u8 type) { return ENEMY_ICON_BASE + type * ENEMY_ICON_TILES; }

static void loadIcon(u8 type)
{
    if (type >= ENEMY_TYPES || iconReady[type]) return;
    if (newArt(type))
        VDP_loadTileData((const u32 *) insect_icons + type * 128,
                        TILE_USER_INDEX + iconTile(type), ENEMY_ICON_TILES, DMA);
    else
    {
        // Existing sandbox targets retain their old 24x24 char-map.
        u32 data[16 * 8] = {0};
        for (u16 y=0; y<24; y++)
            for (u16 x=0; x<24; x++)
            {
                const char c = TRAINING_TARGET_ART[y][x];
                const u16 color = c=='.' ? 0 : c=='o' ? 11 :
                    (c=='h' || c=='w') ? 1 : c=='e' ? 2 : c=='l' ? 6 : 13;
                data[((x/8)*3+y/8)*8+y%8] |= (u32)color << ((7-x%8)*4);
            }
        VDP_loadTileData(data,TILE_USER_INDEX+iconTile(type),16,DMA);
    }
    iconReady[type] = TRUE;
    if(type==ENEMY_BOSS)COMBATGFX_invalidate();
}

void ENEMYGFX_loadForPhase(u8 phase, const u8 *types, u16 count)
{
    (void) phase;
    for (u16 i=0; i<count; i++) loadIcon(types[i]);
}

void ENEMYGFX_dropBoss(void)
{
    // Portrait scratch is separate from all cache/icon tiles.
}

void ENEMYGFX_reset(void)
{
    memset(slots,0,sizeof(slots));
    memset(cachedFrames,0,sizeof cachedFrames);
    memset(frameForKey,0,sizeof frameForKey);
    memset(slotFrame,255,sizeof slotFrame);
    memset(iconReady,0,sizeof(iconReady));
    memset(blockOwner,255,sizeof blockOwner);
    pinnedFrames=0;evictionCursor=0;nextSlot=0;
    COMBATGFX_invalidate();
}

static void releaseSlot(u16 index)
{
    FrameSlot *s=&slots[index];
    if(slotFrame[index]!=255)cachedFrames[slotFrame[index]].refs--;
    s->blocks=0;s->valid=FALSE;slotFrame[index]=255;
}

static void releaseFrame(u16 index)
{
    CachedFrame *c=&cachedFrames[index];
    if(c->valid)frameForKey[c->key]=0;
    for(u16 b=c->block;b<c->block+c->blocks;b++)blockOwner[b]=255;
    c->blocks=0;c->valid=FALSE;
    // Eviction invalidates every alias before these tiles can be overwritten.
    for(u16 i=0;i<MAX_ENEMIES;i++)if(slotFrame[i]==index)releaseSlot(i);
}

static u8 allocateFrame(u16 actor,u16 tiles)
{
    const u16 needed=(tiles+CACHE_BLOCK_TILES-1)/CACHE_BLOCK_TILES;
    const u16 limit=COUNTDOWN_active() ? CACHE_BLOCKS-COUNTDOWN_CACHE_TILES/CACHE_BLOCK_TILES : CACHE_BLOCKS;
    for(u16 attempt=0;attempt<=MAX_ENEMIES;attempt++)
    {
        u16 index=0;
        while(index<MAX_ENEMIES && cachedFrames[index].blocks)index++;
        u16 run=0;
        for(u16 b=0;index<MAX_ENEMIES && b<limit;b++)
        {
            if(blockOwner[b]!=255){run=0;continue;}
            if(++run<needed)continue;
            CachedFrame *c=&cachedFrames[index];
            c->block=b+1-needed;c->blocks=needed;
            c->tile=ENEMY_ROT_BASE+c->block*CACHE_BLOCK_TILES;
            for(u16 j=c->block;j<=b;j++)blockOwner[j]=index;
            return index;
        }
        // Never evict artwork already selected by an actor this frame,
        // whether it came from a new DMA or a shared cache hit.
        bool freed=FALSE;
        for(u16 k=0;k<MAX_ENEMIES;k++)
        {
            const u16 victim=(evictionCursor+k)&(MAX_ENEMIES-1);
            if(!cachedFrames[victim].blocks || (pinnedFrames&(1u<<victim)))continue;
            CachedFrame *c=&cachedFrames[victim];
            // Preserve every other actor's fallback image until it can bind
            // its next frame. An exclusively owned frame can be overwritten.
            if(c->refs && !(c->refs==1 && slotFrame[actor]==victim))continue;
            const u16 block=c->block;
            const bool reuse=c->blocks>=needed && block+needed<=limit;
            releaseFrame(victim);evictionCursor=(victim+1)&(MAX_ENEMIES-1);
            if(reuse) {
                c->block=block;c->blocks=needed;c->tile=ENEMY_ROT_BASE+block*CACHE_BLOCK_TILES;
                for(u16 b=block;b<block+needed;b++)blockOwner[b]=victim;
                return victim;
            }
            freed=TRUE;break;
        }
        if(!freed)break;
    }
    return 255;
}

static void selectFrame(u16 index,u8 cached)
{
    FrameSlot *s=&slots[index];
    const CachedFrame *c=&cachedFrames[cached];
    if(slotFrame[index]!=cached){releaseSlot(index);cachedFrames[cached].refs++;}
    slotFrame[index]=cached;s->tile=c->tile;s->block=c->block;s->blocks=c->blocks;
    s->dir=s->wantedDir;s->pose=s->wantedPose;s->valid=TRUE;
    pinnedFrames|=1u<<cached;
}

static u8 facing(const Enemy *e,const FrameSlot *s)
{
    // Ice and recoil do not turn an actor around. A telegraphed dash keeps
    // the same heading through its wind-up and the whole locked charge.
    if ((e->frozen || e->stun) && s->valid) return s->dir;
    const bool boss=e->type==ENEMY_BOSS;
    const bool bossAttack=boss && !(divu(e->tA,4*fps)&1);
    const bool charge=e->mode!=0 && (ENEMY_DEF(e)->color==COLOR_ORANGE || bossAttack);
    if ((charge || (s->motion && (!boss || bossAttack))) && (e->vx || e->vy))
        return ENEMYGFX_faceDir(e->vx,e->vy);
    const s16 half=ENEMY_SIZE(e)/2;
    const s16 tx=boss || e->aggroPlayer ? px+8 : chaseX;
    const s16 ty=boss || e->aggroPlayer ? py+8 : chaseY;
    const s16 dx=tx-e->x-half,dy=ty-e->y-half;
    return dx || dy ? ENEMYGFX_faceDir(dx,dy) : s->valid ? s->dir : 4;
}

void ENEMYGFX_prepare(u16 frame)
{
    u16 transfers=0;
    bool uploadsBlocked=FALSE;
    const u16 allowance=COMBATGFX_remaining() ? ENEMY_DMA_FRAMES-1 : ENEMY_DMA_FRAMES;
    pinnedFrames=0;
    const u16 runPhase=divu(frame,ACTOR_RUN_TICKS(fps))&(ACTOR_RUN_FRAMES-1);
    const u16 idlePhase=divu(frame,ACTOR_IDLE_TICKS(fps))&(ACTOR_IDLE_FRAMES-1);
    for (u16 i=0; i<MAX_ENEMIES; i++)
    {
        FrameSlot *s=&slots[i];
        const Enemy *e=&enemies[i];
        if (!e->active || !newArt(e->type))
        {if(s->blocks)releaseSlot(i);s->valid=FALSE;s->seen=FALSE;continue;}
        if(s->type!=e->type){releaseSlot(i);s->type=e->type;s->seen=FALSE;s->motion=0;}
        const bool moved=s->seen && (s->x!=e->x || s->y!=e->y);
        // Hold movement briefly through subpixel steps below one pixel/frame.
        if (moved) s->motion=3;
        else if (s->motion) s->motion--;
        if (e->frozen || (e->mode==1 &&
            (ENEMY_DEF(e)->color==COLOR_ORANGE || e->type==ENEMY_BOSS))) s->motion=0;
        s->wantedDir=facing(e,s);
        s->wantedPose=e->frozen ? 0 : s->motion ?
            ACTOR_IDLE_FRAMES+((runPhase+i)&(ACTOR_RUN_FRAMES-1)) :
            (idlePhase+i)&(ACTOR_IDLE_FRAMES-1);
        if(currentLevel==0 && testStage==1)TEST_animation(i,&s->wantedDir,&s->wantedPose);
        // Mirroring needs no upload, even when another actor uses the last
        // DMA allowance or this actor's next animation pose is still pending.
        if(s->valid && CANON[s->dir]==CANON[s->wantedDir])s->dir=s->wantedDir;
        if(s->valid && CANON[s->dir]==CANON[s->wantedDir] && s->pose==s->wantedPose)
            pinnedFrames|=1u<<slotFrame[i];
        s->x=e->x; s->y=e->y; s->seen=TRUE;
    }
    // Round-robin keeps a frequently turning enemy from starving other slots.
    for (u16 k=0; k<MAX_ENEMIES; k++)
    {
        const u16 i=(nextSlot+k)&(MAX_ENEMIES-1);
        FrameSlot *s=&slots[i];
        const Enemy *e=&enemies[i];
        if (!e->active || !newArt(e->type)) continue;
        if (s->valid && s->type==e->type &&
            CANON[s->dir]==CANON[s->wantedDir] && s->pose==s->wantedPose)
        { s->dir=s->wantedDir;pinnedFrames|=1u<<slotFrame[i];continue; }
        const u16 key=((u16)e->type<<5)+CANON[s->wantedDir]*ACTOR_VIEW_FRAMES+s->wantedPose;
        if(frameForKey[key]){selectFrame(i,frameForKey[key]-1);continue;}
        // Cache hits remain available after the upload allowance is exhausted.
        if(transfers>=allowance || uploadsBlocked)continue;
        // Keep at least 1024 bytes and two queue entries for SAT/HUD/other DMA.
        const EnemyArt *art=&ENEMY_ART[e->type];
        const u16 bytes=art->tiles*32;
        if (DMA_getQueueTransferSize()+bytes+1024>DMA_TRANSFER_CAPACITY_NTSC ||
            DMA_getQueueSize()+3>=DMA_getMaxQueueSize())continue;
        const u8 cached=allocateFrame(i,art->tiles);
        if(cached==255)continue;
        CachedFrame *c=&cachedFrames[cached];
        const u32 *source=(const u32 *)insect_frames+art->offset+
            (CANON[s->wantedDir]*ACTOR_VIEW_FRAMES+s->wantedPose)*art->words;
        if(!DMA_queueDma(DMA_VRAM,(void *)source,(TILE_USER_INDEX+c->tile)*32,art->tiles*16,2))
        {releaseFrame(cached);uploadsBlocked=TRUE;continue;}
        c->key=key;c->valid=TRUE;frameForKey[key]=cached+1;
        selectFrame(i,cached);
        transfers++;
    }
    nextSlot=(nextSlot+ENEMY_DMA_FRAMES)&(MAX_ENEMIES-1);
    COMBATGFX_prepare(transfers);
}

bool ENEMYGFX_ready(u16 index)
{
    return slots[index].valid && slots[index].type==enemies[index].type;
}
u16 ENEMYGFX_entityTile(u16 index) { return slots[index].tile; }
u8 ENEMYGFX_entityFlipH(u16 index) { return MIRROR[slots[index].dir]; }

u16 ENEMYGFX_dirTile(u8 type,u8 dir,u8 frame)
{
    (void)dir; (void)frame;
    loadIcon(type);
    return iconTile(type);
}
u8 ENEMYGFX_dirFlipH(u8 type,u8 dir) { (void)type; return MIRROR[dir]; }
u8 ENEMYGFX_dirFlipV(u8 type,u8 dir) { (void)type; (void)dir; return 0; }

void ENEMYGFX_drawOnMap(u8 type,u16 col,u16 row)
{
    loadIcon(type);
    const u16 size=ENEMY_DEFS[type]->size;
    const u16 nt=(size>32 ? 32 : size)/8;
    for (u16 tc=0; tc<nt; tc++)
        for (u16 tr=0; tr<nt; tr++)
            VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(PAL1,FALSE,FALSE,FALSE,
                TILE_USER_INDEX+iconTile(type)+tc*nt+tr),col+tc,row+tr);
}

u8 ENEMYGFX_faceDir(s16 dx,s16 dy)
{
    const s16 ax=dx<0 ? -dx : dx, ay=dy<0 ? -dy : dy;
    if (ax*2<ay) return dy<0 ? 0 : 4;
    if (ay*2<ax) return dx>0 ? 2 : 6;
    if (dx>0) return dy<0 ? 1 : 3;
    return dy<0 ? 7 : 5;
}
