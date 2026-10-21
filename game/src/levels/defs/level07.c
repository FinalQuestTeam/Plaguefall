// Fase 7: lama — duplas começam.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_TRI_YEL, ENEMY_TRI_PUR, ENEMY_SQ_PUR };

const LevelDef LEVEL07_def =
{
    .killTarget   = 22,
    .spawnSeconds = 3,
    .spawnCount   = 2,
    .mud          = MUD_PAIR,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_FOREST,
    .musicTrack   = MUSIC_TRACK_ENTARDECER,
    LVL_ROSTER(roster),
};
