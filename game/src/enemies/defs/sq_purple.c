// Quadrado Roxo — "Baluarte": o tanque supremo (blindado, lento, pesado).
// O escudo cíclico entra na Fase B; por ora é um perseguidor lento e forte.
// Abra este arquivo para ajustar todos os números deste inimigo.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_sq_purple =
{
    .name       = "BALUARTE",
    .shape      = SHAPE_SQUARE,
    .color      = COLOR_PURPLE,         // blindado
    .size       = 32,
    .hp         = 6,                    // o mais resistente
    .contactDmg = 15,
    .dropChance = 75,
    .speedFp    = ENEMY_SPEED_FP / 2,   // metade da velocidade do amarelo
    .timerA     = 25,                   // 2,5 s sem escudo (vulnerável)
    .timerB     = 20,                   // 2,0 s com escudo (invulnerável)
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYPURPLE_update,
};
