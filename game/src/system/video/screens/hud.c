// HUD: linha 0 (mortes, inventário — bomba na posição 0 —, modo de tiro e vida).

#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "core/inventory.h"
#include "items/items.h"
#include "actors/shots.h"
#include "system/video/floor.h"
#include "system/video/sprites/item_icons_data.h"
#include "system/video/sprites/icons_data.h"
#include "system/video/sprites/saint_data.h"
#include "levels/courtyard_data.h"

#define HUD_OPAQUE_BASE (TILE_USER_INDEX + FLOOR_TILE_BASE + COURTYARD_TILE_COUNT)
static const u16 opaqueTiles[HUD_OPAQUE_COUNT]={TILE_SKULL,TILE_BOMB_ICON,TILE_BOLT,TILE_ICON_SHIELD,TILE_ICON_ICE,TILE_ICON_FIRE,TILE_ICON_HEART,TILE_CLOCK,TILE_ICON_SAINT,TILE_ICON_SHOTS,TILE_ICON_SPEED};
static const u32 *const opaqueSources[HUD_OPAQUE_COUNT]={NULL,ITEM_BOMB_ICON_DATA,ITEM_CHAIN_ICON_DATA,ITEM_SHIELD_ICON_DATA,ITEM_ICE_ICON_DATA,ITEM_FIRE_ICON_DATA,ITEM_HEART_ICON_DATA,NULL,SAINT_ICON_DATA,ITEM_SHOTS_ICON_DATA,ITEM_SPEED_ICON_DATA};

void HUD_loadOpaqueIcons(void)
{
    // PAL1 index B is opaque black. Original icon/sprite tiles stay intact.
    u32 data[8];
    for(u16 i=0;i<HUD_OPAQUE_COUNT;i++) {
        for(u16 y=0;y<8;y++) {
            u32 row=opaqueSources[i] ? opaqueSources[i][y] : 0;
            if(!opaqueSources[i]) {
                const char *art=(i==0 ? ICON_SKULL_ART : ICON_CLOCK_ART)[y];
                for(u16 x=0;x<8;x++)if(art[x]=='#')row|=1UL<<((7-x)*4);
            }
            for(u16 x=0;x<8;x++)if(!(row&(15UL<<(x*4))))row|=11UL<<(x*4);
            data[y]=row;
        }
        VDP_loadTileData(data,HUD_OPAQUE_BASE+i,1,DMA);
    }
}
u16 HUD_iconAttr(u16 tile,u16 pal)
{
    if(arenaActive && pal==PAL1)
        for(u16 i=0;i<HUD_OPAQUE_COUNT;i++)if(tile==opaqueTiles[i])
            return TILE_ATTR_FULL(pal,TRUE,FALSE,FALSE,HUD_OPAQUE_BASE+i);
    return TILE_ATTR_FULL(pal,FALSE,FALSE,FALSE,TILE_USER_INDEX+tile);
}

void HUD_drawKills(u16 kills, u16 target)
{
    char buf[16];
    VDP_setTileMapXY(ARENA_hudPlane(),
        HUD_iconAttr(TILE_SKULL,PAL1), 1, 0);
    sprintf(buf, "%02d/%02d", kills, target);
    VDP_drawText(buf, 3, 0);
}

void HUD_drawLife(s16 hp)
{
    char buf[12];
    sprintf(buf, "HP:%3d", hp < 0 ? 0 : hp);
    VDP_drawText(buf, 33, 0);
}

// tile do ícone 8x8 de cada tipo de item de inventário
static u16 iconTile(u8 type)
{
    switch (type)
    {
        case ITEM_BOMB:   return TILE_BOMB_ICON;
        case ITEM_CHAIN:  return TILE_BOLT;
        case ITEM_SHIELD: return TILE_ICON_SHIELD;
        case ITEM_ICE:    return TILE_ICON_ICE;
        case ITEM_FIRE:   return TILE_ICON_FIRE;
    }
    return TILE_BOMB_ICON;
}

// desenha um char isolado (usado para cursor e contagem, sem apagar o tile ícone)
static void putc0(char c, u16 col)
{
    char s[2]; s[0] = c; s[1] = 0;
    VDP_drawText(s, col, 0);
}

// layout centralizado na linha 0: inventário (4 pos × 3 cols) no centro da tela
// (col 20), modo de tiro ativo logo à direita.
#define INV_HUD_X   14      // 4×3 = 12 cols → 14..25 (centro ≈ 20)
#define MODE_HUD_X  27

// assinatura do estado desenhado (cursor + tipos/contagens dos slots + modo/cargas).
// Serve para redesenhar o inventário só quando algo muda (evita ~15 escritas no VDP
// por quadro à toa). Guardada abaixo por HUD_drawInventory.
static u32 s_invSig;

static u32 hudInvSig(void)
{
    u32 s = (u32) INV_selected();
    for (u8 i = 0; i < INV_POS; i++)
    {
        u8 type, count;
        INV_view(i, &type, &count);
        s = s * 131u + ((u32) type << 8) + count;
    }
    s = s * 131u + ((u32) SHOTS_mode() << 8) + SHOTS_modeCharges();
    return s;
}

void HUD_drawInventory(void)
{
    // 4 posições (0=bomba, 1-3 itens), 3 cols cada: [cursor] [ícone] [contagem]
    for (u8 i = 0; i < INV_POS; i++)
    {
        const u16 base = INV_HUD_X + i * 3;
        u8 type, count;
        INV_view(i, &type, &count);

        putc0(i == INV_selected() ? '>' : ' ', base);
        if (type == INV_EMPTY)
        {
            putc0('-', base + 1);
            putc0(' ', base + 2);
        }
        else
        {
            VDP_setTileMapXY(ARENA_hudPlane(),
                HUD_iconAttr(iconTile(type),PAL1),
                base + 1, 0);
            putc0((char) ('0' + (count % 10)), base + 2);
        }
    }

    // modo de tiro ativo (raio/gelo/fogo): ícone + cargas
    const u8 mode = SHOTS_mode();
    if (mode != SHOTMODE_NONE && SHOTS_modeCharges())
    {
        const u16 t = (mode == SHOTMODE_CHAIN) ? TILE_BOLT
                    : (mode == SHOTMODE_ICE)   ? TILE_ICON_ICE : TILE_ICON_FIRE;
        VDP_setTileMapXY(ARENA_hudPlane(),
            HUD_iconAttr(t,PAL1), MODE_HUD_X, 0);
        putc0((char) ('0' + (SHOTS_modeCharges() % 10)), MODE_HUD_X + 1);
    }
    else { putc0(' ', MODE_HUD_X); putc0(' ', MODE_HUD_X + 1); }

    s_invSig = hudInvSig();     // baseline p/ o gating por quadro
}

// versão por quadro: só redesenha quando o estado muda (a maioria dos quadros não
// mexe no inventário → economiza as escritas no VDP). Os pontos de montagem da fase
// (startPhase/startTest/pause) chamam HUD_drawInventory direto, que sempre desenha.
void HUD_drawInventoryIfDirty(void)
{
    if (hudInvSig() == s_invSig) return;
    HUD_drawInventory();
}
