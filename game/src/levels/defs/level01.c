// Fase 1: vazia — quadrados (aprende as cores).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_YEL };

const LevelDef LEVEL01_def =
{
    .killTarget   = 10,
    .spawnSeconds = 5,
    LVL_ROSTER(roster),
};
