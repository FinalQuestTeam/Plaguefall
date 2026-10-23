// Production loader against a recording DMA; no renderer or emulator required.
#include <assert.h>
#include <stdio.h>
typedef int VDPPlane;
#include "system/video/enemygfx.c"

const u32 insect_frames[ENEMY_ASSET_LONGWORDS]={0},insect_icons[1920]={0};
Enemy enemies[MAX_ENEMIES];
static const EnemyDef small={.size=16},medium={.size=24},large={.size=32};
static const EnemyDef orange={.size=16,.color=COLOR_ORANGE},boss={.size=48};
const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES]={
    &small,&small,&large,&orange,&small,&small,&small,&orange,
    &medium,&medium,&large,&orange,&medium,&medium,&boss};
s16 px,py,chaseX,chaseY;
u16 fps=60;
u8 currentLevel=1,testStage;
static u16 bytes,uploads;
static bool failDMA,preview;
static u8 previewDir,previewPose;
static u32 sourceWord;
static bool individualPreview,countdown;
static u8 previewDirs[MAX_ENEMIES],previewPoses[MAX_ENEMIES];
static u32 tileSource[ENEMY_CACHE_TILES];
static bool writtenThisFrame[ENEMY_CACHE_TILES];
u16 DMA_getQueueTransferSize(void){return bytes;}
u16 DMA_getQueueSize(void){return uploads;}
u16 DMA_getMaxQueueSize(void){return 80;}
bool DMA_queueDma(u8 kind,void *source,u16 dest,u16 words,u16 step)
{
    assert(kind==DMA_VRAM && step==2);
    if(failDMA)return false;
    sourceWord=(const u32 *)source-insect_frames;
    const u16 first=dest/32-TILE_USER_INDEX-ENEMY_ROT_BASE;
    assert(first+words/16<=ENEMY_CACHE_TILES);
    for(u16 tile=0;tile<words/16;tile++) {
        assert(!writtenThisFrame[first+tile]);
        writtenThisFrame[first+tile]=true;tileSource[first+tile]=sourceWord+tile*8;
    }
    uploads++;bytes+=words*2;assert(uploads<=ENEMY_DMA_FRAMES);
    return true;
}
void VDP_loadTileData(const u32 *data,u16 tile,u16 count,u8 mode)
{(void)data;(void)tile;(void)count;(void)mode;}
void VDP_setTileMapXY(u16 plane,u16 attr,u16 col,u16 row)
{(void)plane;(void)attr;(void)col;(void)row;}
void COMBATGFX_invalidate(void){}
u16 COMBATGFX_remaining(void){return 0;}
void COMBATGFX_prepare(u16 transfers){assert(transfers==uploads);}
bool COUNTDOWN_active(void){return countdown;}
bool TEST_animation(u8 index,u8 *dir,u8 *pose)
{if(preview){*dir=individualPreview ? previewDirs[index] : previewDir;*pose=individualPreview ? previewPoses[index] : previewPose;}return preview;}
static void tick(u16 frame){bytes=uploads=0;memset(writtenThisFrame,0,sizeof writtenThisFrame);ENEMYGFX_prepare(frame);}
static Enemy *spawn(u8 type)
{
    memset(enemies,0,sizeof enemies);ENEMYGFX_reset();
    Enemy *e=&enemies[0];e->active=true;e->type=type;e->x=100;e->y=100;
    px=160;py=100;chaseX=168;chaseY=108;
    preview=individualPreview=countdown=false;currentLevel=1;failDMA=false;return e;
}
static void gallery(void)
{
    for(u8 type=0;type<ENEMY_TYPES;type++)if(type<ENEMY_DUMMY || type==ENEMY_BOSS)
        for(u8 dir=0;dir<8;dir++)for(u8 pose=0;pose<6;pose++)
        {
            spawn(type);currentLevel=0;testStage=1;preview=true;previewDir=dir;previewPose=pose;
            tick(0);assert(ENEMYGFX_ready(0));
            assert(slots[0].dir==dir && slots[0].pose==pose);
            assert(ENEMYGFX_entityFlipH(0)==(dir>=5));
            const EnemyArt *art=&ENEMY_ART[type];
            const u8 canonical[]={0,1,2,3,4,3,2,1};
            assert(sourceWord==art->offset+(canonical[dir]*6+pose)*art->words);
        }
    preview=false;currentLevel=1;
}
static void movement(void)
{
    static const s16 dx[]={0,64,64,64,0,-64,-64,-64};
    static const s16 dy[]={-64,-64,0,64,64,64,0,-64};
    for(u8 type=0;type<ENEMY_TYPES;type++)if(type<ENEMY_DUMMY || type==ENEMY_BOSS)
        for(u8 dir=0;dir<8;dir++)
        {
            Enemy *e=spawn(type);s16 half=ENEMY_SIZE(e)/2;
            chaseX=e->x+half+dx[dir];chaseY=e->y+half+dy[dir];
            px=chaseX-8;py=chaseY-8;tick(0);assert(slots[0].dir==dir);
            e->vx=dx[dir];e->vy=dy[dir];e->x+=dx[dir]/64;e->y+=dy[dir]/64;
            // Put the target behind the movement: the current heading wins.
            chaseX=px=e->x-dx[dir];chaseY=py=e->y-dy[dir];
            tick(0);assert(slots[0].dir==dir);
            e->frozen=10;tick(0);assert(slots[0].dir==dir);
            e->frozen=0;e->stun=10;e->vx=-e->vx;e->vy=-e->vy;
            e->x++;tick(0);assert(slots[0].dir==dir);
        }
}
static void attacks(void)
{
    for(u8 type=0;type<ENEMY_TYPES;type++)if(type==ENEMY_BOSS || ENEMY_DEFS[type]->color==COLOR_ORANGE)
    {
        Enemy *e=spawn(type);e->mode=1;e->vx=64;e->vy=64;
        px=py=0;chaseX=chaseY=0;tick(0);assert(slots[0].dir==3 && slots[0].pose<2);
        // Wind-up must keep the locked velocity after the motion grace ends.
        for(u16 f=0;f<8;f++){tick(f);assert(slots[0].dir==3);}
        e->mode=2;e->x++;e->y++;tick(0);assert(slots[0].dir==3);
    }
    Enemy *e=spawn(ENEMY_BOSS);e->tA=4*fps;e->vx=-64;e->vy=0;
    tick(0);e->x--;tick(0);assert(slots[0].dir==2); // retreat while facing player
    e=spawn(ENEMY_SQ_RED);chaseX=0;chaseY=108;tick(0);assert(slots[0].dir==6);
    e->aggroPlayer=true;tick(0);assert(slots[0].dir==2);
    // Overlapping centers have no heading: retain the last valid direction.
    px=e->x;py=e->y;tick(0);assert(slots[0].dir==2);
}
static void mirrorWithoutBandwidth(void)
{
    spawn(ENEMY_SQ_PUR);tick(0);assert(slots[0].dir==2);
    chaseX=0;bytes=6500;uploads=0;ENEMYGFX_prepare(fps);
    assert(!uploads && slots[0].dir==6 && ENEMYGFX_entityFlipH(0));
    // A failed upload keeps a complete old view, and a reused type stays hidden.
    chaseX=108;chaseY=0;failDMA=true;tick(0);assert(slots[0].dir==6);
    enemies[0].type=ENEMY_BOSS;tick(0);assert(!ENEMYGFX_ready(0));
    failDMA=false;
}

