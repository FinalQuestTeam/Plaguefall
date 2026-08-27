// Fase 13B: rota de quem demorou na fase 12 (60 s ou mais) — a fase 13 em
// versão "pesada": mesma pressão de spawn, mas na lama (ritmo defensivo).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_PUR, ENEMY_TRI_YEL, ENEMY_TRI_ORG, ENEMY_PEN_RED, ENEMY_PEN_YEL };

const LevelDef LEVEL13B_def =
{
    .killTarget   = 34,
    .spawnSeconds = 2,
    .spawnCount   = 2,
    .mud          = MUD_PAIR,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_FOREST,
    LVL_ROSTER(roster),
};
