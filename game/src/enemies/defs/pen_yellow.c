// Pentágono Amarelo — "Alcateia": perseguidor elite; divide-se em 2 ao morrer.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_pen_yellow =
{
    .name       = "ALCATEIA",
    .shape      = SHAPE_PENTAGON,
    .color      = COLOR_YELLOW,
    .size       = 24,
    .hp         = 3,
    .contactDmg = 10,
    .dropChance = 55,
    .speedFp    = 35,
    .timerA     = 0,
    .timerB     = 0,
    .extra      = EXTRA_SPLIT,    // truque: divide-se em 2 Caçadores
    .behavior   = ENEMYYELLOW_update,
};
