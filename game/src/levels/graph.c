// FLUXO DA CAMPANHA — este é o ÚNICO arquivo a editar para mudar a ordem das
// fases, criar bifurcações e escolher as condições de cada saída.
//
// COMO LER UMA LINHA DA TABELA:
//
//   [N_5] = FASE("5", LEVEL05_def, MAPA(4, 1),
//                SE_FALHOU_OBJETIVO(N_6B),     // o aliado caiu → retirada
//                SENAO(N_6A)),
//
//   [N_5]         quem sou eu (o nome interno do nó; a lista vive em graph.h)
//   "5"           nome mostrado ao jogador ("FASE 5", pausa e mapa de rotas)
//   LEVEL05_def   a fase em si: objetivo, terreno, inimigos (levels/defs/)
//   MAPA(4, 1)    posição no mapa de rotas: coluna 4, linha 1
//                 (linha 0 = rota A, em cima; 1 = caminho do meio; 2 = rota B)
//   SE_.../SENAO  para onde ir ao VENCER, avaliado na ordem em que aparece:
//                 a primeira condição verdadeira decide. Termine SEMPRE com
//                 SENAO(...). Última fase do jogo = FASE_FINAL (sem saídas).
//
// CONDIÇÕES DISPONÍVEIS (o destino vai entre parênteses):
//   SENAO(n)                 sempre vale — a rota padrão
//   SE_SEM_BOMBA(n)          venceu sem usar nenhuma bomba
//   SE_USOU_BOMBA(n)         venceu usando ao menos uma bomba
//   SE_SEM_DANO(n)           venceu sem perder vida
//   SE_LEVOU_DANO(n)         venceu tendo perdido vida
//   SE_TEMPO_MENOR(seg, n)   venceu em MENOS de `seg` segundos
//   SE_TEMPO_MAIOR(seg, n)   venceu em `seg` segundos ou mais
//   SE_FALHOU_OBJETIVO(n)    o objetivo FALHOU (ex.: o aliado caiu). Com essa
//                            saída no nó, falhar deixa de ser game over e
//                            vira rota — o jogo continua por ela
//
// PARA CRIAR UMA BIFURCAÇÃO NOVA (ex.: 7 → 8A/8B):
//   1. em graph.h, acrescente os nomes no enum (N_8A, N_8B, na ordem do run)
//   2. crie a def da fase nova em levels/defs/ (copie uma existente) e
//      declare-a no bloco de externs de levels/levels.h
//   3. aqui: dê ao N_7 as duas saídas (SE_...(N_8A) + SENAO(N_8B)), adicione
//      as linhas dos nós novos (rota A na linha 0 do MAPA, rota B na linha 2)
//      e aponte os dois para o nó onde a rota reconverge
//   O mapa de rotas do jogo se redesenha sozinho a partir desta tabela.
//
// Mapa atual (uma coluna por passo do run; plano em doc/plano-rotas.md):
//   1 ─┬─ 2A ─┬─ 3 ─ 4 ─ 5 ─┬─ 6A ─┬─ 7 ─ 8 ─ 9 ─┬─ 10A ─┬─ 11 ─ 12 ─┬─ 13A ─┬─ 14 ─ 15 ─ 16
//      └─ 2B ─┘              └─ 6B ─┘              └─ 10B ─┘           └─ 13B ─┘        (chefe)

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
                   SE_SEM_BOMBA(N_2A),          // maestria: segurou a bomba
                   SENAO(N_2B)),                // gastou bomba → lama cedo

    [N_2A]  = FASE("2A", LEVEL02_def,  MAPA(1, 0), SENAO(N_3)),
    [N_2B]  = FASE("2B", LEVEL02B_def, MAPA(1, 2), SENAO(N_3)),

    [N_3]   = FASE("3",  LEVEL03_def, MAPA(2, 1), SENAO(N_4)),
    [N_4]   = FASE("4",  LEVEL04_def, MAPA(3, 1), SENAO(N_5)),

    [N_5]   = FASE("5",  LEVEL05_def, MAPA(4, 1),  // PROTEGER o aliado (30 s)
                   SE_FALHOU_OBJETIVO(N_6B),    // o aliado caiu → retirada
                   SENAO(N_6A)),

    [N_6A]  = FASE("6A", LEVEL06_def,  MAPA(5, 0), SENAO(N_7)),
    [N_6B]  = FASE("6B", LEVEL06B_def, MAPA(5, 2), SENAO(N_7)),

    [N_7]   = FASE("7",  LEVEL07_def, MAPA(6, 1), SENAO(N_8)),
    [N_8]   = FASE("8",  LEVEL08_def, MAPA(7, 1), SENAO(N_9)),

    [N_9]   = FASE("9",  LEVEL09_def, MAPA(8, 1),
                   SE_SEM_DANO(N_10A),          // maestria: saiu intocado
                   SENAO(N_10B)),               // levou dano → lava + lama

    [N_10A] = FASE("10A", LEVEL10_def,  MAPA(9, 0), SENAO(N_11)),
    [N_10B] = FASE("10B", LEVEL10B_def, MAPA(9, 2), SENAO(N_11)),

    [N_11]  = FASE("11", LEVEL11_def, MAPA(10, 1), SENAO(N_12)),

    [N_12]  = FASE("12", LEVEL12_def, MAPA(11, 1),
                   SE_TEMPO_MENOR(60, N_13A),   // agressivo: menos de 60 s
                   SENAO(N_13B)),               // demorou → lama, ritmo pesado

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
