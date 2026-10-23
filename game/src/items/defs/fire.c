// Item fogo (dado: ItemDef). Vai para o inventário; ativado com C. Arte + efeito
// em items/item_fire.c. Peso de drop = (raio 15 + escudo 5) / 4 = 5.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_fire =
{
    .name       = "REFIL DE MAÇARICO",
    .weight     = 5,
    .tile       = TILE_FIRE,
    .buildTile  = ITEMFIRE_buildTile,
    .apply      = ITEMFIRE_apply,
};
