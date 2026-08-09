// Fase 3: lava — entra o roxo (escudo).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_YEL, ENEMY_SQ_PUR, ENEMY_SQ_ORG };

const LevelDef LEVEL03_def =
{
    .killTarget = 14, 
    .spawnSeconds = 4, 
    .spawnCount = 1,
    .lava = LAVA_PAIR, 
    .lavaCount = LAYOUT_RECTS,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
