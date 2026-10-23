#ifndef ROUTEMAP_H
#define ROUTEMAP_H

#include <genesis.h>

// Four regional paintings. Connections and global overview use GRAPH;
// persistent pointer shows the origin, concentric rings show the destination.
// Borrows BG_A/B, palettes and animation tiles until ROUTEMAP_release().

void ROUTEMAP_reset(void);              // novo jogo: zera o caminho percorrido
void ROUTEMAP_markVisited(u8 n);        // início de fase: marca o nó no caminho
void ROUTEMAP_prepare(u8 currentNode,u8 nextNode);
void ROUTEMAP_show(u8 currentNode, u8 nextNode);
// A/START begins travel; another press skips it. TRUE means ready to leave.
bool ROUTEMAP_update(u16 pressed);
void ROUTEMAP_release(void);            // restores borrowed graphics and palettes

#endif // ROUTEMAP_H
