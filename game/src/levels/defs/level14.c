// Fase 14: lava+lama — pentágonos pesados, trios.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_PUR, ENEMY_PEN_ORG, ENEMY_PEN_YEL, ENEMY_TRI_YEL };

const LevelDef LEVEL14_def =
{
    .killTarget   = 37,
    .spawnSeconds = 2,
    .spawnCount   = 3,
    .lava         = COMBO_LAVA,
    .lavaCount    = LAYOUT_RECTS,
    .mud          = COMBO_MUD,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_MIX,
    LVL_ROSTER(roster),
};
