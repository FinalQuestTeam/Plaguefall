#ifndef HEROGFX_H
#define HEROGFX_H
#include <genesis.h>
#define HERO_FRAME_TILES 24
#include "system/video/projection.h"
#define HERO_MUZZLE_LIFT VIDEO_HEIGHT_OFFSET
// Uses PAL2 and the first 24 tiles of the existing 48-tile player reservation.
void HERO_load(void);
void HERO_prepare(u8 dir);
void HERO_endFrame(void);
u8 HERO_direction(s16 x,s16 y);
// World coordinates of the visible barrel, before projectile height projection.
void HERO_muzzle(s16 *x,s16 *y);
u16 HERO_tile(void);
u8 HERO_flipH(void);
#endif
