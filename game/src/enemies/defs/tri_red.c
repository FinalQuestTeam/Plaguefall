// Triângulo Vermelho — "Fuzileiro": atirador ágil e frágil (move e atira rápido).

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_tri_red =
{
    .name       = "FUZILEIRO",
    .shape      = SHAPE_TRIANGLE,
    .color      = COLOR_RED,
    .size       = 16,
    .hp         = 1,                // triângulo = frágil
    .contactDmg = 6,
    .dropChance = 20,
    .speedFp    = 55,              // persegue enquanto atira
    .timerA     = 10,              // atira a cada 1,0 s
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYRED_update,
};
