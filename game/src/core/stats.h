#ifndef STATS_H
#define STATS_H

#include <genesis.h>

// Estatísticas da fase em curso — alimentam as condições de saída do grafo
// (levels/graph.c). Zeradas a cada início de fase (startPhase/startTest).
// Para uma condição nova: campo aqui + COND_* em levels/graph.h + caso no
// GRAPH_resolve — nenhuma outra mudança.

typedef struct
{
    u16  bombsUsed;         // bombas detonadas na fase (BOMB_use)
    u16  damageTaken;       // HP perdido na fase (loseHp; escudo não conta)
    u32  frames;            // quadros de jogo ativo (fora do congelamento)
    bool objFailed;         // o objetivo falhou (OBJ_LOST; ex.: aliado caiu)
} PhaseStats;

extern PhaseStats phaseStats;

void STATS_reset(void);     // início de fase: zera tudo
void STATS_tick(void);      // +1 quadro (1x por quadro de jogo ativo)
u16  STATS_seconds(void);   // tempo de fase em segundos (frames / fps)

#endif // STATS_H
