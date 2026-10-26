#ifndef GAME_MARKERS_H
#define GAME_MARKERS_H
#include <genesis.h>
// Virtual HUD symbols; world badges use the same artwork and PAL1.
#define MARKER_HUD_E 0xff00
#define MARKER_HUD_S 0xff01
#define MARKER_HUD_W 0xff02
#define MARKER_HUD_N 0xff03
void MARKERS_load(void);
u16 MARKERS_hudArrow(s16 dx,s16 dy);
const u32 *MARKERS_iconData(u16 symbol);
void MARKERS_destination(u16 *n,s16 centerX,s16 centerY);
void MARKERS_alert(u16 *n,s16 centerX,s16 feetY);
void MARKERS_shoot(u16 *n,s16 centerX,s16 gateTop,u8 hits);
#endif
