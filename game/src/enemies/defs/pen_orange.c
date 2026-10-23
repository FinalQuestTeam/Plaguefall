// Pentágono Laranja — "Meteoro": investida elite; teleporta antes de investir.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_pen_orange =
{
    .name       = "METEORO",
    .shape      = SHAPE_PENTAGON,
    .color      = COLOR_ORANGE,
    .size       = 24,
    .hp         = 3,
    .contactDmg = 14,
    .dropChance = 60,
    .speedFp    = ENEMY_SPEED_FP / 2,
    .timerA     = 18,            // cooldown de 1,8 s
    .timerB     = 0,
    .extra      = EXTRA_TELEPORT,   // truque: pisca para perto antes do bote
    .behavior   = ENEMYORANGE_update,
};
