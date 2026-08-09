// Fase 10: lama — pentágonos + triângulos.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_YEL, ENEMY_PEN_ORG, ENEMY_TRI_ORG };

const LevelDef LEVEL10_def =
{
    .killTarget = 26, .spawnSeconds = 3, .spawnCount = 2,
    .mud = MUD_PAIR, .mudCount = LAYOUT_RECTS,
    .floor = FLOOR_FOREST,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
