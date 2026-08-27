// Fase 13A (venceu a 12 em menos de 60 s): lava — mix, spawn rápido.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_PUR, ENEMY_TRI_YEL, ENEMY_TRI_ORG, ENEMY_PEN_RED, ENEMY_PEN_YEL };

const LevelDef LEVEL13_def =
{
    .killTarget   = 34,
    .spawnSeconds = 2,
    .spawnCount   = 2,
    .lava         = LAVA_PAIR,
    .lavaCount    = LAYOUT_RECTS,
    LVL_ROSTER(roster),
};
