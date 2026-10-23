// Item chain (dado: ItemDef). Arte + efeito em items/item_chain.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_chain =
{
    .name       = "BOBINA DE SUBESTAÇÃO",
    .weight     = 5,
    .tile       = TILE_CHAIN,
    .buildTile  = ITEMCHAIN_buildTile,
    .apply      = ITEMCHAIN_apply,
};
