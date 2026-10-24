#ifndef INVENTORY_H
#define INVENTORY_H

#include <genesis.h>

// Inventário de itens ativáveis. 4 posições selecionáveis:
//   posição 0 = BOMBA (espelha BOMB_count(); ativar = limpar a tela)
//   posições 1..3 = slots de item (raio/escudo/gelo/fogo)
// Ao coletar, o item entra num slot livre; o MESMO item repetido ocupa um novo
// slot (aparece 2 vezes). Em jogo: C troca a seleção, B ativa o selecionado.

#define INV_ITEMS   3       // slots de item (1..3)
#define INV_POS     4       // posições selecionáveis (0 = bomba)
#define INV_EMPTY   0xFF

typedef struct { u8 type; u8 charges; } InvSlot;

void INV_clear(void);                       // novo jogo / treino / nova tentativa
void INV_add(u8 itemType);                  // coleta (bomba -> BOMB_add; item -> slot livre)
bool INV_store(u8 itemType, u8 charges);     // devolve item guardado com as cargas originais
void INV_cycle(void);                       // C: seleciona a próxima posição
u16  INV_activate(void);                    // B: ativa o selecionado; retorna mortes (bomba)

// leitura para o HUD: tipo e contagem da posição i (0 = bomba)
void INV_view(u8 i, u8 *type, u8 *count);
u8   INV_selected(void);
// Read-only HUD comparison, including the live bomb count.
bool INV_matches(const u8 *types,const u8 *counts);

#endif // INVENTORY_H
