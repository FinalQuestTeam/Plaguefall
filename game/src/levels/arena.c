#include "text_data.h"
#include "system/video/screens/loading.h"
// Per-stage worlds, 64x32 VDP ring. Only newly exposed rows/columns are transferred.
#include "levels/arena.h"
#include "levels/operations.h"
#include "levels/graph.h"
#include "levels/campaign_route_ops.h"
#include "levels/campaign_launch.h"
#include "levels/campaign_resistance.h"
#include "system/video/floor.h"
#include "system/video/projection.h"
#include "system/video/screens/hud.h"
#include "actors/player.h"
#include "actors/dinorah.h"
#include "elements/terrain.h"
#include "core/game.h"
#include "courtyard.h"
#include "intro_data.h" // same opaque 96-glyph font, shared by opening and HUD
#include "levels/courtyard_data.h"
#include "system/video/scene_stream.h"

#define SCENE_BASE (TILE_USER_INDEX + FLOOR_TILE_BASE)
#define NPC_BAR_BASE (SCENE_BASE + COURTYARD_TILE_COUNT + HUD_OPAQUE_COUNT)
#define WORK_BAR_BASE (SCENE_BASE + COURTYARD_TILE_COUNT - ARENA_WORK_BAR_TILE_COUNT)
typedef char scene_vram_fits[(NPC_BAR_BASE + 4 <= 1440) ? 1 : -1];

// Low evacuation belongings: solid for feet, below the projectile plane.
// The church/walls are outside the playable bounds, not hidden floor boxes.
static const ArenaRect solids[] = {
    {88, 184, 72, 40, FALSE}, {136, 288, 72, 40, FALSE}, {392, 264, 40, 40, FALSE}
};
static const ArenaScene courtyardScene = {
    .tiles=(const u32 *)courtyard_tiles, .map=(const u16 *)courtyard_map,
    .damaged=(const u16 *)courtyard_damaged, .palette=(const u16 *)courtyard_palette,
    .tileCount=COURTYARD_TILE_COUNT, .rows=COURTYARD_MAP_ROWS
};
const ArenaDef COURTYARD_arena = {
    512, 384, 24, 128, 487, 351, 256, 160, solids, sizeof(solids)/sizeof(solids[0]), &courtyardScene
};
s16 arenaMinX=8, arenaMinY=HUD_HEIGHT+32, arenaMaxX=311, arenaMaxY=215;
s16 cameraX, cameraY;
bool arenaActive;
u8 arenaDamaged;
static const ArenaDef *world;
static const ArenaScene *scene;
static u16 glowClock,glowCursor;
static u8 glowPhase;
static bool glowUploading;
static s16 residentTop=-1,residentLeft;
static bool cameraTargetValid,cameraFollowNpc;
static s16 cameraPlayerX,cameraPlayerY,cameraNpcX,cameraNpcY,cameraTargetX,cameraTargetY;
// Sized for the largest authored world: 3072x320 = 480 words per mask.
// A dynamic row stride retains the original4KB RAM budget for both masks.
#define COLLISION_WORDS 512
static u32 collisionRows[COLLISION_WORDS],shotRows[COLLISION_WORDS];
static u16 collisionStride;
static bool hasShotSolids;
static s16 solidLeft,solidTop,solidRight,solidBottom;
static s16 shotLeft,shotTop,shotRight,shotBottom;
static const u16 emptyMapLine[64]={0};
static bool npcVisible=TRUE;
static u16 npcBarHp=0xFFFF, npcBarMaximum;
static u16 workBarValue=0xFFFF,workBarMaximum;
static void streamRow(u16 row,TransferMethod method,bool clearDecals);
static void streamColumn(u16 col);
static u16 mapCols(void){return scene->cols ? scene->cols : 64;}

