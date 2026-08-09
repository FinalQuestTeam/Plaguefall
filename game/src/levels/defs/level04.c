// Fase 4: lama — 1º triângulo (velocidade).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_PUR, ENEMY_TRI_YEL };

const LevelDef LEVEL04_def =
{
    .killTarget = 16, .spawnSeconds = 4, .spawnCount = 1,
    .mud = MUD_PAIR, .mudCount = LAYOUT_RECTS,
    .floor = FLOOR_FOREST,
    // musica (BPM x ameaca): padrao global; ajuste por fase se quiser
    .musCalmUntil = 4, .musEnemyMax = 15, .musStepCalm = 12, .musStepHot = 4,
    LVL_ROSTER(roster),
};
