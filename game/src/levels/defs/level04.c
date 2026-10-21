// Fase 4: lama — 1º triângulo (velocidade).

#include "levels/levels.h"
#include "levels/stage_scenes.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_PUR, ENEMY_TRI_YEL };

const LevelDef LEVEL04_def =
{
    .killTarget   = 16,
    .spawnSeconds = 4,
    .mud          = STAGE04_mud,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_FOREST,
    .musicTrack   = MUSIC_TRACK_BREU,
    .musEnemyMax  = 4,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ARENA04,
    LVL_ROSTER(roster),
};
