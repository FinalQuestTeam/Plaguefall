// Fase 15: lava+lama — clímax, 7 tipos.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_ORG, ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG, ENEMY_PEN_RED, ENEMY_PEN_PUR, ENEMY_PEN_ORG };

const LevelDef LEVEL15_def =
{
    .killTarget = 40, 
    .spawnSeconds = 2, 
    .spawnCount = 3,
    .lava = COMBO_LAVA, 
    .lavaCount = LAYOUT_RECTS,
    .mud = COMBO_MUD, 
    .floor = FLOOR_MIX,
    .mudCount = LAYOUT_RECTS,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
