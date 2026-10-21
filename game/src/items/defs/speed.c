// Item speed (dado: ItemDef). Arte + efeito em items/item_speed.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_speed =
{
    .name       = "SERVO DE PASSADA",
    .weight     = 10,
    .tile       = TILE_BOOT,
    .buildTile  = ITEMSPEED_buildTile,
    .apply      = ITEMSPEED_apply,
};
