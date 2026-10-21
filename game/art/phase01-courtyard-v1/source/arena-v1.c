// Resident 64x32 world map: scrolling changes four VDP registers, not tiles.
#include "levels/arena.h"
#include "system/video/floor.h"
#include "actors/player.h"
#include "core/game.h"
#include "courtyard.h"
#include "levels/courtyard_data.h"

#define SCENE_BASE (TILE_USER_INDEX + FLOOR_TILE_BASE + FLOOR_TOTAL_TILES)
typedef char scene_vram_fits[(SCENE_BASE + COURTYARD_TILE_COUNT <= 1440) ? 1 : -1];

// Upper building line and side annex have ground footprints, not tall sprite boxes.
static const ArenaRect solids[] = {
    {16, 80, 184, 24}, {208, 80, 112, 16}, {432, 80, 64, 80},
    {16, 104, 24, 64},
    {16, 176, 176, 48}, {304, 200, 192, 24}
};
const ArenaDef COURTYARD_arena = {
    512, 256, 16, 80, 495, 223, 240, 136, solids, sizeof(solids)/sizeof(solids[0])
};
s16 arenaMinX=8, arenaMinY=16, arenaMaxX=311, arenaMaxY=215;
s16 cameraX, cameraY;
bool arenaActive;
u8 arenaDamaged;
static const ArenaDef *world;
// 8px occupancy cells, exact for this map's tile-aligned footprints. Each
// query intersects at most two 32-bit words per row instead of every prop.
static u32 collisionRows[32][2];

void ARENA_configure(const ArenaDef *def)
{
    if(!def)ARENA_leave();
    world=def; arenaActive=def!=NULL;
    if(def) {
        arenaMinX=def->minX;arenaMinY=def->minY;arenaMaxX=def->maxX;arenaMaxY=def->maxY;
        memset(collisionRows,0,sizeof collisionRows);
        for(u16 i=0;i<def->solidCount;i++) {
            const ArenaRect *r=&def->solids[i];
            for(u16 y=r->y/8;y<(r->y+r->h)/8;y++)
                for(u16 x=r->x/8;x<(r->x+r->w)/8;x++)
                    collisionRows[y][x>>5]|=0x80000000UL>>(x&31);
        }
    }
    else {arenaMinX=8;arenaMinY=16;arenaMaxX=311;arenaMaxY=215;}
}
void ARENA_leave(void)
{
    if(arenaActive) {VDP_loadDefaultFont(DMA);PAL_setColor(1,RGB24_TO_VDPCOLOR(0xF0F0F0));}
    arenaActive=FALSE;cameraX=cameraY=0;
    VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_setWindowOff();VDP_setTextPlane(BG_A);
}
VDPPlane ARENA_hudPlane(void) {return arenaActive ? WINDOW : BG_A;}
void ARENA_overlay(void) {if(arenaActive)VDP_setWindowFullScreen();}
void ARENA_gameView(void) {if(arenaActive)VDP_setWindowOnTop(1);}
s16 ARENA_startX(void) {return world ? world->startX : arenaMinX+(arenaMaxX-arenaMinX-15)/2;}
s16 ARENA_startY(void) {return world ? world->startY : arenaMinY+(arenaMaxY-arenaMinY-15)/2;}

bool ARENA_blocked(s16 x,s16 y,u16 w,u16 h)
{
    if(x<arenaMinX || y<arenaMinY || x+w-1>arenaMaxX || y+h-1>arenaMaxY)return TRUE;
    if(!world)return FALSE;
    u16 left=x>>3,right=(x+w-1)>>3;
    const u16 first=left>>5,last=right>>5;
    u32 a=0xFFFFFFFFUL>>(left&31),b=0xFFFFFFFFUL<<(31-(right&31));
    if(first==last)a&=b;
    for(u16 row=y>>3;row<=(y+h-1)>>3;row++)
        if((collisionRows[row][first]&a) || (first!=last && (collisionRows[row][last]&b)))return TRUE;
    return FALSE;
}
void ARENA_move(s32 *x,s32 *y,s16 dx,s16 dy,u16 size)
{
    s32 nx=*x+dx, ny=*y+dy;
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
    s16 x=px+8-160,y=py+8-112;
    s16 maxX=world->width>320 ? world->width-320 : 0;
    s16 maxY=world->height>224 ? world->height-224 : 0;
    if(x<0)x=0;
    if(x>maxX)x=maxX;
    if(y<0)y=0;
    if(y>maxY)y=maxY;
    cameraX=x;cameraY=y;
    VDP_setHorizontalScroll(BG_A,-x);VDP_setHorizontalScroll(BG_B,-x);
    VDP_setVerticalScroll(BG_A,y);VDP_setVerticalScroll(BG_B,y);
}
static void drawMap(bool damaged,bool patch)
{
    const u16 *map=(const u16 *)(damaged ? courtyard_damaged : courtyard_map);
    u16 row[64];
    const u16 width=patch ? 26 : 64,height=patch ? 15 : 32;
    for(u16 y=0;y<height;y++) {
        for(u16 x=0;x<width;x++)row[x]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,SCENE_BASE+map[y*64+x]);
        VDP_setTileMapDataRow(BG_B,row,y,0,width,CPU);
    }
}
void ARENA_draw(void)
{
    if(!arenaActive)return;
    VDP_setEnable(FALSE);
    VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(WINDOW,TRUE);
    VDP_loadFontData((const u32 *)courtyard_font,96,DMA);
    PAL_setColor(1,RGB24_TO_VDPCOLOR(0x242424));
    VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,FALSE,FALSE,FALSE,TILE_FONT_INDEX),0,0,40,1);
    VDP_loadTileData((const u32 *)courtyard_tiles,SCENE_BASE,COURTYARD_TILE_COUNT,DMA);
    PAL_setColors(PAL3*16,(const u16 *)courtyard_palette,16,DMA);
    drawMap(arenaDamaged,FALSE);
    VDP_setTextPlane(WINDOW);VDP_setWindowFullScreen();
    ARENA_camera();VDP_setEnable(TRUE);
}
void ARENA_damageChurch(void)
{
    if(!arenaActive || arenaDamaged)return;
    arenaDamaged=1;drawMap(TRUE,TRUE);
}
void ARENA_bright(u16 mix)
{
    const u16 *pal=(const u16 *)courtyard_palette;u16 out[16];
    for(u16 i=0;i<16;i++) {
        u16 c=pal[i],r=(c>>1)&7,g=(c>>5)&7,b=(c>>9)&7;
        r+=((7-r)*mix)>>4;g+=((7-g)*mix)>>4;b+=((7-b)*mix)>>4;
        out[i]=(r<<1)|(g<<5)|(b<<9);
    }
    PAL_setColors(PAL3*16,out,16,CPU);
}