void ARENA_configure(const ArenaDef *def)
{
    cameraTargetValid=FALSE;
    if(!def)ARENA_leave();
    world=def;arenaActive=def!=NULL;
    scene=def ? (def->scene ? def->scene : &courtyardScene) : NULL;
    if(def) {
        arenaMinX=def->minX;arenaMinY=def->minY;arenaMaxX=def->maxX;arenaMaxY=def->maxY;
        collisionStride=(def->width+255)/256;
        memset(collisionRows,0,sizeof collisionRows);memset(shotRows,0,sizeof shotRows);
        hasShotSolids=FALSE;
        solidLeft=solidTop=32767;solidRight=solidBottom=-32768;
        shotLeft=shotTop=32767;shotRight=shotBottom=-32768;
        for(u16 i=0;i<def->solidCount;i++) {
            const ArenaRect *r=&def->solids[i];
            const s16 l=(r->x/8)*8,t=(r->y/8)*8,rr=((r->x+r->w)/8)*8,bb=((r->y+r->h)/8)*8;
            if(r->blocksShots) {
                hasShotSolids=TRUE;
                if(l<shotLeft)shotLeft=l;
                if(t<shotTop)shotTop=t;
                if(rr>shotRight)shotRight=rr;
                if(bb>shotBottom)shotBottom=bb;
            }
            if(rr>l && bb>t) {
                if(l<solidLeft)solidLeft=l;if(t<solidTop)solidTop=t;
                if(rr>solidRight)solidRight=rr;if(bb>solidBottom)solidBottom=bb;
            }
            for(u16 y=r->y/8;y<(r->y+r->h)/8 && y<64 && (y+1)*collisionStride<=COLLISION_WORDS;y++)
                for(u16 x=r->x/8;x<(r->x+r->w)/8 && x<512;x++) {
                    const u32 bit=0x80000000UL>>(x&31);
                    collisionRows[y*collisionStride+(x>>5)]|=bit;
                    if(r->blocksShots)shotRows[y*collisionStride+(x>>5)]|=bit;
                }
            LOADING_poll();
        }
    } else {arenaMinX=8;arenaMinY=HUD_HEIGHT+32;arenaMaxX=311;arenaMaxY=215;}
}
void ARENA_leave(void)
{
    SCENESTREAM_end();
    cameraTargetValid=FALSE;
    TERRAIN_clear();
    if(arenaActive) {
        // The custom atlas borrows the legacy floor reservation. Clear its
        // map before restoring those tiles so no transitional garbage shows.
        VDP_clearPlane(BG_B,TRUE);
        LOADING_tiles((const u32 *)text_font,TILE_FONT_INDEX,FONT_LENGTH,DMA);LOADING_setColor(1,RGB24_TO_VDPCOLOR(0xF0F0F0));
    }
    arenaActive=FALSE;world=NULL;scene=NULL;cameraX=cameraY=0;residentTop=-1;residentLeft=0;
    glowClock=0;glowCursor=0;glowPhase=0;glowUploading=FALSE;
    VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    LOADING_windowOff();VDP_setTextPlane(BG_A);VDP_setTextPriority(FALSE);
}
VDPPlane ARENA_hudPlane(void) {return WINDOW;}
const u16 *ARENA_scenePalette(void){return scene ? scene->palette : NULL;}
void ARENA_overlay(void) {if(arenaActive)VDP_setWindowFullScreen();}
void ARENA_gameView(void) {if(!LOADING_active())VDP_setWindowOnTop(HUD_ROWS);}
s16 ARENA_startX(void) {return world ? world->startX : arenaMinX+(arenaMaxX-arenaMinX-15)/2;}
s16 ARENA_startY(void) {return world ? world->startY : arenaMinY+(arenaMaxY-arenaMinY-15)/2;}
bool ARENA_npcInMap(void) {return arenaActive && scene && scene->npcInMap;}
const ArenaNpcVisual *ARENA_npcVisual(void) {return ARENA_npcInMap() ? scene->npcVisual : NULL;}

static u16 npcTile(u16 col,u16 row,const u16 *map)
{
    const ArenaNpcVisual *v=scene->npcVisual;
    if(!npcVisible && v && col>=v->col && col<v->col+v->cols && row>=v->row && row<v->row+v->rows)
        return v->floor[(row-v->row)*v->cols+col-v->col];
    return map[row*mapCols()+col];
}

