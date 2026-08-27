#ifndef GRAPH_H
#define GRAPH_H

#include <genesis.h>
#include "levels/levels.h"

// Grafo da campanha: cada fase é um NÓ com uma lista de SAÍDAS; cada saída tem
// uma condição avaliada ao vencer a fase (a primeira satisfeita decide a
// próxima). A tabela editável fica em levels/graph.c — para mudar o fluxo do
// jogo (bifurcações, condições, ordem), edite SÓ aquele arquivo.
// Plano completo: doc/plano-rotas.md.

// condições de saída (campo LevelExit.cond)
#define COND_SENAO        0   // sempre verdadeira — rota padrão (última saída)
#define COND_SEM_BOMBA    1   // venceu sem usar nenhuma bomba
#define COND_USOU_BOMBA   2   // venceu usando ao menos uma bomba
#define COND_SEM_DANO     3   // venceu sem perder HP
#define COND_LEVOU_DANO   4   // venceu tendo perdido HP
#define COND_TEMPO_MENOR  5   // venceu em MENOS de value segundos
#define COND_TEMPO_MAIOR  6   // venceu em value segundos ou mais
#define COND_OBJ_FALHOU   7   // o objetivo FALHOU (ex.: aliado caiu) — se o nó
                              // tem essa saída, falhar vira rota, não game over

typedef struct
{
    u8  cond;               // COND_*
    u16 value;              // parâmetro (segundos nas condições de tempo)
    u8  next;               // nó destino (1..NODE_COUNT)
} LevelExit;

typedef struct
{
    const char *name;       // "2A" → "FASE 2A" (preparação, pausa, mapa)
    const LevelDef *def;    // objetivo/terreno/roster/música da fase
    u8  mapCol, mapRow;     // posição no mapa de rotas (tela da etapa 3)
    const LevelExit *exits; // avaliadas em ordem; NULL = nó final (fim do jogo)
    u8  exitCount;
} LevelNode;

// nós da campanha (1..NODE_COUNT; 0 continua sendo a fase teste). Mantenha a
// ordem do enum na ordem de progressão (nós alternativos juntos, ex.:
// N_2A/N_2B antes de N_3) — só por legibilidade; o descarte de arte na VRAM
// usa alcançabilidade real (GRAPH_reachableTypes), não o número do nó.
typedef enum
{
    N_1 = 1, N_2A, N_2B, N_3, N_4, N_5, N_6A, N_6B, N_7, N_8,
    N_9, N_10A, N_10B, N_11, N_12, N_13A, N_13B, N_14, N_15, N_16,
    NODE_MAX
} NodeId;

#define NODE_COUNT      (NODE_MAX - 1)

// [0] não é usado (0 = fase teste); indexe direto pelo número do nó
extern const LevelNode GRAPH[NODE_MAX];

// nó final (sem saídas) = última fase do run (hoje, o chefe)
bool GRAPH_isFinal(u8 n);

// TRUE se o nó tem uma saída COND_OBJ_FALHOU (falhar o objetivo vira rota)
bool GRAPH_hasFailExit(u8 n);

// avalia as saídas do nó n contra as estatísticas da fase (core/stats) e
// devolve o próximo nó (1..NODE_COUNT), ou 0 se o nó é final
u8 GRAPH_resolve(u8 n);

// próximo nó pela saída SENAO, ignorando condições (debug: pular fase);
// 0 se o nó é final
u8 GRAPH_defaultNext(u8 n);

// máscara (bit = tipo de inimigo) dos rosters de todo nó ALCANÇÁVEL a partir
// de n, incluindo n. Dirige o descarte de arte na VRAM (enemygfx): tipo fora
// da máscara do nó atual não aparece mais neste run. Memoizada (grafo fixo).
u16 GRAPH_reachableTypes(u8 n);

#endif // GRAPH_H
