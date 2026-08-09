// Fase 11: lava+lama — escudo e leque.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_PEN_RED, ENEMY_PEN_PUR, ENEMY_TRI_YEL };

const LevelDef LEVEL11_def =
{
    .killTarget = 28, .spawnSeconds = 3, .spawnCount = 2,
    .lava = COMBO_LAVA, .lavaCount = LAYOUT_RECTS,
    .mud = COMBO_MUD, .mudCount = LAYOUT_RECTS,
    .floor = FLOOR_MIX,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
