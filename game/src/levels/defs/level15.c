// Fase 15: lava+lama — clímax, 7 tipos.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_ORG, ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG, ENEMY_PEN_RED, ENEMY_PEN_PUR, ENEMY_PEN_ORG };

const LevelDef LEVEL15_def =
{
    .killTarget   = 40,
    .spawnSeconds = 2,
    .spawnCount   = 3,
    .lava         = COMBO_LAVA,
    .lavaCount    = LAYOUT_RECTS,
    .mud          = COMBO_MUD,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_MIX,
    LVL_ROSTER(roster),
};
