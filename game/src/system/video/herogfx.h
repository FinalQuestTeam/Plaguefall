#ifndef HEROGFX_H
#define HEROGFX_H
#include <genesis.h>
#define HERO_FRAME_TILES 24
#include "system/video/projection.h"
#define HERO_MUZZLE_LIFT VIDEO_HEIGHT_OFFSET
// Uses PAL2 and the first 24 tiles of the existing 48-tile player reservation.
void HERO_load(void);
void HERO_prepare(u8 dir);
u16 HERO_tile(void);
u8 HERO_flipH(void);
void HERO_loadPreview(void);
u16 HERO_previewTile(u8 dir);
u8 HERO_previewFlipH(u8 dir);
#endif
