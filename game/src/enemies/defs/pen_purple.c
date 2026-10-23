// Pentágono Roxo — "Fortaleza": blindado elite; invoca lacaios enquanto blindado.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_pen_purple =
{
    .name       = "FORTALEZA",
    .shape      = SHAPE_PENTAGON,
    .color      = COLOR_PURPLE,
    .size       = 32,
    .hp         = 4,
    .contactDmg = 15,
    .dropChance = 80,
    .speedFp    = ENEMY_SPEED_FP / 2 - 5,   // bem lento
    .timerA     = 20,            // 2,0 s vulnerável
    .timerB     = 25,            // 2,5 s com escudo (longo)
    .extra      = EXTRA_SUMMON,  // truque: invoca lacaios
    .behavior   = ENEMYPURPLE_update,
};
