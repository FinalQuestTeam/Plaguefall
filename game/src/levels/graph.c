// Campaign flow:19versions,16stages per run, three independent decisions.
// 1:bomb -> church intact/ruined;5:signal -> all/partial rescue;
// 12:Dinorah alive/dead ->13A/13B. Every pair then reconverges.
// Persistent consequences and dialogue variants live in core/campaign_state.c.
#include "levels/graph.h"
#include "core/stats.h"

// ---------------------------------------------------------------------------
// Vocabulário da tabela (expande para LevelNode/LevelExit; não precisa mexer)
// ---------------------------------------------------------------------------
#define MAPA(col, lin)          (col), (lin)

#define SENAO(n)                { COND_SENAO,       0,     (n) }
#define SE_SEM_BOMBA(n)         { COND_SEM_BOMBA,   0,     (n) }
#define SE_USOU_BOMBA(n)        { COND_USOU_BOMBA,  0,     (n) }
#define SE_SEM_DANO(n)          { COND_SEM_DANO,    0,     (n) }
#define SE_LEVOU_DANO(n)        { COND_LEVOU_DANO,  0,     (n) }
#define SE_TEMPO_MENOR(seg, n)  { COND_TEMPO_MENOR, (seg), (n) }
#define SE_TEMPO_MAIOR(seg, n)  { COND_TEMPO_MAIOR, (seg), (n) }
#define SE_FALHOU_OBJETIVO(n)   { COND_OBJ_FALHOU,  0,     (n) }

#define FASE(nm, def, mapa, ...) \
    { (nm), &(def), mapa, (const LevelExit[]){ __VA_ARGS__ }, \
      sizeof((const LevelExit[]){ __VA_ARGS__ }) / sizeof(LevelExit) }
#define FASE_FINAL(nm, def, mapa)  { (nm), &(def), mapa, NULL, 0 }

// ---------------------------------------------------------------------------
// A TABELA — edite aqui
// ---------------------------------------------------------------------------
const LevelNode GRAPH[NODE_MAX] =
{
    // [0] não é usado: 0 = fase teste (fora da campanha)

    [N_1]   = FASE("1",  LEVEL01_def, MAPA(0, 1),
                   SE_SEM_BOMBA(N_2A),          // Igreja preservada
                   SENAO(N_2B)),                // Igreja destruída, destroços sólidos

    [N_2A]  = FASE("2A", LEVEL02_def,  MAPA(1, 0), SENAO(N_3)),
    [N_2B]  = FASE("2B", LEVEL02B_def, MAPA(1, 2), SENAO(N_3)),

    [N_3]   = FASE("3",  LEVEL03_def, MAPA(2, 1), SENAO(N_4)),
    [N_4]   = FASE("4",  LEVEL04_def, MAPA(3, 1), SENAO(N_5)),

    [N_5]   = FASE("5",  LEVEL05_def, MAPA(4, 1),  // Proteger a Santa por120s
                   SE_FALHOU_OBJETIVO(N_6B),    // Sinal interrompido: perdas civis
                   SENAO(N_6A)),

    [N_6A]  = FASE("6A", LEVEL06_def,  MAPA(5, 0), SENAO(N_7)),
    [N_6B]  = FASE("6B", LEVEL06B_def, MAPA(5, 2), SENAO(N_7)),

    [N_7]   = FASE("7",  LEVEL07_def, MAPA(6, 1), SENAO(N_8)),
    [N_8]   = FASE("8",  LEVEL08_def, MAPA(7, 1), SENAO(N_9)),

    [N_9] = FASE("9",LEVEL09_def,MAPA(8,1),SENAO(N_10)),
    [N_10] = FASE("10",LEVEL10_def,MAPA(9,1),SENAO(N_11)),

    [N_11]  = FASE("11", LEVEL11_def, MAPA(10, 1), SENAO(N_12)),

    [N_12]  = FASE("12", LEVEL12_def, MAPA(11, 1),
                   SE_FALHOU_OBJETIVO(N_13B),
                   SENAO(N_13A)),               // Dinorah viva: apoio final

    [N_13A] = FASE("13A", LEVEL13_def,  MAPA(12, 0), SENAO(N_14)),
    [N_13B] = FASE("13B", LEVEL13B_def, MAPA(12, 2), SENAO(N_14)),

    [N_14]  = FASE("14", LEVEL14_def, MAPA(13, 1), SENAO(N_15)),
    [N_15]  = FASE("15", LEVEL15_def, MAPA(14, 1), SENAO(N_16)),

    [N_16]  = FASE_FINAL("16", LEVEL16_def, MAPA(15, 1)),   // chefe (Escorpiao)
};

