// Dummy — alvo de teste: quadrado cinza 24x24, HP 20, parado, sem dano/drop.
// Usado só na fase teste.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_dummy =
{
    .name       = "DUMMY",
    .shape      = SHAPE_SQUARE,
    .color      = COLOR_GRAY,
    .size       = 24,
    .hp         = 20,
    .contactDmg = 0,            // não machuca (é um alvo)
    .dropChance = 0,
    .speedFp    = 0,
    .timerA     = 0,
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYDUMMY_update,
};
