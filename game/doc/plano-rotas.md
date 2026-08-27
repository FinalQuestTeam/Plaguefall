# Plano: sistema de rotas (fases com múltiplas saídas)

> Decisões de design (27/08/2026): malha que **reconverge** (estilo Darius);
> comunicação por **mapa de rotas** entre fases; fluxo definido em **tabela C
> com macros** (`levels/graph.c`); condições iniciais: **bomba**, **sem dano**,
> **tempo** e **falha do objetivo** (ex.: a torre/aliado caiu vira rota, não
> game over).

## 1. Conceito

A campanha deixa de ser uma sequência fixa 1→2→…→16 e vira um **grafo**: cada
fase (nó) tem uma lista de **saídas**, cada saída com uma **condição** avaliada
ao vencer a fase. A primeira condição satisfeita decide a próxima fase; a
última saída é sempre `SENAO` (incondicional), então nunca há beco sem saída.

As rotas **divergem e reconvergem** (malha): todo run tem o mesmo número de
fases, o conteúdo extra fica controlado e as duas rotas de cada bifurcação se
encontram adiante. O chefe (Lacraia) continua único no fim.

Princípios de design das bifurcações:

- **Condição = estilo de jogo**, não sorte: sem bomba (recurso), sem dano
  (maestria), tempo (agressividade), objetivo falhado (consequência).
- A rota "de maestria" (A) é **mais difícil e mais generosa** (itens/coleta);
  a rota padrão (B) é o caminho de menor atrito.
- **Falhar o PROTEGER não é mais game over** quando o nó define uma saída
  `OBJ_FALHOU`: a torre caiu → fase de "retirada" mais dura. Fracasso vira
  história, não tela de derrota (padrão Wing Commander).

## 2. Mapa proposto (primeiro alvo de balanceamento)

```
1 ─┬─ 2A ─┬─ 3A ─┐
   └─ 2B ─┴─ 3B ─┴─ 4 ── 5 ─┬─ 6A ─┐
                            └─ 6B ─┴─ 7 ── 8 ── 9 ─┬─ 10A ─┐
                                                   └─ 10B ─┴─ 11 ─ … ─ 15 ── 16 (chefe)
```

| Bifurcação | Condição para a rota A | Tema |
|---|---|---|
| 1 → 2A/2B | venceu **sem usar bomba** | pedido original; 2A premia com fase de coleta rica |
| 5 → 6A/6B | **protegeu** a torre/aliado (6B = `OBJ_FALHOU`, "retirada") | consequência narrativa |
| 9 → 10A/10B | venceu **sem levar dano** | maestria pura |
| 12 → 13A/13B (opcional, 2ª leva) | venceu em **menos de X s** | agressividade |

Custo de conteúdo: ~5–7 `LevelDef` novas (2B, 3B, 6B, 10B…), reaproveitando as
defs atuais como rota A. Nada disso é fixo no código — é só editar `graph.c`.

## 3. O arquivo de fluxo: `levels/graph.c`

Um único arquivo legível define **número/nome, def (objetivo), saídas e
condições**. Sintaxe alvo:

A tabela usa um vocabulário em português pensado para ser editável por
qualquer pessoa (o manual completo está no cabeçalho do próprio `graph.c`):

```c
    [N_1]   = FASE("1", LEVEL01_def, MAPA(0, 1),
                   SE_SEM_BOMBA(N_2A),          // maestria: segurou a bomba
                   SENAO(N_2B)),                // gastou bomba → lama cedo

    [N_5]   = FASE("5", LEVEL05_def, MAPA(4, 1),   // PROTEGER o aliado
                   SE_FALHOU_OBJETIVO(N_6B),    // o aliado caiu → retirada
                   SENAO(N_6A)),

    [N_12]  = FASE("12", LEVEL12_def, MAPA(11, 1),
                   SE_TEMPO_MENOR(60, N_13A),   // agressivo: menos de 60 s
                   SENAO(N_13B)),               // demorou → lama

    [N_16]  = FASE_FINAL("16", LEVEL16_def, MAPA(15, 1)),  // chefe: fim do jogo
};
```