static void checkSharedPool(void)
{
    for(u16 f=0;f<MAX_ENEMIES;f++) {
        const CachedFrame *c=&cachedFrames[f];
        u16 refs=0;for(u16 i=0;i<MAX_ENEMIES;i++)refs+=slotFrame[i]==f;
        assert(refs==c->refs);
        if(!c->blocks){assert(!c->valid);continue;}
        assert(c->block+c->blocks<=CACHE_BLOCKS);
        for(u16 b=c->block;b<c->block+c->blocks;b++)assert(blockOwner[b]==f);
        if(c->valid)assert(frameForKey[c->key]==f+1);
    }
    for(u16 key=0;key<ENEMY_TYPES*32;key++)if(frameForKey[key]) {
        const CachedFrame *c=&cachedFrames[frameForKey[key]-1];
        assert(c->valid && c->key==key);
    }
    for(u16 i=0;i<MAX_ENEMIES;i++)if(slots[i].valid) {
        const FrameSlot *s=&slots[i];const CachedFrame *c=&cachedFrames[slotFrame[i]];
        const u16 view=CANON[s->dir]*ACTOR_VIEW_FRAMES+s->pose;
        assert(c->valid && c->key==((u16)s->type<<5)+view);
        assert(s->tile==c->tile && s->blocks==c->blocks && s->block==c->block);
        const EnemyArt *art=&ENEMY_ART[s->type];
        for(u16 t=0;t<art->tiles;t++)
            assert(tileSource[c->block*CACHE_BLOCK_TILES+t]==art->offset+view*art->words+t*8);
    }
}

