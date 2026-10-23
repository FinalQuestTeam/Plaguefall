// Quadrado Vermelho — "Torreão": atirador resistente e quase fixo.
// Abra este arquivo para ajustar todos os números deste inimigo.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_sq_red =
{
    .name       = "TORREÃO",
    .shape      = SHAPE_SQUARE,
    .color      = COLOR_RED,        // atirador
    .size       = 16,
    .hp         = 3,                // quadrado = resistente
    .contactDmg = 8,
    .dropChance = 45,
    .speedFp    = 0,                // fixo (não persegue)
    .timerA     = 20,               // atira a cada 2,0 s
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYRED_update,
};
