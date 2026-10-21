// Fase 10A (venceu a 9 sem dano): lama — pentágonos + triângulos.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_YEL, ENEMY_PEN_ORG, ENEMY_TRI_ORG };

const LevelDef LEVEL10_def =
{
    .killTarget   = 26,
    .spawnSeconds = 3,
    .spawnCount   = 2,
    .mud          = MUD_PAIR,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_FOREST,
    .musicTrack   = MUSIC_TRACK_BAIAO,
    LVL_ROSTER(roster),
};
