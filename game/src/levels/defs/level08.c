// Fase 8: lava — triângulos em dupla.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG, ENEMY_SQ_ORG };

const LevelDef LEVEL08_def =
{
    .killTarget   = 24,
    .spawnSeconds = 3,
    .spawnCount   = 2,
    .lava         = LAVA_PAIR,
    .lavaCount    = LAYOUT_RECTS,
    .musicTrack   = MUSIC_TRACK_BAIAO,
    LVL_ROSTER(roster),
};
