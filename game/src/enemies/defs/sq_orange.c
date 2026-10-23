// Quadrado Laranja — "Aríete": investida resistente e forte.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_sq_orange =
{
    .name       = "ARÍETE",
    .shape      = SHAPE_SQUARE,
    .color      = COLOR_ORANGE,     // investida (dash)
    .size       = 16,
    .hp         = 4,
    .contactDmg = 12,
    .dropChance = 45,
    .speedFp    = ENEMY_SPEED_FP / 2,   // aproxima devagar
    .timerA     = 15,                   // cooldown de 1,5 s entre investidas
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYORANGE_update,
};
