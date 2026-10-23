// Quadrado Amarelo — "Batedor": perseguidor resistente e firme.
// Abra este arquivo para ajustar todos os números deste inimigo.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_sq_yellow =
{
    .name       = "BATEDOR",
    .shape      = SHAPE_SQUARE,
    .color      = COLOR_YELLOW,     // perseguidor
    .size       = 16,
    .hp         = 3,                // quadrado = resistente
    .contactDmg = 8,
    .dropChance = 40,
    .speedFp    = ENEMY_SPEED_FP,   // persegue em ritmo padrão
    .timerA     = 0,
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYYELLOW_update,
};