u16 ARENA_sceneTileCount(void){return scene ? scene->tileCount : 0;}
u16 ARENA_backgroundAttr(s16 col,s16 row)
{
    if(!scene || col<0 || row<0 || col>=mapCols() || row>=scene->rows)return 0;
    if(scene->stream)return SCENESTREAM_attr(col,row);
    const u16 *map=arenaDamaged && scene->damaged ? scene->damaged : scene->map;
    return TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+npcTile(col,row,map));
}

void ARENA_showNpc(bool visible)
{
    if(!ARENA_npcInMap() || !scene->npcVisual || npcVisible==visible)return;
    const ArenaNpcVisual *v=scene->npcVisual;
    // Each row is only five cells. Copy stack data into the DMA queue; do not
    // change the visual state unless the complete update fits this frame.
    if(DMA_getQueueTransferSize()+v->cols*v->rows*2+1024>DMA_TRANSFER_CAPACITY_NTSC ||
       DMA_getQueueSize()+v->rows+3>=DMA_getMaxQueueSize())return;
    npcVisible=visible;
    for(u16 row=v->row;row<v->row+v->rows;row++) {
        if(row<residentTop || row>=residentTop+32)continue;
        u16 data[5];
        for(u16 x=0;x<v->cols;x++)data[x]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,
            SCENE_BASE+npcTile(v->col+x,row,scene->map));
        VDP_setTileMapDataRow(BG_B,data,row&31,v->col,v->cols,DMA_QUEUE_COPY);
    }
}

