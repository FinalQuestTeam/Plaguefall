// Fase 3: lava — entra o roxo (escudo).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_YEL, ENEMY_SQ_PUR, ENEMY_SQ_ORG };

const LevelDef LEVEL03_def =
{
    .killTarget   = 14,
    .spawnSeconds = 4,
    .lava         = LAVA_PAIR,
    .lavaCount    = LAYOUT_RECTS,
    LVL_ROSTER(roster),
};
