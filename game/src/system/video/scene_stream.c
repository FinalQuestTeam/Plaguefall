// Exact ROM patterns are cached only while visible below the24px WINDOW HUD.
// No approximate pattern substitution. Each scene declares its resident budget.
#include "system/video/scene_stream.h"
#include "system/video/screens/loading.h"
#include "system/video/screens/hud.h"
#include "system/video/floor.h"
#include "levels/courtyard_data.h"
#define CAP capacity
#define BASE (TILE_USER_INDEX+FLOOR_TILE_BASE)
#define NONE 0xffff
static const ArenaScene *streamScene;
static u16 *persistent,*work,*owner,*location,*refs,*freeNext,*freePrev;
static bool suspended;
static u16 capacity,freeCount,freeHead,freeTail;
static s16 left=-1,right,top,bottom;
static s16 lastPixelX,warmCol=-1,warmRow;
static s8 warmDirection=1;
volatile u16 sceneStreamFaults,sceneStreamPeak,sceneStreamUploads;
static const u16 *rowAt(s16 y)
{
    // The exported map contains12800 cells. Narrow before pointer arithmetic
    // so68000 emits MULU.W rather than a32-bit software multiplication.
    return streamScene->map+(u16)(y*streamScene->cols);
}
static bool allocateWork(void)
{
    work=MEM_alloc((streamScene->stream->sourceCount+CAP*3)*2);
    if(!work){sceneStreamFaults++;return FALSE;}
    location=work;refs=location+streamScene->stream->sourceCount;freeNext=refs+CAP;freePrev=freeNext+CAP;
    memset(location,255,streamScene->stream->sourceCount*2);memset(refs,0,CAP*2);freeCount=0;freeHead=freeTail=NONE;
    for(u16 i=0;i<CAP;i++)if(owner[i]!=NONE)location[owner[i]]=i;
    if(left>=0)for(s16 y=top;y<=bottom;y++) {
        const u16 *line=rowAt(y);
        for(s16 x=left;x<=right;x++){u16 slot=location[line[x]];if(slot==NONE){sceneStreamFaults++;return FALSE;}refs[slot]++;}
    }
    for(u16 i=0;i<CAP;i++)if(!refs[i]) {
        freePrev[i]=freeTail;freeNext[i]=NONE;
        if(freeTail!=NONE)freeNext[freeTail]=i;else freeHead=i;
        freeTail=i;freeCount++;
    }
    return TRUE;
}
bool SCENESTREAM_begin(const ArenaScene *scene)
{
    SCENESTREAM_end();sceneStreamFaults=sceneStreamPeak=sceneStreamUploads=0;
    if(!scene->tileCount || scene->tileCount>COURTYARD_TILE_COUNT)return FALSE;
    capacity=scene->tileCount;streamScene=scene;
    persistent=MEM_alloc(CAP*2);
    if(!persistent){sceneStreamFaults++;streamScene=NULL;return FALSE;}
    owner=persistent;memset(owner,255,CAP*2);left=-1;warmCol=-1;lastPixelX=-1;warmDirection=1;
    if(allocateWork())return TRUE;
    SCENESTREAM_end();return FALSE;
}
static void releaseWork(void)
{
    if(work){MEM_free(work);work=NULL;location=refs=freeNext=freePrev=NULL;}
}
void SCENESTREAM_suspend(void)
{
    if(!streamScene || suspended)return;
    releaseWork();
    // The paused HUD does not compose pixels. Its existing scratch keeps the
    // small slot identity snapshot, freeing ALL cache heap for the32KiB panel.
    void *scratch=HUD_pausedScratch(CAP*2);
    if(!scratch){sceneStreamFaults++;return;}
    memcpy(scratch,persistent,CAP*2);MEM_free(persistent);
    persistent=owner=NULL;suspended=TRUE;
}
bool SCENESTREAM_resume(void)
{
    if(!streamScene || work)return TRUE;
    if(suspended) {
        persistent=MEM_alloc(CAP*2);
        if(!persistent){sceneStreamFaults++;return FALSE;}
        memcpy(persistent,HUD_pausedScratch(CAP*2),CAP*2);
        owner=persistent;suspended=FALSE;
    }
    return allocateWork();
}
void SCENESTREAM_end(void)
{
    releaseWork();if(persistent)MEM_free(persistent);
    persistent=owner=NULL;streamScene=NULL;left=-1;
    suspended=FALSE;
}
static inline __attribute__((always_inline)) void removeFree(u16 slot)
{
    const u16 prev=freePrev[slot],next=freeNext[slot];
    if(prev==NONE)freeHead=next;else freeNext[prev]=next;
    if(next==NONE)freeTail=prev;else freePrev[next]=prev;
    freeCount--;
}
static inline __attribute__((always_inline)) void releaseCell(u16 id)
{
    const u16 slot=location[id];
    if(slot==NONE || !refs[slot]){sceneStreamFaults++;return;}
    if(!--refs[slot]) {
        // Keep recently invisible patterns until a slot is actually needed.
        // This avoids re-uploading the same materials during small pans.
        freePrev[slot]=freeTail;freeNext[slot]=NONE;
        if(freeTail!=NONE)freeNext[freeTail]=slot;else freeHead=slot;
        freeTail=slot;freeCount++;
    }
}
static inline __attribute__((always_inline)) void enterCell(u16 id,bool initial)
{
    u16 slot=location[id];
    if(slot==NONE) {
        if(!freeCount){sceneStreamFaults++;return;}
        slot=freeHead;removeFree(slot);
        if(owner[slot]!=NONE)location[owner[slot]]=NONE;
        owner[slot]=id;location[id]=slot;refs[slot]=0;
        const u32 *source=streamScene->tiles+(u32)id*8;
        if(initial)LOADING_tiles(source,BASE+slot,1,DMA);
        // Exported arrays are32-byte aligned. One tile cannot cross a128KiB
        // DMA source bank, so the bank-splitting wrapper is unnecessary.
        else if(!DMA_queueDmaFast(DMA_VRAM,(void *)source,(BASE+slot)*32,16,2))sceneStreamFaults++;
        sceneStreamUploads++;
    }
    else if(!refs[slot])removeFree(slot);
    refs[slot]++;
}
static u16 attrAt(s16 x,s16 y)
{
    return TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,BASE+location[rowAt(y)[x]]);
}
static void cells(s16 x,s16 y,s16 w,s16 h,bool entering,bool initial)
{
    if(w<=0 || h<=0)return;
    const u16 *line=rowAt(y)+x;
    if(w==1) {
        if(entering)while(h--){enterCell(*line,initial);line+=streamScene->cols;}
        else while(h--){releaseCell(*line);line+=streamScene->cols;}
        return;
    }
    while(h--) {
        const u16 *p=line;
        for(s16 n=0;n<w;n++)if(entering)enterCell(*p++,initial);else releaseCell(*p++);
        line+=streamScene->cols;
    }
}
static void writeColumn(s16 x,s16 t,s16 b)
{
    u16 *data=DMA_allocateAndQueueDma(DMA_VRAM,VDP_BG_B+(x&63)*2,32,128);
    if(!data){sceneStreamFaults++;return;}
    memset(data,0,64);
    if(streamScene->streamOverlay) {
        u16 *overlay=DMA_allocateAndQueueDma(DMA_VRAM,VDP_BG_A+(x&63)*2,32,128);
        if(!overlay){sceneStreamFaults++;return;}
        memset(overlay,0,64);
    }
    const u16 *p=rowAt(t)+x;
    for(s16 y=t;y<=b;y++,p+=streamScene->cols)data[y&31]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,BASE+location[*p]);
}
static void writeRow(s16 y,s16 l,s16 r)
{
    u16 *data=DMA_allocateAndQueueDma(DMA_VRAM,VDP_BG_B+(y&31)*128,64,2);
    if(!data){sceneStreamFaults++;return;}
    memset(data,0,128);
    if(streamScene->streamOverlay) {
        u16 *overlay=DMA_allocateAndQueueDma(DMA_VRAM,VDP_BG_A+(y&31)*128,64,2);
        if(!overlay){sceneStreamFaults++;return;}
        memset(overlay,0,128);
    }
    for(s16 x=l;x<=r;x++)data[x&63]=attrAt(x,y);
}
static void warmAhead(void)
{
    if(!freeCount || left<0 || DMA_getQueueSize()+14>DMA_getMaxQueueSize() ||
       DMA_getQueueTransferSize()+1152>DMA_TRANSFER_CAPACITY_NTSC)return;
    const s16 col=warmDirection>0 ? right+1 : left-1;
    if(col<0 || col>=streamScene->cols)return;
    if(col!=warmCol){warmCol=col;warmRow=top;}
    u16 budget=freeCount<4?freeCount:4;
    const u16 *p=rowAt(warmRow)+col;
    // Use spare slots and spare frames to prepare the next column. Referenced
    // patterns are never evicted; the current map/scroll remain untouched.
    while(warmRow<=bottom && budget) {
        const u16 id=*p;warmRow++;p+=streamScene->cols;
        if(location[id]!=NONE)continue;
        enterCell(id,FALSE);releaseCell(id);budget--;
    }
}
static u16 differenceCells(s16 l,s16 r,s16 t,s16 b,s16 ol,s16 orr,s16 ot,s16 ob)
{
    const s16 il=l>ol?l:ol,ir=r<orr?r:orr,it=t>ot?t:ot,ib=b<ob?b:ob;
    return (r-l+1)*(b-t+1)-((il<=ir && it<=ib)?(ir-il+1)*(ib-it+1):0);
}
bool SCENESTREAM_move(s16 px,s16 py)
{
    sceneStreamUploads=0;
    if(!streamScene || !work)return FALSE;
    const s16 l=px>>3,r=(px+319)>>3,t=(py+HUD_HEIGHT)>>3,b=(py+223)>>3;
    if(lastPixelX>=0 && px!=lastPixelX)warmDirection=px>lastPixelX?1:-1;
    lastPixelX=px;
    if(l==left && r==right && t==top && b==bottom){warmAhead();return TRUE;}
    const bool initial=left<0;
    const u16 entering=initial ? (r-l+1)*(b-t+1) : differenceCells(l,r,t,b,left,right,top,bottom);
    if(!initial && (DMA_getQueueSize()+entering+10>DMA_getMaxQueueSize() || DMA_getQueueTransferSize()+entering*32+1024>DMA_TRANSFER_CAPACITY_NTSC))return FALSE;
    if(initial)cells(l,t,r-l+1,b-t+1,TRUE,TRUE);
    else {
        const s16 it=t>top?t:top,ib=b<bottom?b:bottom,ih=ib-it+1;
        // Only the entering/leaving strips are traversed. The camera moves
        // at most4px per frame, so the previous and next rectangles overlap.
        cells(left,top,right-left+1,t-top,FALSE,FALSE);
        cells(left,b+1,right-left+1,bottom-b,FALSE,FALSE);
        cells(left,it,l-left,ih,FALSE,FALSE);
        cells(r+1,it,right-r,ih,FALSE,FALSE);
        cells(l,t,r-l+1,top-t,TRUE,FALSE);
        cells(l,bottom+1,r-l+1,b-bottom,TRUE,FALSE);
        cells(l,it,left-l,ih,TRUE,FALSE);
        cells(right+1,it,r-right,ih,TRUE,FALSE);
    }
    // Batch each entering strip. Patterns, map and camera commit together in
    // VBlank; no per-cell VRAM port stalls during active display. Clear the
    // same BG_A strips before mission mechanisms repaint their visible edges.
    if(initial) {
        for(s16 y=t;y<=b;y++)for(s16 x=l;x<=r;x++)VDP_setTileMapXY(BG_B,attrAt(x,y),x&63,y&31);
    } else {
        for(s16 y=t;y<=b;y++)if(y<top || y>bottom)writeRow(y,l,r);
        for(s16 x=l;x<left && x<=r;x++)writeColumn(x,t,b);
        for(s16 x=right+1;x<=r;x++)if(x>=l)writeColumn(x,t,b);
    }
    left=l;right=r;top=t;bottom=b;
    if(CAP-freeCount>sceneStreamPeak)sceneStreamPeak=CAP-freeCount;
    if(!initial && !entering)warmAhead();
    return TRUE;
}
bool SCENESTREAM_heavyFrame(void)
{
    return streamScene && sceneStreamUploads>=3;
}
u16 SCENESTREAM_attr(s16 col,s16 row)
{
    if(!streamScene || !work || col<0 || col>=streamScene->cols || row<0 || row>=streamScene->rows)return 0;
    const u16 slot=location[streamScene->map[row*streamScene->cols+col]];
    return slot==NONE ? 0 : TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,BASE+slot);
}

bool SCENESTREAM_active(void)
{return streamScene!=NULL;}
