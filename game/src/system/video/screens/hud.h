#ifndef HUD_H
#define HUD_H

#include <genesis.h>
#define HUD_OPAQUE_COUNT 11
void HUD_loadOpaqueIcons(void);
u16 HUD_iconAttr(u16 tile, u16 pal);

// linha 0 da tela: caveira+mortes | inventário (ícones) | modo ativo | HP
void HUD_drawKills(u16 kills, u16 target);
void HUD_drawLife(s16 hp);

// inventário: 4 posições (0=bomba, 1-3 itens) com ÍCONE + contagem, selecionado
// com cursor; + o modo de tiro ativo. Chamado a cada quadro em jogo.
void HUD_drawInventory(void);

// como HUD_drawInventory, mas só redesenha quando o estado muda (uso por quadro)
void HUD_drawInventoryIfDirty(void);

#endif // HUD_H
