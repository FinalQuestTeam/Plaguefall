// Pentágono Vermelho — "Artilheiro": atirador elite, dispara em leque (3 tiros).

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_pen_red =
{
    .name       = "ARTILHEIRO",
    .shape      = SHAPE_PENTAGON,
    .color      = COLOR_RED,
    .size       = 24,
    .hp         = 3,
    .contactDmg = 10,
    .dropChance = 60,
    .speedFp    = 0,               // fixo
    .timerA     = 25,             // leque a cada 2,5 s
    .timerB     = 0,
    .extra      = EXTRA_SPREAD,   // truque: leque de tiros
    .behavior   = ENEMYRED_update,
};
