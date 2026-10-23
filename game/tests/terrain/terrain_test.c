#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "elements/terrain.c"
#include "system/video/blood.c"

u16 fps=60;
s16 arenaMinX=0,arenaMinY=0,arenaMaxX=2047,arenaMaxY=383,cameraX,cameraY;
bool arenaActive=TRUE;
static u32 vram[2048*8];
static u16 writes,queuedBytes;
static bool acceptDma=TRUE;
void VDP_loadTileData(const u32 *source,u16 tile,u16 count,u16 method)
{(void)method;assert(tile+count<=2048);memcpy(vram+tile*8,source,count*32);}
void VDP_setTileMapXY(VDPPlane plane,u16 attr,u16 x,u16 y)
{assert(plane==BG_A && x<64 && y<32);assert(attr);writes++;}
u16 DMA_getQueueTransferSize(void){return queuedBytes;}
u16 DMA_getQueueSize(void){return 0;}
u16 DMA_getMaxQueueSize(void){return 64;}
bool DMA_queueDma(u16 target,void *source,u16 address,u16 words,u16 step)
{
    assert(target==DMA_VRAM && step==2);
    if(!acceptDma)return FALSE;
    memcpy((u8 *)vram+address,source,words*2);return TRUE;
}
bool ARENA_blocked(s16 x,s16 y,u16 w,u16 h)
{(void)x;(void)y;(void)w;(void)h;return FALSE;}
static u16 variant(u16 x,u16 y,u16 materialBase)
{
    const u16 attr=TERRAIN_attr(x,y);
    assert((attr&0xe000)==(PAL1<<13));
    return (attr&2047)-materialBase;
}
int main(void)
{
    // Adjacent rectangles must lose their shared border. An L-shaped union
    // stays empty in its notch, and unrelated materials never join.
    const TileRect lava[]={{4,4,3,3},{7,4,3,3},{4,7,3,3}},mud[]={{10,4,3,3}};
    TERRAIN_start(lava,3,mud,1,NULL);
    assert(variant(4,4,TERRAIN_TILE_BASE)==6);
    assert(variant(6,5,TERRAIN_TILE_BASE)>=15);
    assert(variant(7,5,TERRAIN_TILE_BASE)>=15);
    assert(variant(9,5,TERRAIN_TILE_BASE)==13);
    assert(variant(10,5,TERRAIN_TILE_BASE+TERRAIN_VARIANTS)==7);
    assert(!TERRAIN_attr(7,7) && !TERRAIN_attr(3,4));
    assert(variant(5,6,TERRAIN_TILE_BASE)>=15);
    writes=0;TERRAIN_draw();assert(writes==36);
    // Damage/slowdown zones stay legible after an enemy dies on their edge.
    writes=0;BLOOD_splat(40,40);assert(!writes);
    BLOOD_splat(120,120);assert(writes==4);
    const TileRect tiny[]={{0,0,1,1}},far[]={{130,10,2,2}};
    TERRAIN_start(tiny,1,far,1,NULL);
    assert(variant(0,0,TERRAIN_TILE_BASE)==0);
    assert(!TERRAIN_attr(65535,0) && !TERRAIN_attr(2,10));
    assert(variant(130,10,TERRAIN_TILE_BASE+TERRAIN_VARIANTS)==6);
    // Zero-sized rectangles do not create isolated phantom pieces.
    const TileRect zero[]={{2,2,0,3},{2,2,3,0}};
    TERRAIN_start(zero,2,NULL,0,NULL);assert(!TERRAIN_attr(2,2));
    for(u16 region=0;region<2;region++) {
        fps=region ? 50 : 60;TERRAIN_start(tiny,1,far,1,TERRAIN_SOURCE_PALETTE);
        const u32 first=vram[TERRAIN_TILE_BASE*8+15*8+3];
        queuedBytes=7200;for(u16 i=0;i<fps;i++)TERRAIN_update();
        assert(vram[TERRAIN_TILE_BASE*8+15*8+3]==first);
        queuedBytes=0;acceptDma=FALSE;TERRAIN_update();
        assert(vram[TERRAIN_TILE_BASE*8+15*8+3]==first);
        acceptDma=TRUE;TERRAIN_update();
        assert(!memcmp(vram+TERRAIN_TILE_BASE*8,TERRAIN_LAVA_ART+TERRAIN_VARIANTS*8,TERRAIN_VARIANTS*32));
        assert(!memcmp(vram+(TERRAIN_TILE_BASE+TERRAIN_VARIANTS)*8,TERRAIN_MUD_ART,TERRAIN_VARIANTS*32));
    }
    u16 palette[16];memcpy(palette,TERRAIN_SOURCE_PALETTE,sizeof palette);
    palette[1]=TERRAIN_SOURCE_PALETTE[7];palette[7]=TERRAIN_SOURCE_PALETTE[1];
    TERRAIN_start(tiny,1,far,1,palette);
    assert((TERRAIN_attr(0,0)&0xe000)==(PAL3<<13));
    assert(palettePairs[0x17]==0x71 && palettePairs[0x10]==0x70);
    assert(!memcmp(palette+2,TERRAIN_SOURCE_PALETTE+2,5*sizeof(u16)));
    TERRAIN_clear();assert(!TERRAIN_active() && !TERRAIN_attr(0,0));
    puts("PASS: connected rectangles/L shapes, material boundaries, world coordinates, transparent gaps, blood preservation scene palette remapping/transparency and PAL/NTSC animation/DMA backpressure.");
    return 0;
}
