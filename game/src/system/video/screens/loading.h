#ifndef LOADING_H
#define LOADING_H
#include <genesis.h>

// Cooperative graphics work: music/SFX continue at video-frame boundaries.
// Nested owners are supported; no interrupt callback competes with gameplay.
void LOADING_workBegin(void);
void LOADING_workEnd(void);
void LOADING_poll(void);
bool LOADING_begin(u16 minimumFrames,u8 missionNode);
void LOADING_end(void);
bool LOADING_active(void);

// The loading WINDOW borrows low tiles and PAL0. Destination writes to that
// range are shadowed and restored on release, so scene resources keep their
// established addresses while the radio monitor remains visible.
void LOADING_setEnable(bool enabled);
void LOADING_windowOff(void);
void LOADING_setColor(u16 index,u16 color);
void LOADING_setColors(u16 index,const u16 *colors,u16 count,TransferMethod method);
void LOADING_tiles(const u32 *data,u16 index,u16 count,TransferMethod method);
void LOADING_copyVRAM(const u16 *data,u16 address,u16 words);
void LOADING_getColors(u16 index,u16 *colors,u16 count);
#endif