Condições: `SENAO`, `SE_SEM_BOMBA`/`SE_USOU_BOMBA`, `SE_SEM_DANO`/
`SE_LEVOU_DANO`, `SE_TEMPO_MENOR(seg, …)`/`SE_TEMPO_MAIOR(seg, …)` e
`SE_FALHOU_OBJETIVO`. `MAPA(coluna, linha)` posiciona o nó no mapa de rotas
(linha 0 = rota A, 1 = caminho principal, 2 = rota B).

### Estruturas (`levels/graph.h`)

```c
typedef struct {
    u8  cond;       // COND_* abaixo
    u16 value;      // parâmetro (segundos para as condições de tempo)
    u8  next;       // índice do nó destino
} LevelExit;

typedef struct {
    const char *name;        // "2A" → "FASE 2A" (preparação, pausa, mapa)
    const LevelDef *def;     // objetivo/terreno/roster/música (inalterado)
    u8  mapCol, mapRow;      // posição do nó no mapa de rotas
    const LevelExit *exits;  // NULL/0 = nó final (fim do jogo)
    u8  exitCount;
} LevelNode;
```

### Condições (`COND_*`)

| Condição | Verdadeira quando | Fonte do dado |
|---|---|---|
| `SENAO` | sempre (obrigatória como última saída) | — |
| `SEM_BOMBA` / `USOU_BOMBA` | `stats.bombsUsed == 0` / `> 0` | `BOMB_use()` |
| `SEM_DANO` / `LEVOU_DANO` | `stats.damageTaken == 0` / `> 0` | hook no dano do jogador |
| `TEMPO_MENOR` / `TEMPO_MAIOR` | tempo de fase `< value` / `>= value` (s) | frames em `ST_PLAY` |
| `OBJ_FALHOU` | o objetivo retornou `OBJ_LOST` (só PROTEGER hoje) | `OBJECTIVE_update` |

Regra especial de `OBJ_FALHOU`: se o nó **tem** uma saída com essa condição,
`OBJ_LOST` encerra a fase como "concluída" por essa rota (mensagem própria,
ex.: "A TORRE CAIU!" → mapa → próxima fase). Se **não tem**, mantém o
comportamento atual (game over, recomeça a fase).

## 4. Estatísticas de fase (`core/stats`)

Struct pequena, zerada em `startPhase` (e no restart pós-game-over):

```c
typedef struct {
    u16 bombsUsed;      // BOMB_use incrementa
    u16 damageTaken;    // hook onde o HP do jogador diminui (actors/player.c)
    u32 frames;         // conta em updatePlay (fora do congelamento de 3 s)
    bool objFailed;     // OBJECTIVE_update devolveu OBJ_LOST
} PhaseStats;
```

Fica pronta para condições futuras (itens coletados, precisão, vida do NPC…)
sem tocar no grafo — só adicionar campo + `COND_*` novo.

## 5. Mapa de rotas (tela nova, `screens/routemap.c`)

Estilo Darius: mostrado **após "FASE CONCLUIDA!"** e antes da preparação da
próxima fase (e também acessível na pausa, se couber).

- Desenha os nós a partir de `mapCol/mapRow` do próprio grafo (caixinhas de
  texto com o `name`) e as ligações a partir das `exits` — o mapa **nunca
  desatualiza** em relação ao fluxo, porque é gerado dos mesmos dados.
- Destaque: caminho já percorrido (bitmask `visited`, `u32` cobre até 32 nós),
  nó atual piscando, próximos nós visíveis; ramos não visitados aparecem
  apagados (planta a curiosidade do replay).
