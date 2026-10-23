// Inventário: posição 0 = bomba (reaproveita o módulo actors/bomb); posições
// 1..3 = slots de item. Ativar chama o apply() do item (modo de tiro / escudo)
// e esvazia o slot; ativar a bomba usa uma carga (limpa a tela).

#include "core/inventory.h"
#include "items/items.h"
#include "actors/shots.h"       // ICE_CHARGES / FIRE_CHARGES / SHOTS_CHAIN_HITS
#include "actors/bomb.h"

static InvSlot item[INV_ITEMS];     // slots das posições 1..3
static u8 sel;                      // 0..3 (0 = bomba)

// cargas iniciais (máximas) de cada item
static u8 maxCharges(u8 type)
{
    switch (type)
    {
        case ITEM_ICE:   return ICE_CHARGES;
        case ITEM_FIRE:  return FIRE_CHARGES;
        case ITEM_CHAIN: return SHOTS_CHAIN_HITS;
        default:         return 1;              // escudo
    }
}

void INV_clear(void)
{
    for (u8 i = 0; i < INV_ITEMS; i++) { item[i].type = INV_EMPTY; item[i].charges = 0; }
    sel = 0;
}

void INV_add(u8 t)
{
    if (t == ITEM_BOMB) { BOMB_add(); return; }     // bomba: posição 0
    INV_store(t, maxCharges(t));
}

bool INV_store(u8 t, u8 charges)
{
    if (!ITEM_IS_INVENTORY(t) || t == ITEM_BOMB || !charges) return FALSE;
    // item: primeiro slot livre; o mesmo item repetido ocupa um novo slot
    for (u8 i = 0; i < INV_ITEMS; i++)
        if (item[i].type == INV_EMPTY) { item[i].type = t; item[i].charges = charges; return TRUE; }
    return FALSE;
}

void INV_cycle(void) { sel = (u8) ((sel + 1) % INV_POS); }

u16 INV_activate(void)
{
    if (sel == 0) return BOMB_use();                // bomba: limpa a tela (mortes)

    InvSlot *s = &item[sel - 1];
    if (s->type == INV_EMPTY) return 0;
    ITEM_DEFS[s->type]->apply();                    // modo de tiro / escudo
    s->type = INV_EMPTY; s->charges = 0;
    return 0;
}

void INV_view(u8 i, u8 *type, u8 *count)
{
    if (i == 0) { *type = ITEM_BOMB; *count = (u8) BOMB_count(); }
    else        { *type = item[i - 1].type; *count = item[i - 1].charges; }
}

u8 INV_selected(void) { return sel; }