// ---------------------------------------------------------------------------
// Navegação (lógica; a tabela acima é o único lugar a editar no dia a dia)
// ---------------------------------------------------------------------------

bool GRAPH_isFinal(u8 n)
{
    return GRAPH[n].exitCount == 0;
}

bool GRAPH_hasFailExit(u8 n)
{
    const LevelNode *node = &GRAPH[n];
    for (u8 i = 0; i < node->exitCount; i++)
        if (node->exits[i].cond == COND_OBJ_FALHOU) return TRUE;
    return FALSE;
}

// a condição da saída vale com as estatísticas atuais? (SENAO = sempre)
static bool condMet(const LevelExit *e)
{
    const PhaseStats *s = &phaseStats;
    switch (e->cond)
    {
        case COND_SEM_BOMBA:   return s->bombsUsed == 0;
        case COND_USOU_BOMBA:  return s->bombsUsed > 0;
        case COND_SEM_DANO:    return s->damageTaken == 0;
        case COND_LEVOU_DANO:  return s->damageTaken > 0;
        case COND_TEMPO_MENOR: return STATS_seconds() <  e->value;
        case COND_TEMPO_MAIOR: return STATS_seconds() >= e->value;
        case COND_OBJ_FALHOU:  return s->objFailed;
        default:               return TRUE;             // COND_SENAO
    }
}

u8 GRAPH_resolve(u8 n)
{
    const LevelNode *node = &GRAPH[n];

    // falha do objetivo tem prioridade sobre a ordem da tabela: se a fase
    // falhou e o nó tem rota de falha, é ela — mesmo mal posicionada
    if (phaseStats.objFailed)
        for (u8 i = 0; i < node->exitCount; i++)
            if (node->exits[i].cond == COND_OBJ_FALHOU)
                return node->exits[i].next;

    for (u8 i = 0; i < node->exitCount; i++)
    {
        if (node->exits[i].cond == COND_OBJ_FALHOU) continue;   // só via falha
        if (condMet(&node->exits[i])) return node->exits[i].next;
    }
    return 0;                                           // nó final
}

u8 GRAPH_defaultNext(u8 n)
{
    const LevelNode *node = &GRAPH[n];
    for (u8 i = 0; i < node->exitCount; i++)
        if (node->exits[i].cond == COND_SENAO) return node->exits[i].next;
    // sem SENAO explícito (tabela mal formada): usa a primeira saída
    return node->exitCount ? node->exits[0].next : 0;
}

u16 GRAPH_reachableTypes(u8 n)
{
    static u16 memo[NODE_MAX];
    static u8  state[NODE_MAX];     // 0 = novo, 1 = calculando, 2 = pronto

    if (state[n] == 2) return memo[n];
    if (state[n] == 1) return 0;    // ciclo (erro de tabela): corta a recursão
    state[n] = 1;

    const LevelNode *node = &GRAPH[n];
    u16 mask = 0;
    for (u16 i = 0; i < node->def->enemyTypeCount; i++)
        mask |= (u16) 1 << node->def->enemyTypes[i];
    for (u8 i = 0; i < node->exitCount; i++)
        mask |= GRAPH_reachableTypes(node->exits[i].next);

    memo[n] = mask;
    state[n] = 2;
    return mask;
}
