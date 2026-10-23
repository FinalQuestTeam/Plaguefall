// Alvo frágil — quadrado cinza 24x24, HP 1, parado, sem dano/drop.
// Usado só na FASE TESTE 2, para demonstrar a reação em cadeia do item raio:
// um tiro no grupo (com o raio ativo) elimina os 3 de uma vez. Reusa a arte e o
// comportamento (parado) do dummy — muda só o HP.

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_target =
{
    .name       = "ALVO",
    .shape      = SHAPE_SQUARE,
    .color      = COLOR_GRAY,
    .size       = 24,
    .hp         = 1,            // morre em 1 acerto (do tiro OU da cadeia)
    .contactDmg = 0,            // não machuca (é um alvo)
    .dropChance = 0,
    .speedFp    = 0,
    .timerA     = 0,
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYDUMMY_update,
};