- Custo de VRAM baixo: texto + meia dúzia de tiles de linha/caixa em PAL0.
- Pequena animação: o cursor "anda" do nó concluído para o próximo (~1 s),
  então A/START segue para a preparação.

A preparação também mostra o nome ("FASE 2A") — troca de `sprintf("FASE %d")`
por `sprintf("FASE %s", node->name)`.

## 6. Impactos no código atual

| Onde | Hoje | Vira |
|---|---|---|
| `flow.c` (3 lugares) | `(currentLevel % LEVEL_COUNT) + 1` | resolução de saída no grafo (`GRAPH_resolve(node, &stats)`) |
| identidade da fase | `currentLevel` 1..16 | `currentNode` (índice no grafo); `currentLevel == 0` continua sendo a fase teste |
| fim do jogo | `currentLevel == LEVEL_COUNT` + `bossDefeated` | nó sem saídas (`exitCount == 0`) |
| game over | recomeça `currentLevel` | recomeça `currentNode` (igual) |
| debug A+B+C / C na preparação | próxima fase linear | segue a saída `SENAO` do nó atual |
| `LEVEL_drawInfo` / pausa / prep | `"FASE %d"` | `"FASE %s"` (nome do nó) |
| `LEVEL_typeLastPhase()` (descarte de arte na VRAM) | "última fase linear em que o tipo aparece" | **alcançabilidade**: por nó, bitmask dos tipos usados em algum nó alcançável a partir dele (DFS único no boot; grafo é minúsculo). `ENEMYGFX` descarta tipos fora da máscara do nó atual |
| fases teste (`levels/test.c`) | fora da campanha | inalteradas |

## 7. Etapas de implementação

1. **Infra sem mudança de jogo** ✅ (27/08/2026): `graph.h`/`graph.c`
   replicando o fluxo linear atual (16 nós, todas as saídas `SENAO`); `flow.c`
   navega pelo grafo; `core/stats.c` coletando. Adiantado da etapa 2: o
   avaliador de condições (`GRAPH_resolve`), a rota de falha no `flow.c`
   (`GRAPH_hasFailExit`) e o nome do nó na preparação/pausa ("FASE %s") já
   estão prontos — a etapa 2 vira só dados (defs novas + tabela).
2. **Condições + primeira bifurcação** ✅ (27/08/2026): def nova `LEVEL02B`
   (lama cedo, rota de quem gastou bomba) e a bifurcação 1→2A/2B na tabela;
   rota de falha com mensagem própria ("A MISSAO CONTINUA...").
3. **Mapa de rotas** ✅ (27/08/2026): tela `routemap.c` gerada do grafo,
   bitmask `visited`, inserida no fluxo `ST_DONE → ST_MAP → preparação`.
   Simplificações: marcador da próxima fase pisca (sem animação de cursor
   andando); mapa ainda não acessível pela pausa.
4. **VRAM por alcançabilidade** ✅ (27/08/2026): `LEVEL_typeLastPhase` saiu;
   `GRAPH_reachableTypes(n)` (DFS memoizado com guarda de ciclo) dá a
   máscara de tipos alcançáveis, e o `pickSlot` do enemygfx descarta por
   ela (fase teste continua com `phase=0xFF` = máscara vazia).
5. **Design das rotas** ✅ (27/08/2026): fase 5 virou PROTEGER (aliado, 30 s)
   com 6B = retirada via `OBJ_FALHOU` (spawn 2 s, música tensa); 9→10A/10B
   por SEM_DANO (10B = lava+lama); 12→13A/13B por TEMPO_MENOR **60 s**
   (13B = lama; o limiar considera que 30 kills a 2/3 s levam ≥45 s só de
   spawn). 3A/3B do esboço original ficou de fora (a malha já tem 4
   bifurcações; adicionar é só editar a tabela). **Balancear jogando.**

Cada etapa compila e roda sozinha; dá para parar em qualquer ponto com o jogo
funcional.
