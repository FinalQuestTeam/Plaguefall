# Plano: sistema de história (diálogos entre fases)

> Decisões de design (27/08/2026): retratos **novos de 48×48** (char-maps, a
> técnica de arte do projeto); **máquina de escrever** com A avança / START
> pula a cena; cena toca **só na primeira chegada** do run; texto em
> **MAIÚSCULA SEM ACENTO** (fonte atual, padrão da era).

## 1. Conceito

Diálogos estilo 16-bit (Streets of Rage 3 / MUSHA) **entre** as arenas — nunca
durante a ação. Cada cena é uma sequência de falas alternando dois cantos:

```
+--------------------------------------+
| [RETRATO]  REX:                      |
| [ 48x48 ]  ONDE ESTOU? ESTE SETOR    |
| [ESQ/topo] ESTA INFESTADO...         |
|                                      |
|                                      |
|      COMANDO:            [RETRATO]   |
|      REX, OS INSETOS     [ 48x48 ]   |
|      TOMARAM A BASE!     [DIR/baixo] |
+--------------------------------------+
```

O falante ativo fica em destaque (o outro esmaece / só o balão ativo aparece);
as mensagens **intercalam** os dois cantos na ordem escrita no roteiro.

**A regra de ouro: história é amarrada ao NÓ do grafo, não ao "número da
fase".** Cada nó pode ter uma cena de **ANTES** (ao chegar, antes da tela de
preparação) e uma de **DEPOIS** (ao vencer, antes do mapa de rotas). Com isso
as rotas contam histórias diferentes de graça: a 6B "retirada" abre lamentando
a torre perdida, a 2B alfineta o uso da bomba, o DEPOIS da 15 prepara o chefe.
É o que transforma as bifurcações de mecânica em narrativa.

## 2. O arquivo único de roteiro: `levels/story.c`

Mesma filosofia do `graph.c`: um arquivo, vocabulário em português, manual no
cabeçalho. O roteirista escreve a fala corrida — a quebra de linha na caixa é
automática (por palavra, na largura da caixa).

```c
// ---- CENA: chegada na fase 1 -------------------------------------------
CENA(abertura)
    ESQUERDA(P_REX,     "ONDE ESTOU? ESTE SETOR ESTA INFESTADO DE INSETOS.")
    DIREITA(P_COMANDO,  "REX, ELES TOMARAM A BASE! LIMPE A AREA, SETOR POR SETOR.")
    ESQUERDA(P_REX,     "PODE DEIXAR. NENHUM INSETO VAI SOBRAR.")
FIM

// ---- CENA: a torre caiu (chegando na retirada) -------------------------
CENA(retirada)
    DIREITA(P_COMANDO,  "PERDEMOS A TORRE... ELES ESTAO EM CIMA DE VOCE!")
    ESQUERDA(P_REX,     "ENTAO EU ABRO CAMINHO NA MARRA.")
FIM

// ---- ONDE cada cena toca (nó do grafo + momento) -----------------------
const StoryEntry STORY[] =
{
    QUANDO(N_1,  ANTES,  abertura),
    QUANDO(N_6B, ANTES,  retirada),
    QUANDO(N_15, DEPOIS, rumo_ao_chefe),
    QUANDO(N_16, DEPOIS, final),
};
```

- `ESQUERDA(retrato, "fala")` / `DIREITA(retrato, "fala")` — o canto define
  quem fala; a ordem das linhas é a ordem da conversa (intercala como quiser).
- O **retrato é escolhido POR FALA** — é o controle de troca de sprite pedido:
  o mesmo personagem pode trocar de expressão no meio da cena
  (`P_REX` → `P_REX_BRAVO`), ou entrar um terceiro personagem no mesmo canto.
- Um nó pode ter cena de ANTES, de DEPOIS, as duas ou nenhuma; a tabela
  `QUANDO(...)` no fim do arquivo é o índice de tudo.

### Estruturas (novas, em `levels/story.h`)

```c
typedef struct { u8 side; u8 portrait; const char *text; } StoryLine;
typedef struct { u8 node; u8 when; const StoryLine *lines; u8 count; } StoryEntry;
```

## 3. Retratos 48×48 (`system/video/sprites/portraits_data.h`)

Mesma técnica de toda a arte do jogo: **char-map em texto** — 48 linhas de 48
caracteres hex, 1 paleta de 16 cores por retrato, '0' = transparente. Editável
num editor de texto com o gabarito comentado; e o mesmo caminho offline usado
em `img/char.jpg → chars_data.h` (script de derivação) serve para converter
uma imagem desenhada fora.

- Registro: `enum { P_REX, P_REX_BRAVO, P_COMANDO, P_LACRAIA, ... }` +
  `PORTRAIT_NAME[]` (o nome aparece sobre o balão: "REX:").
