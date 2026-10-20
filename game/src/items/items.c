// Engine dos itens: registro, geração dos tiles, ciclo de vida no chão (TTL,
// piscando no fim), coleta pelo jogador e desenho. O sorteio/queda (loot) fica
// em items/drop.c; o reabastecimento da fase teste em items/test_items.c.

#include "items/items.h"
#include "system/video/sprites/tiles.h"
#include "system/video/spritelist.h"
#include "system/audio/sfx.h"
#include "core/game.h"
#include "core/inventory.h"
#include "core/objective.h"        // OBJECTIVE_addCollected (objetivo COLETAR)

Item items[MAX_ITEMS];

// configurações dos itens — dado em items/defs/*.c (uma por item).
// A chance de um inimigo dropar vem de ENEMY_DEFS[type]->dropChance; o peso de
// QUAL item cai vem de ITEM_DEFS[t]->weight. Fontes únicas, fáceis de ajustar.
extern const ItemDef ITEMDEF_heart, ITEMDEF_bomb, ITEMDEF_shots,
                     ITEMDEF_speed, ITEMDEF_shield, ITEMDEF_chain,
                     ITEMDEF_ice, ITEMDEF_fire;

const ItemDef *const ITEM_DEFS[ITEM_TYPES] =
{
    &ITEMDEF_heart,     // ITEM_HEART
    &ITEMDEF_bomb,      // ITEM_BOMB
    &ITEMDEF_shots,     // ITEM_SHOTS
    &ITEMDEF_speed,     // ITEM_SPEED
    &ITEMDEF_shield,    // ITEM_SHIELD
    &ITEMDEF_chain,     // ITEM_CHAIN
    &ITEMDEF_ice,       // ITEM_ICE
    &ITEMDEF_fire,      // ITEM_FIRE
};

// método ÚNICO de desenho: mapa 16x16 de caracteres + legenda de cores
void ITEMS_paintTile16(u32 *tileBuf, u16 baseTile,
                       const char *const rows[16],
                       const TilePixel *legend, u8 legendCount)
{
    for (u16 y = 0; y < 16; y++)
    {
        for (u16 x = 0; x < 16; x++)
        {
            const char c = rows[y][x];
            u16 col = 0;
            for (u8 k = 0; k < legendCount; k++)
                if (legend[k].ch == c) { col = legend[k].color; break; }
            if (col)
            {
                u16 tile = baseTile + (x / 8) * 2 + (y / 8);
                tileBuf[tile * 8 + (y % 8)] |= (u32) col << ((7 - (x % 8)) * 4);
            }
        }
    }
}

void ITEMS_buildTiles(u32 *tileBuf)
{
    for (u8 t = 0; t < ITEM_TYPES; t++)
        ITEM_DEFS[t]->buildTile(tileBuf);
}

void ITEMS_clear(void)
{
    memset(items, 0, sizeof(items));
    ITEMS_testReset();          // zera o estado do reabastecimento da fase teste
}

void ITEMS_spawnAt(u8 type, s16 x, s16 y)
{
    for (u16 i = 0; i < MAX_ITEMS; i++)
    {
        if (items[i].active) continue;
        items[i].x = x;
        items[i].y = y;
        items[i].ttl = 0xFFFF;      // ~permanente
        items[i].type = type;
        items[i].active = TRUE;
        return;
    }
}

void ITEMS_update(void)
{
    for (u16 i = 0; i < MAX_ITEMS; i++)
    {
        Item *it = &items[i];
        if (!it->active) continue;

        if (--it->ttl == 0)
        {
            it->active = FALSE;
            continue;
        }

        // coleta: AABB 16x16 do jogador sobre o item
        if ((it->x < px + 16) && (it->x + 16 > px) &&
            (it->y < py + 16) && (it->y + 16 > py))
        {
            // itens ativáveis vão para o inventário; os demais aplicam na hora
            if (ITEM_IS_INVENTORY(it->type)) INV_add(it->type);
            else                             ITEM_DEFS[it->type]->apply();
            sfxItemPickup();
            OBJECTIVE_addCollected(it->type);   // COLETAR conta só o item-alvo
            it->active = FALSE;
        }
    }
}

u16 ITEMS_draw(u16 n)
{
    for (u16 i = 0; i < MAX_ITEMS; i++)
    {
        const Item *it = &items[i];
        if (!it->active) continue;

        // pisca nos últimos 2 segundos antes de sumir
        if ((it->ttl < fps * 2) && ((it->ttl >> 2) & 1)) continue;

        const u16 tile = ITEM_DEFS[it->type]->tile;
        SPRITES_emit(&n, it->x, it->y, SPRITE_SIZE(2, 2),
            TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, TILE_USER_INDEX + tile));
    }
    return n;
}
