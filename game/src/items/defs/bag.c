#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_bag =
{
    .name = "BORNAL DE RECUPERAÇÃO",
    .weight = 0,
    .tile = TILE_BAG,
    .buildTile = ITEMBAG_buildTile,
    .apply = ITEMBAG_apply,
};
