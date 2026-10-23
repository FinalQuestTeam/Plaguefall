#ifndef HUD_H
#define HUD_H

#include <genesis.h>
#include "system/video/sprites/tiles.h"
#define HUD_HEIGHT 24
#define HUD_ROWS 3
#define HUD_TILE_COUNT 120
#define HUD_TILE_BASE (TILE_USER_INDEX+ENEMY_ICON_BASE)
#define HUD_OPAQUE_COUNT 11
void HUD_begin(void);
void HUD_present(void); // commit the prepared HUD after releasing loading WINDOW
void HUD_flush(void);
void HUD_drawObjective(const char *label,u16 icon,const char *value,u16 auxiliaryIcon,const char *auxiliary);
void HUD_loadOpaqueIcons(void);
u16 HUD_iconAttr(u16 tile, u16 pal);

// Painel24px: objetivo | equipamento | modo ativo | vida e barra.
void HUD_drawKills(u16 kills, u16 target);
void HUD_drawLife(s16 hp);

// inventário: 4 posições (0=bomba, 1-3 itens) com ÍCONE + contagem, selecionado
// com borda dourada; caixa azul para o modo de tiro ativo.
void HUD_drawInventory(void);

// como HUD_drawInventory, mas só redesenha quando o estado muda (uso por quadro)
void HUD_drawInventoryIfDirty(void);

#endif // HUD_H
