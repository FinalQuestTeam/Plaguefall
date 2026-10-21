// Fase 12: lava+lama — teleporte.
// Bifurca no grafo: venceu em menos de 60 s → 13A; demorou → 13B (lama).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_ORG, ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_SQ_PUR };

const LevelDef LEVEL12_def =
{
    .killTarget   = 30,
    .spawnSeconds = 3,
    .spawnCount   = 2,
    .lava         = COMBO_LAVA,
    .lavaCount    = LAYOUT_RECTS,
    .mud          = COMBO_MUD,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_MIX,
    .musicTrack   = MUSIC_TRACK_BAIAO,
    LVL_ROSTER(roster),
};
