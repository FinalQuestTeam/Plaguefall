#ifndef BOMB_H
#define BOMB_H

#include <genesis.h>

// ===========================================================================
// CONFIG (balanceamento da bomba) — ajuste aqui
// ===========================================================================
#define BOMB_MAX    3   // teto de cargas de bomba
// ===========================================================================

// cargas de bomba do jogador (persistem entre fases, teto de BOMB_MAX)

// duas cargas iniciais (novo jogo / treino); NÃO desenha o HUD
void BOMB_reset(void);
void BOMB_clear(void); // nenhuma carga antes de recuperar a bolsa

// +1 carga (respeita o teto) e atualiza o HUD — usado pelo item de bomba
void BOMB_add(void);

// usa 1 carga: som + flash de tela + mata todos os inimigos;
// devolve quantos inimigos morreram (0 se não havia carga)
u16 BOMB_use(void);

// cargas atuais (para o HUD ao (re)desenhar a fase)
u16 BOMB_count(void);

#endif // BOMB_H
