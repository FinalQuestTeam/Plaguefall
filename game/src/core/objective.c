// Sistema de objetivos de fase — ver objective.h.

#include "core/objective.h"
#include "core/game.h"
#include "actors/npc.h"
#include "enemies/enemies.h"                     // ENEMIES_setAggroSplit (PROTEGER)
#include "items/items.h"                        // ITEM_* (item alvo do COLETAR)
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"

static const LevelDef *cur;
static u16 surviveLeft;      // frames restantes (SURVIVE / PROTECT)
static u16 collected;        // itens do tipo-alvo coletados (COLLECT)
static u16 hudLast;          // assinatura do último HUD desenhado (gate de redesenho)

// nome (PT) do item para o texto da preparação do COLETAR
static const char *itemName(u8 type)
{
    switch (type)
    {
        case ITEM_HEART:  return "CORACOES";
        case ITEM_BOMB:   return "BOMBAS";
        case ITEM_SHOTS:  return "BALAS";
        case ITEM_SPEED:  return "BOTINHAS";
        case ITEM_SHIELD: return "ESCUDOS";
        case ITEM_CHAIN:  return "RAIOS";
        case ITEM_ICE:    return "GELOS";
        case ITEM_FIRE:   return "FOGOS";
    }
    return "ITENS";
}

// tile 8x8 do símbolo do item (para o HUD do COLETAR)
static u16 itemIcon(u8 type)
{
    switch (type)
    {
        case ITEM_HEART:  return TILE_ICON_HEART;
        case ITEM_BOMB:   return TILE_BOMB_ICON;
        case ITEM_SHIELD: return TILE_ICON_SHIELD;
        case ITEM_CHAIN:  return TILE_BOLT;
        case ITEM_ICE:    return TILE_ICON_ICE;
        case ITEM_FIRE:   return TILE_ICON_FIRE;
    }
    return TILE_SKULL;                           // fallback (itens sem ícone 8x8)
}

void OBJECTIVE_start(const LevelDef *def)
{
    cur = def;
    collected = 0;
    surviveLeft = (u16) (def->objTarget * fps);
    hudLast = 0xFFFF;                            // força o 1º desenho do HUD
    VDP_clearText(1, 0, 13);                     // zera a área do contador (sem sobras)

    if (def->objective == OBJ_PROTECT)
    {
        NPC_spawn(def->npcX, def->npcY, def->npcHp);
        ENEMIES_setAggroSplit(3);       // 1 a cada 3 inimigos persegue o jogador
    }
    else
    {
        NPC_clear();
        ENEMIES_setAggroSplit(0);       // demais objetivos: todos no alvo padrão
    }
}

void OBJECTIVE_addCollected(u8 itemType)
{
    // só conta o item-alvo da fase (não qualquer item)
    if (cur->objective == OBJ_COLLECT && itemType == cur->collectItem) collected++;
}

u8 OBJECTIVE_update(u16 kills)
{
    switch (cur->objective)
    {
        case OBJ_SURVIVE:
            if (surviveLeft) surviveLeft--;
            return surviveLeft ? OBJ_ONGOING : OBJ_WON;

        case OBJ_COLLECT:
            return (collected >= cur->objTarget) ? OBJ_WON : OBJ_ONGOING;

        case OBJ_PROTECT:
            NPC_update();                       // sofre dano de inimigos encostados
            if (!NPC_alive()) return OBJ_LOST;  // aliado caiu = falha
            if (surviveLeft) surviveLeft--;
            return surviveLeft ? OBJ_ONGOING : OBJ_WON;

        default: // OBJ_KILL
            return (kills >= cur->killTarget) ? OBJ_WON : OBJ_ONGOING;
    }
}

// segundos restantes (arredonda p/ cima) do timer de sobrevivência
static u16 secsLeft(void) { return (u16) ((surviveLeft + fps - 1) / fps); }

// desenha um ícone 8x8 na coluna col da linha 0 do HUD (pal escolhe a cor:
// PAL1 = cor "natural" do tile; PAL0 = branco, p/ o coração do aliado)
static void icon(u16 tile, u16 col, u16 pal)
{
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(pal, FALSE, FALSE, FALSE,
        TILE_USER_INDEX + tile), col, 0);
}

void OBJECTIVE_drawHUD(u16 kills)
{
    char buf[12];

    switch (cur->objective)
    {
        case OBJ_SURVIVE:
        {
            const u16 s = secsLeft();
            if (s == hudLast) return;
            hudLast = s;
            icon(TILE_CLOCK, 1, PAL1);          // só o relógio + o tempo
            sprintf(buf, "%02d", s);
            VDP_drawText(buf, 3, 0);
            break;
        }
        case OBJ_COLLECT:
        {
            if (collected == hudLast) return;
            hudLast = collected;
            icon(itemIcon(cur->collectItem), 1, PAL1);  // símbolo do item alvo
            sprintf(buf, "%d/%d ", collected, cur->objTarget);
            VDP_drawText(buf, 3, 0);
            break;
        }
        case OBJ_PROTECT:
        {
            const u16 hp = (u16) (npcHp < 0 ? 0 : npcHp);
            const u16 sig = (u16) (secsLeft() * 512 + hp);
            if (sig == hudLast) return;
            hudLast = sig;
            icon(TILE_ICON_ANTENNA, 1, PAL0);   // antena BRANCA (aliado) + vida
            sprintf(buf, "%03d", hp);
            VDP_drawText(buf, 3, 0);
            icon(TILE_CLOCK, 7, PAL1);          // relógio + tempo
            sprintf(buf, "%02d", secsLeft());
            VDP_drawText(buf, 9, 0);
            break;
        }
        default: // OBJ_KILL
            if (kills == hudLast) return;
            hudLast = kills;
            HUD_drawKills(kills, cur->killTarget);
            break;
    }
}

void OBJECTIVE_prepText(char *buf, const LevelDef *def)
{
    switch (def->objective)
    {
        case OBJ_SURVIVE: sprintf(buf, "META: SOBREVIVA %d S", def->objTarget); break;
        case OBJ_COLLECT: sprintf(buf, "META: COLETE %d %s", def->objTarget, itemName(def->collectItem)); break;
        case OBJ_PROTECT: sprintf(buf, "META: PROTEJA O ALIADO %d S", def->objTarget); break;
        default:          sprintf(buf, "META: MATE %d INIMIGOS", def->killTarget); break;
    }
}
