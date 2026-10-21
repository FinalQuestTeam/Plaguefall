// Fase 1: pátio da igreja — protege a retirada; bomba danifica a construção.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_YEL };

const LevelDef LEVEL01_def =
{
    .killTarget   = 10,
    .spawnSeconds = 5,
    .musicTrack   = MUSIC_TRACK_LADAINHA,
    .enemyCap     = 4,
    .shotCap      = 6,
    .musCalmUntil = 1,
    .musEnemyMax  = 4,
    .arena        = &COURTYARD_arena,
    LVL_ROSTER(roster),
};
