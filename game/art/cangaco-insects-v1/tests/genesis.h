#ifndef GENESIS_H
#define GENESIS_H
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
typedef uint8_t u8; typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
#define TRUE true
#define FALSE false
#define PAL0 0
#define PAL1 1
#define PAL2 2
#define PAL3 3
#define TILE_USER_INDEX 16
#define BG_A 0
#define DMA 1
#define DMA_QUEUE 2
#define DMA_VRAM 0
#define DMA_TRANSFER_CAPACITY_NTSC 7200
#define SPRITE_SIZE(w,h) ((((w)-1)<<2)|((h)-1))
#define TILE_ATTR_FULL(p,prio,v,h,t) (((p)<<13)|((prio)<<15)|((v)<<12)|((h)<<11)|(t))
void PAL_setColors(u16,const u16*,u16,u8);
void VDP_loadTileData(const u32*,u16,u16,u8);
void VDP_setTileMapXY(u16,u16,u16,u16);
void VDP_setSpriteFull(u16,s16,s16,u8,u16,u8);
void VDP_setSpriteLink(u16,u8);
void VDP_updateSprites(u16,u8);
u16 DMA_getQueueTransferSize(void);
u16 DMA_getQueueSize(void);
u16 DMA_getMaxQueueSize(void);
bool DMA_queueDma(u8,void*,u16,u16,u16);
#endif
