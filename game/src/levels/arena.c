// Per-stage worlds, 64x32 VDP ring. Only newly exposed rows are transferred.
#include "levels/arena.h"
#include "system/video/floor.h"
#include "system/video/projection.h"
#include "system/video/screens/hud.h"
#include "actors/player.h"
#include "core/game.h"
#include "courtyard.h"
#include "intro_data.h" // same opaque 96-glyph font, shared by opening and HUD
#include "levels/courtyard_data.h"

#define SCENE_BASE (TILE_USER_INDEX + FLOOR_TILE_BASE)
typedef char scene_vram_fits[(SCENE_BASE + COURTYARD_TILE_COUNT + HUD_OPAQUE_COUNT <= 1440) ? 1 : -1];

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
s16 arenaMinX=8, arenaMinY=16, arenaMaxX=311, arenaMaxY=215;
s16 cameraX, cameraY;
bool arenaActive;
u8 arenaDamaged;
static const ArenaDef *world;
static const ArenaScene *scene;
static u16 glowClock,glowCursor;
static u8 glowPhase;
static bool glowUploading;
static s16 residentTop=-1;
static u32 collisionRows[64][2], shotRows[64][2];
static bool hasShotSolids;
static void streamRow(u16 row,TransferMethod method,bool clearDecals);

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
        }
    } else {arenaMinX=8;arenaMinY=16;arenaMaxX=311;arenaMaxY=215;}
}
void ARENA_leave(void)
{
    if(arenaActive) {
        // The custom atlas borrows the legacy floor reservation. Clear its
        // map before restoring those tiles so no transitional garbage shows.
        VDP_clearPlane(BG_B,TRUE);
        VDP_loadDefaultFont(DMA);FLOOR_init();PAL_setColor(1,RGB24_TO_VDPCOLOR(0xF0F0F0));
    }
    arenaActive=FALSE;world=NULL;scene=NULL;cameraX=cameraY=0;residentTop=-1;
    glowClock=0;glowCursor=0;glowPhase=0;glowUploading=FALSE;
    VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_setWindowOff();VDP_setTextPlane(BG_A);VDP_setTextPriority(FALSE);
}
VDPPlane ARENA_hudPlane(void) {return arenaActive ? WINDOW : BG_A;}
void ARENA_overlay(void) {if(arenaActive)VDP_setWindowFullScreen();}
void ARENA_gameView(void) {if(arenaActive)VDP_setWindowOnTop(1);}
s16 ARENA_startX(void) {return world ? world->startX : arenaMinX+(arenaMaxX-arenaMinX-15)/2;}
s16 ARENA_startY(void) {return world ? world->startY : arenaMinY+(arenaMaxY-arenaMinY-15)/2;}
bool ARENA_npcInMap(void) {return arenaActive && scene && scene->npcInMap;}

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
static bool occupied(const u32 rows[64][2],s16 x,s16 y,u16 w,u16 h)
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
    s16 x=px+8-160,y=py+8-VIDEO_HEIGHT_OFFSET-112;
    const s16 maxX=world->width>320 ? world->width-320 : 0;
    const s16 maxY=world->height>224 ? world->height-224 : 0;
    if(x<0)x=0;
    if(x>maxX)x=maxX;
    if(y<0)y=0;
    if(y>maxY)y=maxY;
    cameraX=x;cameraY=y;
    const s16 top=y>>3;
    if(residentTop>=0 && top!=residentTop) {
        const s16 difference=top-residentTop;
        if(difference>4 || difference< -4) {
            VDP_setEnable(FALSE);
            for(u16 row=top;row<top+32;row++)streamRow(row,CPU,TRUE);
            VDP_setEnable(TRUE);
        } else if(top>residentTop) {
            for(s16 row=residentTop+32;row<top+32;row++)streamRow(row,DMA_QUEUE_COPY,TRUE);
        } else {
            for(s16 row=top;row<residentTop;row++)streamRow(row,DMA_QUEUE_COPY,TRUE);
        }
        residentTop=top;
    }
    VDP_setHorizontalScroll(BG_A,-x);VDP_setHorizontalScroll(BG_B,-x);
    VDP_setVerticalScroll(BG_A,y);VDP_setVerticalScroll(BG_B,y);
}
static void streamRow(u16 row,TransferMethod method,bool clearDecals)
{
    const u16 *map=arenaDamaged && scene->damaged ? scene->damaged : scene->map;
    u16 data[64];
    for(u16 x=0;x<64;x++)data[x]=row<scene->rows ?
        TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+map[row*64+x]) : 0;
    VDP_setTileMapDataRow(BG_B,data,row&31,0,64,method);
    if(clearDecals) {
        memset(data,0,sizeof data);
        VDP_setTileMapDataRow(BG_A,data,row&31,0,64,method);
    }
}
void ARENA_draw(void)
{
    if(!arenaActive)return;
    VDP_setEnable(FALSE);residentTop=-1;
    glowClock=0;glowCursor=0;glowPhase=0;glowUploading=FALSE;
    VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(WINDOW,TRUE);
    VDP_loadFontData((const u32 *)intro_font,96,DMA);
    PAL_setColor(1,0);VDP_setTextPriority(TRUE);
    VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_FONT_INDEX),0,0,40,1);
    VDP_loadTileData(scene->tiles,SCENE_BASE,scene->tileCount,DMA);
    HUD_loadOpaqueIcons();
    PAL_setColors(PAL3*16,scene->palette,16,DMA);
    ARENA_camera();residentTop=cameraY>>3;
    for(u16 row=residentTop;row<residentTop+32;row++)streamRow(row,CPU,FALSE);
    VDP_setTextPlane(WINDOW);VDP_setWindowFullScreen();VDP_setEnable(TRUE);
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
    PAL_setColors(PAL3*16,out,16,CPU);
}
