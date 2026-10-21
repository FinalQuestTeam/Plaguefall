// Item shield (dado: ItemDef). Arte + efeito em items/item_shield.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"

const ItemDef ITEMDEF_shield =
{
    .name       = "CAPACITOR DE PROTECAO",
    .weight     = 5,
    .tile       = TILE_SHIELD,
    .buildTile  = ITEMSHIELD_buildTile,
    .apply      = ITEMSHIELD_apply,
};
