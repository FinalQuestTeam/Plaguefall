#ifndef ROUTEMAP_H
#define ROUTEMAP_H

#include <genesis.h>

// Mapa de rotas (estilo Darius): mostrado entre a "FASE CONCLUIDA!" e a
// preparação da próxima. Desenhado A PARTIR DO GRAFO (levels/graph.c —
// mapCol/mapRow dos nós e as saídas), então nunca desatualiza em relação ao
// fluxo. Caminho percorrido = "O"; próxima fase = "*" piscando; resto = ".".

void ROUTEMAP_reset(void);              // novo jogo: zera o caminho percorrido
void ROUTEMAP_markVisited(u8 n);        // início de fase: marca o nó no caminho
void ROUTEMAP_show(u8 nextNode);        // desenha a tela (nó destino em destaque)
void ROUTEMAP_update(void);             // por quadro: pisca o marcador da próxima

#endif // ROUTEMAP_H
