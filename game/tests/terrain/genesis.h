// Host-only SGDK surface for testing the production terrain renderer.
#ifndef TEST_TERRAIN_GENESIS_H
#define TEST_TERRAIN_GENESIS_H
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef int32_t s32;
typedef enum {BG_A,BG_B,WINDOW} VDPPlane;
#define TRUE true
#define FALSE false
#define TILE_USER_INDEX 16
#define PAL1 1
#define PAL3 3
#define DMA 1
#define DMA_VRAM 0
#define DMA_TRANSFER_CAPACITY_NTSC 7200
#define TILE_ATTR_FULL(p,pr,v,h,t) (((p)<<13)|((pr)<<15)|((v)<<12)|((h)<<11)|(t))
void VDP_loadTileData(const u32 *,u16,u16,u16);
void VDP_setTileMapXY(VDPPlane,u16,u16,u16);
u16 DMA_getQueueTransferSize(void);
u16 DMA_getQueueSize(void);
u16 DMA_getMaxQueueSize(void);
bool DMA_queueDma(u16,void *,u16,u16,u16);
#endif
