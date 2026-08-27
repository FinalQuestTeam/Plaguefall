// Fase 6A (protegeu o aliado na 5): lava — enxame de triângulos.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG };

const LevelDef LEVEL06_def =
{
    .killTarget   = 20,
    .spawnSeconds = 3,
    .lava         = LAVA_PAIR,
    .lavaCount    = LAYOUT_RECTS,
    LVL_ROSTER(roster),
};
