// Item bomb (dado: ItemDef). Arte + efeito em items/item_bomb.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_bomb =
{
    .name       = "CARGA DE DESMONTE",
    .weight     = 20,
    .tile       = TILE_BOMB,
    .buildTile  = ITEMBOMB_buildTile,
    .apply      = ITEMBOMB_apply,
};
