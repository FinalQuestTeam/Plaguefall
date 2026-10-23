#include "text_data.h"
#include "system/video/screens/loading.h"
// Per-stage worlds, 64x32 VDP ring. Only newly exposed rows/columns are transferred.
#include "levels/arena.h"
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

#define SCENE_BASE (TILE_USER_INDEX + FLOOR_TILE_BASE)
#define NPC_BAR_BASE (SCENE_BASE + COURTYARD_TILE_COUNT + HUD_OPAQUE_COUNT)
typedef char scene_vram_fits[(NPC_BAR_BASE + 4 <= 1440) ? 1 : -1];

// Low evacuation belongings: solid for feet, below the projectile plane.
// The church/walls are outside the playable bounds, not hidden floor boxes.
static const ArenaRect solids[] = {
    {48, 104, 72, 8, FALSE}, {272, 96, 56, 8, FALSE}
};
static const ArenaScene courtyardScene = {
    .tiles=(const u32 *)courtyard_tiles, .map=(const u16 *)courtyard_map,
    .damaged=(const u16 *)courtyard_damaged, .palette=(const u16 *)courtyard_palette,
    .tileCount=COURTYARD_TILE_COUNT, .rows=COURTYARD_MAP_ROWS
};
const ArenaDef COURTYARD_arena = {
    512, 384, 16, 112, 495, 367, 256, 160, solids, sizeof(solids)/sizeof(solids[0]), &courtyardScene
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
static u32 collisionRows[64][8], shotRows[64][8];
static bool hasShotSolids;
static bool npcVisible=TRUE;
static u16 npcBarHp=0xFFFF, npcBarMaximum;
static void streamRow(u16 row,TransferMethod method,bool clearDecals);
static void streamColumn(u16 col);
static u16 mapCols(void){return scene->cols ? scene->cols : 64;}

void ARENA_configure(const ArenaDef *def)
{
    if(!def)ARENA_leave();
    world=def;arenaActive=def!=NULL;
    scene=def ? (def->scene ? def->scene : &courtyardScene) : NULL;
    if(def) {
        arenaMinX=def->minX;arenaMinY=def->minY;arenaMaxX=def->maxX;arenaMaxY=def->maxY;
        memset(collisionRows,0,sizeof collisionRows);memset(shotRows,0,sizeof shotRows);
        hasShotSolids=FALSE;
        for(u16 i=0;i<def->solidCount;i++) {
            const ArenaRect *r=&def->solids[i];
            if(r->blocksShots)hasShotSolids=TRUE;
            for(u16 y=r->y/8;y<(r->y+r->h)/8;y++)
                for(u16 x=r->x/8;x<(r->x+r->w)/8;x++) {
                    const u32 bit=0x80000000UL>>(x&31);
                    collisionRows[y][x>>5]|=bit;
                    if(r->blocksShots)shotRows[y][x>>5]|=bit;
                }
            LOADING_poll();
        }
    } else {arenaMinX=8;arenaMinY=HUD_HEIGHT+32;arenaMaxX=311;arenaMaxY=215;}
}
void ARENA_leave(void)
{
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

u16 ARENA_npcBar(u16 hp,u16 maximum)
{
    if(hp!=npcBarHp || maximum!=npcBarMaximum) {
        if(DMA_getQueueTransferSize()+128+1024>DMA_TRANSFER_CAPACITY_NTSC ||
           DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return npcBarHp==0xFFFF ? 0 : NPC_BAR_BASE;
        const u16 fill=maximum ? (u32)hp*30/maximum : 0;
        u32 data[32]={0};
        for(u16 x=0;x<32;x++)for(u16 y=1;y<=5;y++) {
            const u16 color=(y==1 || y==5 || x==0 || x==31) ? 1 : x<=fill ? 4 : 11;
            data[(x/8)*8+y]|=(u32)color<<((7-(x&7))*4);
        }
        LOADING_tiles(data,NPC_BAR_BASE,4,DMA_QUEUE_COPY);
        npcBarHp=hp;npcBarMaximum=maximum;
    }
    return NPC_BAR_BASE;
}

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
    return x<arenaMinX || y<arenaMinY || x+w-1>arenaMaxX || y+h-1>arenaMaxY;
}
static bool occupied(const u32 rows[64][8],s16 x,s16 y,u16 w,u16 h)
{
    const u16 left=x>>3,right=(x+w-1)>>3,first=left>>5,last=right>>5;
    u32 a=0xFFFFFFFFUL>>(left&31),b=0xFFFFFFFFUL<<(31-(right&31));
    if(first==last)a&=b;
    for(u16 row=y>>3;row<=(y+h-1)>>3;row++)
        if((rows[row][first]&a) || (first!=last && (rows[row][last]&b)))return TRUE;
    return FALSE;
}
bool ARENA_blocked(s16 x,s16 y,u16 w,u16 h)
{
    return outside(x,y,w,h) || (world && occupied(collisionRows,x,y,w,h));
}
bool ARENA_shotBlocked(s16 x,s16 y)
{
    // Bullets are drawn 16px above ground. Wall tests use that visible plane.
    y-=VIDEO_HEIGHT_OFFSET;
    if(x<arenaMinX || x+7>arenaMaxX || y<arenaMinY-VIDEO_HEIGHT_OFFSET || y+7>arenaMaxY)return TRUE;
    return hasShotSolids && occupied(shotRows,x,y,8,8);
}
bool ARENA_playerShotBlocked(s16 x,s16 y)
{
    // The 8x8 bullet has a transparent one-pixel border. Test its visible 6x6
    // footprint, so padding cannot consume a shot alongside a wall.
    x++;y+=1-VIDEO_HEIGHT_OFFSET;
    if(x<arenaMinX || x+5>arenaMaxX || y<arenaMinY-VIDEO_HEIGHT_OFFSET || y+5>arenaMaxY)return TRUE;
    return hasShotSolids && occupied(shotRows,x,y,6,6);
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
    if(!world || !ARENA_blocked(nx>>6,*y>>6,size,size))*x=nx;
    if(!world || !ARENA_blocked(*x>>6,ny>>6,size,size))*y=ny;
}
void ARENA_camera(void)
{
    if(!arenaActive)return;
    const s16 oldX=cameraX,oldY=cameraY;
    s16 x=px+8-160,y=py+8-VIDEO_HEIGHT_OFFSET-(224+HUD_HEIGHT)/2;
    if(DINORAH_alive() && abs(px-dinorahX)<200 && abs(py-dinorahY)<120) {
        x=(px+dinorahX)/2+8-160;y=(py+dinorahY)/2+8-VIDEO_HEIGHT_OFFSET-(224+HUD_HEIGHT)/2;
    }
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
    cameraX=x;cameraY=y;
    const s16 top=y>>3,left=x>>3;
    if(residentTop>=0 && (top!=residentTop || left!=residentLeft)) {
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
        else memset(data,0,sizeof data);
        VDP_setTileMapDataRow(BG_A,data,row&31,0,64,method);
    }
}
static void streamColumn(u16 col)
{
    u16 data[32];const u16 cols=mapCols();
    const u16 *map=arenaDamaged && scene->damaged ? scene->damaged : scene->map;
    for(u16 y=residentTop;y<residentTop+32;y++)data[y&31]=(col<cols && y<scene->rows) ?
        TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+npcTile(col,y,map)) : 0;
    VDP_setTileMapDataColumnFast(BG_B,data,col&63,0,32,DMA_QUEUE_COPY);
    if(TERRAIN_active())for(u16 y=residentTop;y<residentTop+32;y++)data[y&31]=TERRAIN_attr(col,y);
    else memset(data,0,sizeof data);
    VDP_setTileMapDataColumnFast(BG_A,data,col&63,0,32,DMA_QUEUE_COPY);
}
void ARENA_draw(void)
{
    if(!arenaActive)return;
    const bool enabled=VDP_getEnable();
    LOADING_setEnable(FALSE);residentTop=-1;residentLeft=0;
    glowClock=0;glowCursor=0;glowPhase=0;glowUploading=FALSE;
    npcVisible=TRUE;npcBarHp=0xFFFF;
    VDP_clearPlane(BG_A,TRUE);if(!LOADING_active())VDP_clearPlane(WINDOW,TRUE);
    VDP_loadFontData((const u32 *)intro_font,96,DMA);
    LOADING_setColor(1,0);VDP_setTextPriority(TRUE);
    if(!LOADING_active())VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX),0,0,40,1);
    LOADING_tiles(scene->tiles,SCENE_BASE,scene->tileCount,DMA);
    HUD_loadOpaqueIcons();
    LOADING_setColors(PAL3*16,scene->palette,16,DMA);
    ARENA_camera();residentTop=cameraY>>3;residentLeft=cameraX>>3;
    for(u16 row=residentTop;row<residentTop+32;row++){streamRow(row,CPU,FALSE);LOADING_poll();}
    HUD_begin();LOADING_setEnable(enabled);
}
void ARENA_damageChurch(void)
{
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
