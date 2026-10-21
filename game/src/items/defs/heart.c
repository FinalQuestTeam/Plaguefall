// Item heart (dado: ItemDef). Arte + efeito em items/item_heart.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_heart =
{
    .name       = "MARMITA DO ABRIGO",
    .weight     = 40,
    .tile       = TILE_HEART,
    .buildTile  = ITEMHEART_buildTile,
    .apply      = ITEMHEART_apply,
};
