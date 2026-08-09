// Fase 9: vazia — entram os pentágonos (elite).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_RED, ENEMY_PEN_YEL, ENEMY_TRI_YEL };

const LevelDef LEVEL09_def =
{
    .killTarget = 24, .spawnSeconds = 4, .spawnCount = 1,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
