// Triângulo Roxo — "Escudeiro": blindado veloz, escudo curto e frequente.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_tri_purple =
{
    .name       = "ESCUDEIRO",
    .shape      = SHAPE_TRIANGLE,
    .color      = COLOR_PURPLE,
    .size       = 16,
    .hp         = 2,
    .contactDmg = 10,
    .dropChance = 30,
    .speedFp    = 50,
    .timerA     = 12,             // 1,2 s vulnerável
    .timerB     = 8,              // 0,8 s com escudo (curto)
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYPURPLE_update,
};
