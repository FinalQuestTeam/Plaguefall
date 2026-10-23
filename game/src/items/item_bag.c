#include "items/items.h"
#include "core/death.h"
#include "system/video/sprites/tiles.h"
#include "system/video/sprites/bag_data.h"

void ITEMBAG_buildTile(u32 *tileBuf)
{
    ITEMS_paintTile16(tileBuf, TILE_BAG, ITEM_BAG_ART, ITEM_BAG_LEG,
                      sizeof(ITEM_BAG_LEG) / sizeof(TilePixel));
}

void ITEMBAG_apply(void)
{
    DEATH_recover();
}
