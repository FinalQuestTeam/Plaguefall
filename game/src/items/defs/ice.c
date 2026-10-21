// Item gelo (dado: ItemDef). Vai para o inventário; ativado com C. Arte + efeito
// em items/item_ice.c. Peso de drop = (raio 15 + escudo 5) / 4 = 5.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_ice =
{
    .name       = "REFIL DE ARREFECIMENTO",
    .weight     = 5,
    .tile       = TILE_ICE,
    .buildTile  = ITEMICE_buildTile,
    .apply      = ITEMICE_apply,
};
