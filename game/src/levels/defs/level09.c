// Fase 9: vazia — entram os pentágonos (elite).
// Bifurca no grafo: venceu sem levar dano → 10A; levou dano → 10B (lava+lama).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_RED, ENEMY_PEN_YEL, ENEMY_TRI_YEL };

const LevelDef LEVEL09_def =
{
    .killTarget   = 24,
    .spawnSeconds = 4,
    .musicTrack   = MUSIC_TRACK_BREU,
    LVL_ROSTER(roster),
};