- **VRAM**: 48×48 = 36 tiles; 2 retratos na tela = 72 tiles por cena. Gerados
  **sob demanda** ao abrir a cena, numa região emprestada (candidata natural:
  `BOSS_ROT`, 288 tiles, livre fora da fase do chefe — o cache do `ENEMYGFX`
  já sabe se invalidar via `resident[]`/`ENEMYGFX_reset`). Sem custo residente.
- **Paletas**: a tela de história é exclusiva (sem jogo atrás), então PAL2 e
  PAL3 ficam livres para os dois retratos (1 paleta cada); PAL0 segue no
  texto. Ao sair, recarregar as paletas do jogo (chão/jogador) — mesmo padrão
  que o título já usa ao devolver a VRAM.

## 4. Motor da cena (`system/video/screens/story.c`)

- **Máquina de escrever**: ~2 letras/quadro, com blip curto de PSG a cada N
  letras (respeitando o árbitro de áudio). A com fala em curso → completa a
  fala; A com fala completa → próxima; **START pula a cena inteira**.
- **Quebra automática**: por palavra, caixa de ~26 colunas × 4 linhas (≈100
  caracteres por fala — falas mais longas são erro de roteiro, avisar no log
  de build futuramente; por ora, corta com reticências).
- Indicador "▼" piscando quando a fala terminou (convenção do gênero).
- Nome do falante em cima do balão; retrato inativo esmaecido (ou só o balão
  do ativo visível — decidir no primeiro protótipo visual).

## 5. Integração no fluxo (`core/flow.c`)

Novo estado `ST_STORY`, sempre **entre** telas já existentes:

- **ANTES**: `mapa de rotas → HISTORIA(nó, ANTES) → preparação`
  (fase 1, sem mapa antes: `título → HISTORIA → preparação`).
- **DEPOIS**: `"FASE CONCLUIDA!" (ou falha roteada) → HISTORIA(nó, DEPOIS) →
  mapa de rotas`.
- **Uma vez por run**: bitmask `seen` (u32 por momento, como o `visited` do
  mapa), zerada no novo jogo. Morrer e recomeçar **não** repete a cena de
  ANTES. START pula mesmo na primeira vez.
- Fase teste: sem história (sandbox intocado).

## 6. Etapas de implementação — ✅ TUDO IMPLEMENTADO (27/08/2026)

Notas da implementação: as 4 etapas abaixo foram feitas de uma vez. O blip da
máquina de escrever reusa o `sfxItemPickup` (canal 2); os retratos usam PAL2
(esq.) e PAL3 (dir.), restauradas automaticamente pelo início de fase
(`CHARS_load`/`FLOOR_draw`); a região do chefe é invalidada por
`ENEMYGFX_dropBoss()` ao fim de cada cena. Roteiro de demonstração com 7
cenas em `levels/story.c` (abertura, 2A, 2B, 6B, pós-15, pré-chefe, final).
Os retratos foram gerados por script (procedurais) e podem ser refinados à
mão direto no char-map de `portraits_data.h`.

1. **Motor + dados com retrato provisório**: `story.h`/`story.c` (roteiro e
   registro), `screens/story.c` (layout, quebra de linha, máquina de
   escrever, A/START) usando arte existente (mech/inseto) como retrato — 
   valida a tela inteira sem depender de arte nova.
2. **Integração no fluxo**: `ST_STORY` nos dois pontos, bitmask `seen`,
   reset no novo jogo; cena de exemplo na fase 1 (ANTES) e no chefe (DEPOIS).
3. **Pipeline de retratos 48×48**: `portraits_data.h` + gabarito comentado
   (e/ou derivação offline de imagem), geração na VRAM emprestada, paletas;
   troca dos provisórios.
4. **Conteúdo**: escrever o roteiro do run — sugestão de cobertura mínima:
   abertura (1 ANTES), uma cena por bifurcação nas rotas B (2B/6B/10B/13B
   ANTES — são as que dão sabor às rotas), rumo ao chefe (15 DEPOIS) e final
   (16 DEPOIS). ~7 cenas curtas (3 a 5 falas cada).

Cada etapa compila e roda sozinha, como nos planos anteriores.

## 7. Riscos e princípios de ritmo

- **Cena curta é cena boa**: 3–5 falas. O jogador está entre duas arenas — a
  história tempera, não interrompe.
- **Sempre pulável** (START), inclusive na primeira vez — replay das rotas é
  o coração do jogo e ninguém pode ficar refém do texto.
- Texto em MAIÚSCULA SEM ACENTO ("VOCE", "ENTAO") — consistente com todo o
  resto do jogo e com a era.
- VRAM emprestada do chefe exige cuidado na fase 16 (a cena DEPOIS do chefe
  acontece com o chefe já fora de cena — sem conflito; a de ANTES do 16, se
  existir, deve rodar antes do `LEVEL_loadGfx`, que é a ordem natural do
  fluxo de qualquer forma).
