// Item shots (dado: ItemDef). Arte + efeito em items/item_shots.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_shots =
{
    .name       = "DIVISOR DE DISPARO",
    .weight     = 10,
    .tile       = TILE_BULLET,
    .buildTile  = ITEMSHOTS_buildTile,
    .apply      = ITEMSHOTS_apply,
};
