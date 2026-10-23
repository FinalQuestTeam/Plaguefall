#ifndef DEATH_H
#define DEATH_H
#include <genesis.h>

#define DEATH_KEEP 0
#define DEATH_REDUCE 1
#define DEATH_BAG 2

u8 DEATH_rule(u8 node); // usa a etapa, incluindo as rotas A/B
void DEATH_reset(void); // novo jogo / treino
void DEATH_capture(u8 node, s16 x, s16 y); // fotografia do equipamento antes da queda
void DEATH_retry(u8 node, s16 x, s16 y); // uma penalidade por nova tentativa
void DEATH_startPhase(u8 node); // coloca a bolsa após limpar itens
#define DEATH_RECOVER_BLOCKED 0
#define DEATH_RECOVER_PARTIAL 1
#define DEATH_RECOVER_DONE 2
u8 DEATH_recover(void); // sem espaço: guarda os itens restantes na bolsa

#endif
