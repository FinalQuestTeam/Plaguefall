// Fase 6: lava — enxame de triângulos.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG };

const LevelDef LEVEL06_def =
{
    .killTarget = 20, .spawnSeconds = 3, .spawnCount = 1,
    .lava = LAVA_PAIR, .lavaCount = LAYOUT_RECTS,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
