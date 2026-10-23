// Triângulo Laranja — "Adaga": investidas rápidas e repetidas (frágil).

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_tri_orange =
{
    .name       = "ADAGA",
    .shape      = SHAPE_TRIANGLE,
    .color      = COLOR_ORANGE,
    .size       = 16,
    .hp         = 1,
    .contactDmg = 10,
    .dropChance = 25,
    .speedFp    = ENEMY_SPEED_FP,   // aproxima em ritmo normal
    .timerA     = 8,               // cooldown curto (0,8 s) — investe muito
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYORANGE_update,
};
