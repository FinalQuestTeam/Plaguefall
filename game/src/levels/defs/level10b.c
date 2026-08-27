// Fase 10B: rota de quem levou dano na fase 9 — a fase 10 com lava E lama
// (o terreno pune quem já joga descuidado; o combo antecipa o mix da 11).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_YEL, ENEMY_PEN_ORG, ENEMY_TRI_ORG };

const LevelDef LEVEL10B_def =
{
    .killTarget   = 26,
    .spawnSeconds = 3,
    .spawnCount   = 2,
    .lava         = COMBO_LAVA,
    .lavaCount    = LAYOUT_RECTS,
    .mud          = COMBO_MUD,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_MIX,
    LVL_ROSTER(roster),
};
