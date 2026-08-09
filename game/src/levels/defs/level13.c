// Fase 13: lava — mix, spawn rápido.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_PUR, ENEMY_TRI_YEL, ENEMY_TRI_ORG, ENEMY_PEN_RED, ENEMY_PEN_YEL };

const LevelDef LEVEL13_def =
{
    .killTarget = 34, .spawnSeconds = 2, .spawnCount = 2,
    .lava = LAVA_PAIR, .lavaCount = LAYOUT_RECTS,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