static void sharing(void)
{
    spawn(ENEMY_SQ_PUR);currentLevel=0;testStage=1;preview=true;previewDir=2;previewPose=2;
    for(u16 i=1;i<8;i++)enemies[i]=enemies[0];
    tick(0);assert(uploads==1 && bytes==512);
    for(u16 i=0;i<8;i++){assert(ENEMYGFX_ready(i));assert(slots[i].tile==slots[0].tile);}
    checkSharedPool();
    // Removing the original actor cannot release another actor's graphics.
    const u16 oldTile=slots[0].tile;
    enemies[0].active=false;enemies[1].type=ENEMY_PEN_PUR;
    tick(0);assert(uploads==1);
    for(u16 i=2;i<8;i++)assert(ENEMYGFX_ready(i) && slots[i].tile==oldTile);
    assert(slots[1].tile!=oldTile);checkSharedPool();
    // Cache hits work even when this frame has no upload budget left.
    releaseSlot(7);bytes=6500;uploads=0;ENEMYGFX_prepare(0);
    assert(!uploads && ENEMYGFX_ready(7) && slots[7].tile==oldTile);checkSharedPool();

    spawn(ENEMY_SQ_PUR);currentLevel=0;testStage=1;preview=individualPreview=true;
    for(u16 i=0;i<8;i++) {
        enemies[i]=enemies[0];previewDirs[i]=i&1 ? 6 : 2;previewPoses[i]=2+i%4;
    }
    tick(0);assert(uploads==4 && bytes==2048);
    for(u16 i=0;i<8;i++){assert(ENEMYGFX_ready(i));assert(ENEMYGFX_entityFlipH(i)==(i&1));}
    // All four walking poses stay resident; changing phase needs no new DMA.
    for(u16 frame=1;frame<80;frame++) {
        for(u16 i=0;i<8;i++)previewPoses[i]=2+(frame+i)%4;
        tick(frame);assert(!uploads);checkSharedPool();
    }
    // One actor freezing must not overwrite the walking poses of its peers.
    previewPoses[0]=0;tick(80);assert(uploads==1);checkSharedPool();

    // Churn all species, canonical views and poses, including cache pressure
    // from multiple 48px bosses. Every visible alias must reference its own art.
    for(u16 frame=0;frame<1200;frame++) {
        countdown=(frame%31)<4;
        for(u16 i=0;i<MAX_ENEMIES;i++) {
            enemies[i].active=(frame+i)%9!=0;
            enemies[i].type=frame%5 ? (frame+i)%12 : ENEMY_BOSS;
            previewDirs[i]=(frame/3+i)%8;previewPoses[i]=(frame+i)%6;
        }
        failDMA=frame%19==0;tick(frame+81);checkSharedPool();
    }
    failDMA=false;countdown=false;
}
int main(void)
{
    for(fps=50;fps<=60;fps+=10){gallery();movement();attacks();mirrorWithoutBandwidth();sharing();}
    puts("1248 gallery frames; all 13 actors in 8 directions at 50/60Hz; sharing, mirrored aliases, independent poses, exhausted DMA, despawn/type changes and 2400 cache-pressure/failure frames passed.");
    return 0;
}
