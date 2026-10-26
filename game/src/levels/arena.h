#ifndef LEVEL_ARENA_H
#define LEVEL_ARENA_H
#include <genesis.h>

typedef struct { s16 x, y, w, h; bool blocksShots; } ArenaRect;
typedef struct { u16 sourceCount; } ArenaStream;
typedef struct {
    u16 col, row, cols, rows;
    const u16 *floor;          // revealed when the mapped objective blinks/falls
    ArenaRect footprint;      // same solid rectangle used for enemy contact
    s16 crownX, crownY;        // world position of the 8x8 sparkle
    u16 crownTile;            // two scene-atlas tiles, rendered using PAL1
    s16 focusTop;             // include the complete beacon floor markings
} ArenaNpcVisual;
typedef struct {
    const u32 *tiles;
    const u16 *map, *damaged, *palette;
    u16 tileCount, rows;
    const u32 *glow;             // A then B; base frame lives in tiles.
    u16 glowStart, glowCount;
    bool npcInMap;
    const ArenaNpcVisual *npcVisual;
    u16 cols;                  // zero = legacy 64-column source
    u16 cameraPlayerY;         // zero = arena follow; corridors retain facade headroom
    const ArenaRect *cameraFocus;
    u8 cameraFocusCount;
    const ArenaStream *stream; // optional exact ROM-to-visible640-tile cache
    u16 cameraSouthStart;      // optional player Y where the southern reveal starts
} ArenaScene;
typedef struct {
    u16 width, height;
    s16 minX, minY, maxX, maxY;
    s16 startX, startY;
    const ArenaRect *solids;
    u8 solidCount;
    const ArenaScene *scene;
} ArenaDef;

extern s16 arenaMinX, arenaMinY, arenaMaxX, arenaMaxY;
extern s16 cameraX, cameraY;
extern bool arenaActive;
extern u8 arenaDamaged;
extern const ArenaDef COURTYARD_arena;

u16 ARENA_sceneTileCount(void);
u16 ARENA_backgroundAttr(s16 col,s16 row);
void ARENA_configure(const ArenaDef *def);
void ARENA_draw(void);
void ARENA_leave(void);
void ARENA_camera(void);
void ARENA_overlay(void);
void ARENA_gameView(void);
void ARENA_damageChurch(void);
void ARENA_bright(u16 mix);
void ARENA_update(void);
bool ARENA_npcInMap(void);
const ArenaNpcVisual *ARENA_npcVisual(void);
void ARENA_showNpc(bool visible);
u16 ARENA_npcBar(u16 hp, u16 maximum);
bool ARENA_blocked(s16 x, s16 y, u16 w, u16 h);
bool ARENA_shotBlocked(s16 x, s16 y);
bool ARENA_playerShotBlocked(s16 x, s16 y);
void ARENA_move(s32 *x, s32 *y, s16 dx, s16 dy, u16 size);
s16 ARENA_startX(void);
s16 ARENA_startY(void);
VDPPlane ARENA_hudPlane(void);
const u16 *ARENA_scenePalette(void);
#endif
