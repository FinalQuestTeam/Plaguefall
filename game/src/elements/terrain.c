// Portable connected lava/mud. All geometry comes from the gameplay TileRects.
#include "elements/terrain.h"
#include "elements/terrain_art.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

// HUD owns icon tiles 0..119, navigation starts at 180. Countdown lives in
// the enemy frame cache, so terrain has no lifetime conflict with 3/2/1.
typedef char terrain_fits_before_markers[(120+TERRAIN_TILE_COUNT<=180)?1:-1];
typedef char terrain_count_matches_art[(TERRAIN_TILE_COUNT==TERRAIN_VARIANTS*2)?1:-1];
static const TileRect *lavaRects,*mudRects;
static u16 lavaCount,mudCount,animTicks;
static u8 lavaFrame;
static u8 palettePairs[256];
static u16 paletteBank;
static u32 terrainPixels[TERRAIN_VARIANTS*8];

void TERRAIN_clear(void)
{
    lavaRects=mudRects=NULL;lavaCount=mudCount=animTicks=0;lavaFrame=0;
}
bool TERRAIN_active(void){return lavaCount || mudCount;}
static void adaptPalette(const u16 *palette)
{
    u8 colors[16];colors[0]=0;paletteBank=palette ? PAL3 : PAL1;
    for(u16 i=1;i<16;i++) {
        if(!palette){colors[i]=TERRAIN_DEFAULT_MAP[i];continue;}
        const u16 source=TERRAIN_SOURCE_PALETTE[i];u16 best=0xFFFF;colors[i]=1;
        for(u16 j=1;j<16;j++) {
            const u16 target=palette[j];
            const s16 r=((source>>1)&7)-((target>>1)&7);
            const s16 g=((source>>5)&7)-((target>>5)&7);
            const s16 b=((source>>9)&7)-((target>>9)&7);
            const u16 distance=r*r+2*g*g+b*b;
            if(distance<best){best=distance;colors[i]=j;}
        }
    }
    for(u16 i=0;i<256;i++)palettePairs[i]=(colors[i>>4]<<4)|colors[i&15];
}
static void adaptPixels(const u32 *source)
{
    // One bounded buffer survives queued DMA. Pair lookup keeps the subtle
    // lava shimmer inexpensive; no palette writes or per-pixel RGB work.
    for(u16 i=0;i<TERRAIN_VARIANTS*8;i++) {
        const u32 v=source[i];
        terrainPixels[i]=((u32)palettePairs[v>>24]<<24)|((u32)palettePairs[(v>>16)&255]<<16)|
            ((u32)palettePairs[(v>>8)&255]<<8)|palettePairs[v&255];
    }
}
void TERRAIN_start(const TileRect *lava,u16 lc,const TileRect *mud,u16 mc,const u16 *palette)
{
    TERRAIN_clear();lavaRects=lava;mudRects=mud;lavaCount=lc;mudCount=mc;
    if(!TERRAIN_active())return;
    adaptPalette(palette);
    adaptPixels(TERRAIN_LAVA_ART);
    VDP_loadTileData(terrainPixels,TERRAIN_TILE_BASE,TERRAIN_VARIANTS,DMA);
    adaptPixels(TERRAIN_MUD_ART);
    VDP_loadTileData(terrainPixels,TERRAIN_TILE_BASE+TERRAIN_VARIANTS,TERRAIN_VARIANTS,DMA);
}
static bool contains(const TileRect *rects,u16 count,s16 x,s16 y)
{
    if(x<0 || y<0)return FALSE;
    for(u16 i=0;i<count;i++) {
        const TileRect *r=&rects[i];
        if(x>=r->x && y>=r->y && x-r->x<r->w && y-r->y<r->h)return TRUE;
    }
    return FALSE;
}
u16 TERRAIN_attr(u16 col,u16 row)
{
    const TileRect *rects;u16 count,base;
    if(contains(lavaRects,lavaCount,col,row)){rects=lavaRects;count=lavaCount;base=TERRAIN_TILE_BASE;}
    else if(contains(mudRects,mudCount,col,row)){rects=mudRects;count=mudCount;base=TERRAIN_TILE_BASE+TERRAIN_VARIANTS;}
    else return 0;
    const u16 mask=contains(rects,count,col,row-1) |
        (contains(rects,count,col+1,row)<<1) |
        (contains(rects,count,col,row+1)<<2) |
        (contains(rects,count,col-1,row)<<3);
    const u16 variant=mask==15 ? 15+(col&3)+((row&1)<<2) : mask;
    return TILE_ATTR_FULL(paletteBank,FALSE,FALSE,FALSE,base+variant);
}
void TERRAIN_draw(void)
{
    // Fixed-screen levels share exactly the same renderer as scrolling maps.
    for(u16 row=ARENA_TILE_Y+1;row<ARENA_TILE_Y+ARENA_TILES_H-1;row++)
        for(u16 col=ARENA_TILE_X+1;col<ARENA_TILE_X+ARENA_TILES_W-1;col++) {
            const u16 attr=TERRAIN_attr(col,row);
            if(attr)VDP_setTileMapXY(BG_A,attr,col,row);
        }
}
void TERRAIN_update(void)
{
    if(!lavaCount)return;
    if(++animTicks<fps/5)return;
    const u16 bytes=TERRAIN_VARIANTS*32;
    if(DMA_getQueueTransferSize()+bytes+1024>DMA_TRANSFER_CAPACITY_NTSC ||
       DMA_getQueueSize()+3>=DMA_getMaxQueueSize())return;
    const u8 frame=lavaFrame^1;
    adaptPixels(TERRAIN_LAVA_ART+frame*TERRAIN_VARIANTS*8);
    if(!DMA_queueDma(DMA_VRAM,terrainPixels,
        TERRAIN_TILE_BASE*32,TERRAIN_VARIANTS*16,2))return;
    lavaFrame=frame;animTicks=0;
}
