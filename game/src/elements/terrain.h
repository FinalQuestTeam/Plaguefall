#ifndef MODULAR_TERRAIN_H
#define MODULAR_TERRAIN_H
#include "elements/elements.h"
#include "system/video/sprites/tiles.h"

// Portable overlay, adapted to scenery PAL3 (PAL1 fallback on legacy floors).
// Rectangles use world tile coordinates; touching rectangles join seamlessly.
#define TERRAIN_TILE_BASE (TILE_USER_INDEX+ENEMY_ICON_BASE+120)
#define TERRAIN_TILE_COUNT 46
void TERRAIN_start(const TileRect *lava,u16 lavaCount,const TileRect *mud,u16 mudCount,const u16 *palette);
void TERRAIN_clear(void);
bool TERRAIN_active(void);
u16 TERRAIN_attr(u16 col,u16 row);
void TERRAIN_draw(void);
void TERRAIN_update(void);
#endif