static u16 drawBar(u16 value,u16 maximum,u16 base,u16 *previous,u16 *previousMaximum)
{
    if(value!=*previous || maximum!=*previousMaximum) {
        if(DMA_getQueueTransferSize()+128+1024>DMA_TRANSFER_CAPACITY_NTSC ||
           DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return *previous==0xFFFF ? 0 : base;
        const u16 fill=maximum ? (u32)value*30/maximum : 0;
        u32 data[32]={0};
        for(u16 x=0;x<32;x++)for(u16 y=1;y<=5;y++) {
            const u16 color=(y==1 || y==5 || x==0 || x==31) ? 1 : x<=fill ? 4 : 11;
            data[(x/8)*8+y]|=(u32)color<<((7-(x&7))*4);
        }
        LOADING_tiles(data,base,4,DMA_QUEUE_COPY);
        *previous=value;*previousMaximum=maximum;
    }
    return base;
}
u16 ARENA_npcBar(u16 hp,u16 maximum)
{return drawBar(hp,maximum,NPC_BAR_BASE,&npcBarHp,&npcBarMaximum);}
u16 ARENA_workBar(u16 value,u16 maximum)
{return drawBar(value,maximum,WORK_BAR_BASE,&workBarValue,&workBarMaximum);}

void ARENA_update(void)
{
    if(!arenaActive || !scene->glow || !scene->glowCount)return;
    // Slow, material-only shimmer. Never modify PAL0 (font/hit flashes), PAL1
    // (objects), PAL2 (Damião) or the shared scenery palette.
    if(++glowClock>=fps) {
        glowClock=0;glowPhase=(glowPhase+1)&3;glowCursor=0;glowUploading=TRUE;
    }
    if(!glowUploading)return;
    u16 count=scene->glowCount-glowCursor;
    if(count>4)count=4;
    const u16 bytes=count*32;
    if(DMA_getQueueTransferSize()+bytes+1024>DMA_TRANSFER_CAPACITY_NTSC ||
       DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return;
    const u8 phase=glowPhase==3 ? 1 : glowPhase;
    const u32 *source=phase ? scene->glow+(phase-1)*scene->glowCount*8 : scene->tiles+scene->glowStart*8;
    source+=glowCursor*8;
    if(!DMA_queueDma(DMA_VRAM,(void *)source,(SCENE_BASE+scene->glowStart+glowCursor)*32,count*16,2))return;
    glowCursor+=count;
    if(glowCursor==scene->glowCount)glowUploading=FALSE;
}
static bool outside(s16 x,s16 y,u16 w,u16 h)
{
    return (u16)(x-arenaMinX)>(u16)(arenaMaxX-arenaMinX-w+1) || (u16)(y-arenaMinY)>(u16)(arenaMaxY-arenaMinY-h+1);
}
// Exact cell masks avoid two variable 32-bit shifts per collision query.
static const u32 occupiedLeft[32]={0xffffffffUL,0x7fffffffUL,0x3fffffffUL,0x1fffffffUL,0x0fffffffUL,0x07ffffffUL,0x03ffffffUL,0x01ffffffUL,0x00ffffffUL,0x007fffffUL,0x003fffffUL,0x001fffffUL,0x000fffffUL,0x0007ffffUL,0x0003ffffUL,0x0001ffffUL,0x0000ffffUL,0x00007fffUL,0x00003fffUL,0x00001fffUL,0x00000fffUL,0x000007ffUL,0x000003ffUL,0x000001ffUL,0x000000ffUL,0x0000007fUL,0x0000003fUL,0x0000001fUL,0x0000000fUL,0x00000007UL,0x00000003UL,0x00000001UL};
static const u32 occupiedRight[32]={0x80000000UL,0xc0000000UL,0xe0000000UL,0xf0000000UL,0xf8000000UL,0xfc000000UL,0xfe000000UL,0xff000000UL,0xff800000UL,0xffc00000UL,0xffe00000UL,0xfff00000UL,0xfff80000UL,0xfffc0000UL,0xfffe0000UL,0xffff0000UL,0xffff8000UL,0xffffc000UL,0xffffe000UL,0xfffff000UL,0xfffff800UL,0xfffffc00UL,0xfffffe00UL,0xffffff00UL,0xffffff80UL,0xffffffc0UL,0xffffffe0UL,0xfffffff0UL,0xfffffff8UL,0xfffffffcUL,0xfffffffeUL,0xffffffffUL};
static bool occupied(const u32 *rows,s16 x,s16 y,u16 w,u16 h)
{
    const u16 left=x>>3,right=(x+w-1)>>3,first=left>>5,last=right>>5;
    u32 a=occupiedLeft[left&31];const u32 b=occupiedRight[right&31];
    const u16 count=((y+h-1)>>3)-(y>>3)+1;
    // Collision masks have at most512 words, so a16-bit offset is exact.
    const u32 *line=rows+(u16)((y>>3)*collisionStride)+first;
    if(first==last) {
        a&=b;
        for(u16 row=0;row<count;row++,line+=collisionStride)if(*line&a)return TRUE;
    } else {
        const u16 delta=last-first;
        for(u16 row=0;row<count;row++,line+=collisionStride)if((*line&a) || (line[delta]&b))return TRUE;
    }
    return FALSE;
}
bool ARENA_blocked(s16 x,s16 y,u16 w,u16 h)
{
    if(outside(x,y,w,h))return TRUE;
    if(CR_OPS_blocked(x,y,w,h))return TRUE;
    if(CAMPAIGN_RESISTANCE_blocked(x,y,w,h))return TRUE;
    if(!currentLevel && testStage>=OPS_FIRST_ROOM && OPS_blocked(x,y,w,h))return TRUE;
    if(!world || x>=solidRight || x+(s16)w<=solidLeft || y>=solidBottom || y+(s16)h<=solidTop)return FALSE;
    return occupied(collisionRows,x,y,w,h);
}
bool ARENA_shotBlocked(s16 x,s16 y)
{
    // Bullets are drawn 16px above ground. Wall tests use that visible plane.
    y-=VIDEO_HEIGHT_OFFSET;
    if(CR_OPS_shotBlocked(x,y,FALSE))return TRUE;
    if(!currentLevel && testStage>=OPS_FIRST_ROOM && OPS_shotBlocked(x,y,FALSE))return TRUE;
    if((u16)(x-arenaMinX)>(u16)(arenaMaxX-arenaMinX-7) ||
       (u16)(y-arenaMinY+VIDEO_HEIGHT_OFFSET)>(u16)(arenaMaxY-arenaMinY+VIDEO_HEIGHT_OFFSET-7))return TRUE;
    return hasShotSolids && x<shotRight && x+8>shotLeft && y<shotBottom && y+8>shotTop && occupied(shotRows,x,y,8,8);
}
bool ARENA_playerShotBlocked(s16 x,s16 y)
{
    // The 8x8 bullet has a transparent one-pixel border. Test its visible 6x6
    // footprint, so padding cannot consume a shot alongside a wall.
    x++;y+=1-VIDEO_HEIGHT_OFFSET;
    if(CR_OPS_shotBlocked(x,y,TRUE))return TRUE;
    if(!currentLevel && testStage>=OPS_FIRST_ROOM && OPS_shotBlocked(x,y,TRUE))return TRUE;
    if((u16)(x-arenaMinX)>(u16)(arenaMaxX-arenaMinX-5) ||
       (u16)(y-arenaMinY+VIDEO_HEIGHT_OFFSET)>(u16)(arenaMaxY-arenaMinY+VIDEO_HEIGHT_OFFSET-5))return TRUE;
    return hasShotSolids && x<shotRight && x+6>shotLeft && y<shotBottom && y+6>shotTop && occupied(shotRows,x,y,6,6);
}
void ARENA_move(s32 *x,s32 *y,s16 dx,s16 dy,u16 size)
{
    s32 nx=*x+dx,ny=*y+dy;
    const s32 lx=(s32)arenaMinX*64,rx=(s32)(arenaMaxX-size+1)*64;
    const s32 ly=(s32)arenaMinY*64,ry=(s32)(arenaMaxY-size+1)*64;
    if(nx<lx)nx=lx;
    if(nx>rx)nx=rx;
    if(ny<ly)ny=ly;
    if(ny>ry)ny=ry;
    // Both axis sweeps are provably clear south of the solid tile bounds.
    // nx/ny were clamped above; the horizontal sweep also needs its old Y
    // inside the arena, including calls that start at an invalid coordinate.
    const s16 oldY=*y>>6,clearY=solidBottom>arenaMinY?solidBottom:arenaMinY;
    if(!CR_OPS_active() && currentLevel!=N_7 && (currentLevel || testStage<OPS_FIRST_ROOM) && world && oldY>=clearY && oldY<=arenaMaxY-(s16)size+1 && (ny>>6)>=solidBottom) {
        *x=nx;*y=ny;return;
    }
    if((nx>>6)==(*x>>6) || !world || !ARENA_blocked(nx>>6,*y>>6,size,size))*x=nx;
    if((ny>>6)==(*y>>6) || !world || !ARENA_blocked(*x>>6,ny>>6,size,size))*y=ny;
}
void ARENA_camera(void)
{
    if(!arenaActive)return;
    const s16 oldX=cameraX,oldY=cameraY;
    const bool followNpc=DINORAH_alive() && abs(px-dinorahX)<200 && abs(py-dinorahY)<120;
    s16 x,y;
    if(cameraTargetValid && cameraPlayerX==px && cameraPlayerY==py && cameraFollowNpc==followNpc &&
       (!followNpc || (cameraNpcX==dinorahX && cameraNpcY==dinorahY))) {
        x=cameraTargetX;y=cameraTargetY;
    } else {
    x=px+8-160;y=py+8-VIDEO_HEIGHT_OFFSET-(224+HUD_HEIGHT)/2;
    if(followNpc) {
        x=(px+dinorahX)/2+8-160;y=(py+dinorahY)/2+8-VIDEO_HEIGHT_OFFSET-(224+HUD_HEIGHT)/2;
    }
    if(scene->cameraPlayerY) {
        const s16 anchor=scene->cameraPlayerY;
        y=py-anchor;
        if(followNpc)
            y=(py+dinorahY)/2-anchor;
        // A close, complete landmark supplies vertical context. Northern
        // facades need roof headroom; southern docks need their full footing.
        // Streaming still interpolates at4px/frame, so changing rooms cannot
        // jump or reload the picture.
        const ArenaRect *focus=NULL;
        s16 nearest=65;
        for(u8 i=0;i<scene->cameraFocusCount;i++) {
            const ArenaRect *r=&scene->cameraFocus[i];
            const s16 cx=px+8,cy=py+8;
            const s16 dx=cx<r->x ? r->x-cx : (cx>r->x+r->w ? cx-r->x-r->w : 0);
            if(dx>=nearest)continue;
            const s16 dy=cy<r->y ? r->y-cy : (cy>r->y+r->h ? cy-r->y-r->h : 0);
            if(dx+dy<nearest){nearest=dx+dy;focus=r;}
        }
        if(focus) {
            const s16 low=focus->y+focus->h-224,high=focus->y-HUD_HEIGHT;
            if(low<=high){if(y<low)y=low;if(y>high)y=high;}
            const s16 left=focus->x+focus->w-320,right=focus->x;
            if(left<=right){if(x<left)x=left;if(x>right)x=right;}
        }
        // Both actors stay inside the picture while the camera gives the
        // approach to tall corridor buildings enough space above the HUD.
        const s16 minimum=py+8-224;
        if(y<minimum)y=minimum;
        const s16 maximum=py-HUD_HEIGHT-VIDEO_HEIGHT_OFFSET-31;
        if(y>maximum)y=maximum;
        if(x<px+24-320)x=px+24-320;
        if(x>px-8)x=px-8;
        if(followNpc) {
            const s16 escortMinimum=dinorahY+8-224;
            if(y<escortMinimum)y=escortMinimum;
            const s16 escortMaximum=dinorahY-HUD_HEIGHT-VIDEO_HEIGHT_OFFSET-31;
            if(y>escortMaximum)y=escortMaximum;
            if(x<dinorahX+24-320)x=dinorahX+24-320;
            if(x>dinorahX-8)x=dinorahX-8;
        }
    }
    if(scene->cameraSouthStart && py>(s16)scene->cameraSouthStart && world->height>224) {
        // Frame decorative scenery beyond the walkable boundary as the
        // player approaches it. Landmark headroom must not hide this edge.
        const s16 span=arenaMaxY-15-scene->cameraSouthStart;
        if(span>0) {
            const s16 south=divu(mulu(py-scene->cameraSouthStart,world->height-224),span);
            if(y<south)y=south;
        }
    }
    cameraPlayerX=px;cameraPlayerY=py;cameraFollowNpc=followNpc;
    cameraNpcX=dinorahX;cameraNpcY=dinorahY;cameraTargetX=x;cameraTargetY=y;cameraTargetValid=TRUE;
    }
    CL_camera(&x,&y);
    const s16 maxX=world->width>320 ? world->width-320 : 0;
    s16 maxY=world->height>224 ? world->height-224 : 0;
    // This defense arena fits the player feet and the objective marker in
    // one view. Keep the Santa below the fixed HUD even at the south wall.
    if(scene->npcVisual) {
        s16 focusMax=scene->npcVisual->focusTop-HUD_HEIGHT-8;
        // Prefer headroom for the Santa, but never strand Damião below the
        // viewport at the south wall. Far away, her HUD readout stays visible.
        const s16 playerMinimum=py+20-224;
        if(focusMax<playerMinimum)focusMax=playerMinimum;
        // Expanded defense fields may frame the whole southern perimeter.
        // Near the objective retain its headroom; further south follow the
        // same boundary framing used by the street, with its HUD readout.
        if(scene->cameraSouthStart && py>(s16)scene->cameraSouthStart) {
            const s16 span=arenaMaxY-15-scene->cameraSouthStart;
            if(span>0) {
                const s16 south=divu(mulu(py-scene->cameraSouthStart,maxY),span);
                if(focusMax<south)focusMax=south;
            }
        }
        if(focusMax>=0 && maxY>focusMax)maxY=focusMax;
    }
    if(x<0)x=0;
    if(x>maxX)x=maxX;
    if(y<0)y=0;
    if(y>maxY)y=maxY;
    // Keep the streaming window continuous when escort focus changes or an
    // actor falls. At most one new tile per axis; no blank-screen reload.
    if(residentTop>=0) {
        if(x>cameraX+4)x=cameraX+4;else if(x<cameraX-4)x=cameraX-4;
        if(y>cameraY+4)y=cameraY+4;else if(y<cameraY-4)y=cameraY-4;
    }
    if(scene->stream && !SCENESTREAM_move(x,y))return;
    cameraX=x;cameraY=y;
    const s16 top=y>>3,left=x>>3;
    if(!scene->stream && residentTop>=0 && (top!=residentTop || left!=residentLeft)) {
        const s16 dy=top-residentTop,dx=left-residentLeft;
        if(dy>4 || dy< -4 || dx>4 || dx< -4) {
            LOADING_setEnable(FALSE);residentTop=top;residentLeft=left;
            for(u16 row=top;row<top+32;row++)streamRow(row,CPU,TRUE);
            LOADING_setEnable(TRUE);
        } else {
            // Rows use the NEW horizontal window; columns then fill the
            // overlap at the new vertical window. Every physical ring cell
            // is indexed by world tile modulo the VDP dimensions.
            const s16 oldLeft=residentLeft;residentLeft=left;
            if(top>residentTop)for(s16 r=residentTop+32;r<top+32;r++)streamRow(r,DMA_QUEUE_COPY,TRUE);
            else for(s16 r=top;r<residentTop;r++)streamRow(r,DMA_QUEUE_COPY,TRUE);
            residentTop=top;
            if(left>oldLeft)for(s16 c=oldLeft+64;c<left+64;c++)streamColumn(c);
            else for(s16 c=left;c<oldLeft;c++)streamColumn(c);
        }
    }
    if(residentTop<0) {
        // Initial drawing runs with the display disabled, before its first DMA.
        VDP_setHorizontalScroll(BG_A,-x);VDP_setHorizontalScroll(BG_B,-x);
        VDP_setVerticalScroll(BG_A,y);VDP_setVerticalScroll(BG_B,y);
    } else {
        // Commit scroll after the queued row/column DMA in the SAME VBlank.
        // Immediate writes expose stale ring cells when a slow frame moves
        // left/up before its newly exposed cells have reached VRAM.
        if(x!=oldX) {
            VDP_setHorizontalScrollVSync(BG_A,-x);VDP_setHorizontalScrollVSync(BG_B,-x);
        }
        if(y!=oldY) {
            VDP_setVerticalScrollVSync(BG_A,y);VDP_setVerticalScrollVSync(BG_B,y);
        }
    }
    if(scene->stream){residentTop=top;residentLeft=left;}
}
static void streamRow(u16 row,TransferMethod method,bool clearDecals)
{
    const u16 *map=arenaDamaged && scene->damaged ? scene->damaged : scene->map;
    u16 data[64];
    const u16 cols=mapCols();
    for(u16 x=residentLeft;x<residentLeft+64;x++)data[x&63]=(row<scene->rows && x<cols) ?
        TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+map[row*cols+x]) : 0;
    const ArenaNpcVisual *v=scene->npcVisual;
    if(!npcVisible && v && row>=v->row && row<v->row+v->rows)
        for(u16 x=0;x<v->cols;x++)data[v->col+x]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,
            SCENE_BASE+v->floor[(row-v->row)*v->cols+x]);
    VDP_setTileMapDataRow(BG_B,data,row&31,0,64,method);
    if(clearDecals || TERRAIN_active()) {
        if(TERRAIN_active())for(u16 x=residentLeft;x<residentLeft+64;x++) {
            data[x&63]=TERRAIN_attr(x,row);
            if((x&7)==0)LOADING_poll();
        }
        VDP_setTileMapDataRow(BG_A,TERRAIN_active() ? data : emptyMapLine,row&31,0,64,method);
    }
}
static void streamColumn(u16 col)
{
    u16 data[32];const u16 cols=mapCols();
    const u16 *map=arenaDamaged && scene->damaged ? scene->damaged : scene->map;
    // Step through the ROM column directly. Its stride and the visibility
    // test are invariant; there is no per-cell mapCols/multiply/NPC lookup.
    memset(data,0,sizeof data);
    if(col<cols && residentTop<scene->rows) {
        u16 count=scene->rows-residentTop;if(count>32)count=32;
        const u16 *source=map+residentTop*cols+col;
        const u16 ring=residentTop&31;
        u16 first=32-ring;if(first>count)first=count;
        u16 *target=data+ring;
        for(u16 i=0;i<first;i++,source+=cols)
            *target++=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+*source);
        target=data;
        for(u16 i=first;i<count;i++,source+=cols)
            *target++=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+*source);
        const ArenaNpcVisual *v=scene->npcVisual;
        if(!npcVisible && v && col>=v->col && col<v->col+v->cols) {
            u16 top=residentTop>v->row ? residentTop : v->row;
            u16 bottom=residentTop+count;if(bottom>v->row+v->rows)bottom=v->row+v->rows;
            for(u16 y=top;y<bottom;y++)
                data[y&31]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+v->floor[(y-v->row)*v->cols+col-v->col]);
        }
    }
    VDP_setTileMapDataColumnFast(BG_B,data,col&63,0,32,DMA_QUEUE_COPY);
    if(TERRAIN_active())for(u16 y=residentTop;y<residentTop+32;y++)data[y&31]=TERRAIN_attr(col,y);
    VDP_setTileMapDataColumnFast(BG_A,TERRAIN_active() ? data : emptyMapLine,col&63,0,32,DMA_QUEUE_COPY);
}
void ARENA_draw(void)
{
    if(!arenaActive)return;
    const bool enabled=VDP_getEnable();
    LOADING_setEnable(FALSE);residentTop=-1;residentLeft=0;
    glowClock=0;glowCursor=0;glowPhase=0;glowUploading=FALSE;
    npcVisible=TRUE;npcBarHp=workBarValue=0xFFFF;
    VDP_clearPlane(BG_A,TRUE);if(!LOADING_active())VDP_clearPlane(WINDOW,TRUE);
    VDP_loadFontData((const u32 *)intro_font,96,DMA);
    LOADING_setColor(1,0);VDP_setTextPriority(TRUE);
    if(!LOADING_active())VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX),0,0,40,1);
    if(scene->stream) {
        if(!SCENESTREAM_begin(scene)){LOADING_setEnable(enabled);return;}
    } else LOADING_tiles(scene->tiles,SCENE_BASE,scene->tileCount,DMA);
    HUD_loadOpaqueIcons();
    LOADING_setColors(PAL3*16,scene->palette,16,DMA);
    ARENA_camera();residentTop=cameraY>>3;residentLeft=cameraX>>3;
    if(!scene->stream)for(u16 row=residentTop;row<residentTop+32;row++){streamRow(row,CPU,FALSE);LOADING_poll();}
    HUD_begin();LOADING_setEnable(enabled);
}
void ARENA_damageChurch(void)
{
    if(currentLevel && currentLevel!=N_1)return;
    if(!arenaActive || !scene->damaged || scene->damaged==scene->map || arenaDamaged)return;
    arenaDamaged=1;
    const u16 *map=scene->damaged;
    u16 data[COURTYARD_DAMAGE_COLS];
    for(u16 row=0;row<COURTYARD_DAMAGE_ROWS;row++) {
        if(row<residentTop || row>=residentTop+32)continue;
        for(u16 x=0;x<COURTYARD_DAMAGE_COLS;x++)data[x]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+map[row*64+x]);
        VDP_setTileMapDataRow(BG_B,data,row&31,0,COURTYARD_DAMAGE_COLS,CPU);
    }
}
void ARENA_bright(u16 mix)
{
    if(!scene)return;
    const u16 *pal=scene->palette;u16 out[16];
    for(u16 i=0;i<16;i++) {
        u16 c=pal[i],r=(c>>1)&7,g=(c>>5)&7,b=(c>>9)&7;
        r+=((7-r)*mix)>>4;g+=((7-g)*mix)>>4;b+=((7-b)*mix)>>4;
        out[i]=(r<<1)|(g<<5)|(b<<9);
    }
    LOADING_setColors(PAL3*16,out,16,CPU);
}
