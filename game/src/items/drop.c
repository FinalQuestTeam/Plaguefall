// Loot: quando um inimigo morre, sorteia se dropa (chance por tipo de inimigo)
// e QUAL item cai (peso por item). Opera sobre o vetor items[] do engine.

#include "items/items.h"
#include "core/game.h"
#include "enemies/enemies.h"

// sorteia o tipo de item proporcional ao peso (ITEM_DEFS[t]->weight); usa a SOMA
// dos pesos (não precisa somar 100 — assim os pesos novos entram sem renormalizar)
static u8 pickItemType(void)
{
    u16 total = 0;
    for (u8 t = 0; t < ITEM_DROP_TYPES; t++) total += ITEM_DEFS[t]->weight;

    u16 r = random() % total;
    for (u8 t = 0; t < ITEM_DROP_TYPES; t++)
    {
        if (r < ITEM_DEFS[t]->weight) return t;
        r -= ITEM_DEFS[t]->weight;
    }
    return ITEM_HEART;          // segurança: nunca sorteia bolsa
}

void ITEMS_tryDrop(s16 cx, s16 cy, u8 enemyType)
{
    if ((random() % 100) >= ENEMY_DEFS[enemyType]->dropChance) return;

    for (u16 i = 0; i < MAX_ITEMS; i++)
    {
        if (items[i].active) continue;

        s16 x = cx - 8, y = cy - 8;
        if (x < INNER_MIN_X) x = INNER_MIN_X;
        if (x > INNER_MAX_X - 15) x = INNER_MAX_X - 15;
        if (y < INNER_MIN_Y) y = INNER_MIN_Y;
        if (y > INNER_MAX_Y - 15) y = INNER_MAX_Y - 15;

        items[i].x = x;
        items[i].y = y;
        items[i].ttl = fps * 10;    // 10 s no chão
        items[i].type = pickItemType();
        items[i].active = TRUE;
        return;
    }
    // sem slot livre: o drop é perdido
}
