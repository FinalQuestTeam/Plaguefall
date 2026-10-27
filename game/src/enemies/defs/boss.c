// CHEFE "Escorpiao" — inimigo bônus da última fase. Sprite dedicado 48x48
// (INS_BOSS48, desenhado em 4 quadrantes); comportamento em enemy_boss.c.
//   25 de vida · contato20 · tiro13 · até2lacaios/10s · fase1:blindado3s/15s
//   Aos12HP:fúria, duas investidas avisadas, recuperação1.2s e leques alternados.
//   resistente à bomba · fase agressiva com investidas (dash)
// timerA/B não são usados (o comportamento tem contador próprio).

#include "enemies/enemies.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"

const EnemyDef ENEMYDEF_boss =
{
    .name       = "ESCORPIÃO",
    .shape      = SHAPE_SQUARE,      // escorpiao (arte propria via enemygfx)
    .color      = COLOR_RED,         // classe de comportamento; o chefe usa arte propria
    .size       = 48,
    .hp         = 25,
    .contactDmg = 20,
    .dropChance = 100,               // derruba item ao morrer (recompensa)
    .speedFp    = ENEMY_SPEED_FP - 8, // um pouco mais lento que o padrão
    .timerA     = 0,
    .timerB     = 0,
    .extra      = EXTRA_NONE,
    .behavior   = ENEMYBOSS_update,
};
