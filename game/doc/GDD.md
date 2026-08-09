# RedRex — Game Design Document (GDD)

> **Plataforma:** Sega Mega Drive / Genesis · **Engine:** SGDK 2.11 (C, m68k-elf)
> **Gênero:** shooter de arena top-down, sobrevivência por fases
> **Documento gerado a partir do código-fonte** (`game/src/`) — os valores refletem a implementação real.
> Tempos convertidos assumindo **60 fps (NTSC)**; em PAL (`fps` = 50) as cadências se ajustam automaticamente.

---

## Sumário

1. [Visão geral, controles, fluxo e HUD](#1-visão-geral-controles-fluxo-e-hud)
2. [Jogador, tiros, bomba e inventário](#2-jogador-tiros-bomba-e-inventário)
3. [Inimigos](#3-inimigos)
4. [Itens](#4-itens)
5. [Fases e elementos de terreno](#5-fases-e-elementos-de-terreno)
6. [Áudio e gráficos (técnico)](#6-áudio-e-gráficos-técnico)

---

# 1. Visão geral, controles, fluxo e HUD

## Visão geral

**RedRex** é um shooter de arena *top-down* para Mega Drive. O jogador pilota um **mech 32×32** (hitbox 16×16) numa arena de tela única, eliminando insetos-máquina que surgem em ondas. Em cada fase da campanha o objetivo é **matar N inimigos** (`killTarget`); na **fase 16**, o objetivo é **derrotar o chefe Lacraia** — vencê-lo mostra a tela de fim ("PARABENS! FIM") e volta ao título.

A arena ocupa a tela inteira; a linha 0 de tiles é o HUD.

| Dimensão | Valor (tiles) | Valor (pixels) |
|---|---|---|
| Largura da arena (`ARENA_TILES_W`) | 40 | 320 |
| Altura da arena (`ARENA_TILES_H`) | 27 | 216 |
| Origem da arena (`ARENA_TILE_X`, `ARENA_TILE_Y`) | (0, 1) | (0, 8) |

Limites internos de movimento (dentro da borda de parede): `INNER_MIN_X` = 8, `INNER_MIN_Y` = 16, `INNER_MAX_X` = 311, `INNER_MAX_Y` = 215.

## Controles

Só o Joypad 1 (`JOY_1`) é lido. Comandos de menu/itens usam **detecção de borda** (comparação com `prevJoy`).

| Botão | Em jogo (`ST_PLAY`) | Em telas |
|---|---|---|
| D-pad | Move nas 8 direções | Navega no menu / troca página da ajuda |
| A | Atira (segurar = autofire na cadência) | Começa a fase (preparação) / confirma |
| B | **Ativa** o item selecionado do inventário | Sai ao título (pausa) |
| C | **Troca** a seleção do inventário | Avança a fase (preparação) |
| START | Pausa / retoma | Confirma (game over → recomeça a fase; tela de fim → título) |
| A+B+C (segurar) | **(Debug)** pula para a próxima fase (uma vez por combo) | — |

## Fluxo e estados do jogo

Máquina de estados em `core/flow.c` (a tela-título roda antes do laço, em `title.c`):

| Estado | Descrição |
|---|---|
| `ST_PREP` | Preparação: "FASE n", meta, intervalo de spawn e os **sprites** dos inimigos da fase. A começa; C avança de fase. |
| `ST_PLAY` | Jogo ativo (inclui a contagem "PREPARE-SE" de 3 s congelada). |
| `ST_PAUSE` | Pausa: infos da fase; START retoma, B sai ao título. |
| `ST_OVER` | Game over: START **recomeça a fase atual** com vida/bombas restauradas. |
| `ST_DONE` | "FASE CONCLUIDA!" por 3 s antes da preparação da próxima fase. |
| `ST_END` | Fim de jogo (chefe derrotado): "PARABENS! FIM"; START volta ao título. |

### Fluxo geral

1. **Splash** (logo FinalQuest) → **Tela-título** (fundo em bitmap-art + menu: **NOVO JOGO / FASE TESTE / COMO JOGAR**).
2. **Preparação** (`ST_PREP`) → A para começar.
3. **"PREPARE-SE 3-2-1"** (3 s congelado) → jogo ativo.
4. Meta atingida → `ST_DONE` → preparação da próxima. Morte → `ST_OVER` → recomeça a mesma fase.
5. **Fase 16**: o chefe é gerado no início; derrotá-lo → `ST_END` → título.

### Temporizações (60 fps NTSC)

| Evento | Código | Segundos |
|---|---|---|
| Congelamento "PREPARE-SE" | `fps * 3` | 3 s |
| Primeiro inimigo (`FIRST_SPAWN_S`) | `1 * fps` | 1 s após o congelamento |
| "FASE CONCLUIDA!" (`doneTimer`) | `fps * 3` | 3 s |
| Intervalo entre ondas | `spawnSeconds * fps` | por fase (2–5 s) |

### Persistência

- **Entre fases**: HP, cargas de bomba, itens do inventário e bônus acumulados (leque de balas, velocidade) **persistem**.
- **No game over**: vida cheia (`PLAYER_fullHp`), bombas ao máximo (`BOMB_reset`), inventário esvaziado (`INV_clear`), potência de tiro/raio/velocidade zerados.
- Cura tem **teto de 100 HP**.

## Tela-título, splash e ajuda

- **Splash** (`splash.c`): logo da desenvolvedora (FinalQuest) recriado por char-map.
- **Título** (`title.c`): arte de fundo em tile-art derivada de `src/img/bg.jpg` (`titlebg_data.h`, 2 paletas de 16 cores por cluster de tiles) + menu **NOVO JOGO / FASE TESTE / COMO JOGAR**. A música dark toca calma aqui (ver Áudio).
- **Como Jogar** (`help.c`): **5 páginas** navegáveis com ←/→ — controles, inimigos (cor/forma, com os sprites reais), a elite (pentágonos), itens diretos e itens de inventário.

## HUD (linha 0)

| Coluna | Elemento | Fonte |
|---|---|---|
| 1–8 | Caveira + `kills/killTarget` | `HUD_drawKills` |
| 14–25 | **Inventário**: 4 posições × 3 colunas (`>` cursor, ícone 8×8, contagem) | `HUD_drawInventory` |
| 27–28 | **Modo de tiro ativo** (raio/gelo/fogo): ícone + cargas restantes | idem |
| 33–39 | `HP:xxx` | `HUD_drawLife` |

O inventário é redesenhado **só quando o estado muda** (`HUD_drawInventoryIfDirty`, assinatura do estado) — economiza escritas de VDP por quadro.

---

# 2. Jogador, tiros, bomba e inventário

## O jogador

Mech **32×32** (sprite, PAL2, 8 direções — encara a direção do movimento) com **hitbox 16×16**. Movimento em **fixed-point 26.6**. Só **3 direções** são geradas na VRAM (N/NE/E); as outras 5 saem por **espelhamento de hardware** (H/V-flip) — ver §6.

| Parâmetro | Constante | Valor |
|---|---|---|
| Velocidade base | `PLAYER_SPEED` | 2 px/frame |
| Vida inicial / teto | `PLAYER_START_HP` | 100 |
| Invencibilidade pós-dano | `PLAYER_INV_TENTHS` | 0,3 s (pisca a cada 4 frames) |
| Cadência de tiro | `PLAYER_FIRE_TENTHS` | 0,8 s (1,25 tiros/s) |
| Bônus da botinha | `PLAYER_SPEED_STEP` / `PLAYER_SPEED_MAX` | +20% por item, teto +100% (dobro) |
| Escudo (item) | `PLAYER_SHIELD_TENTHS` | 3,0 s de invencibilidade total |

Rotinas de dano:

| Função | Respeita invencibilidade? | Uso | Som |
|---|---|---|---|
| `damagePlayer(dmg)` | Sim | Contato e projétil de **inimigo** | `SFX_playerHit` (tom grave descendente) |
| `loseHp(dmg)` | Não | Ambiente (lava) | só o crepitar ambiente |

A direção de tiro (`faceX/faceY`) segue a última direção pressionada (8 direções); inicial = direita.

## Tiros do jogador

| Propriedade | Valor |
|---|---|
| Velocidade (`PSHOT_SPEED`) | 3 px/frame |
| Máx. simultâneos (`MAX_PSHOTS`) | 16 |
| Potência (leque) | 1 a `SHOTS_MAX_POWER` = 5 balas por disparo (item bala) |
| Abertura do leque | cisalhamento `SHOTS_ARC_SHEAR` = 8 |
| Origem | boca do mech (`PSHOT_MUZZLE_FWD` = 13 px à frente, 5 px à direita) |
| Dano | 1 por bala (HP dos inimigos é medido em tiros) |

**Modos de tiro** (ativados pelo inventário; a carga é consumida **a cada disparo**, mesmo errando):

| Modo | Cargas | Efeito no inimigo atingido |
|---|---|---|
| `SHOTMODE_CHAIN` (raio) | 5 acertos | Reação em cadeia: até **3 inimigos** num raio de **80 px**, com arcos elétricos visuais |
| `SHOTMODE_ICE` (gelo) | 3 tiros | **Congela por 5 s** (parado, sem dano de contato; overlay ciano contínuo) |
| `SHOTMODE_FIRE` (fogo) | 4 tiros | **Queimadura por 6 s**: 1 de dano a cada 2 s. A cada tique, o inimigo dá um **pulso vermelho sólido** (feedback) |

## Tiros inimigos

Fixed-point 26.6, mirados no centro do jogador no instante do disparo (`getApproximatedDistance` normaliza).

| Propriedade | Valor |
|---|---|
| Velocidade (`ESHOT_SPEED`) | 2 px/frame |
| Máx. simultâneos (`MAX_ESHOTS`) | 16 |
| Dano padrão (`ESHOT_DAMAGE`) | 10 (o chefe atira com 13) |
| Colisão | círculo: `dx²+dy² ≤ 100` (raio 7 do jogador + 3 do tiro) |

## Bomba

- Teto **`BOMB_MAX` = 3 cargas**; começa com o máximo. Item de bomba dá +1 (respeitando o teto).
- **Uso**: pelo inventário (posição 0, botão B). Consome 1 carga, toca `SFX_bombBlast`, dispara o **flash de tela** e mata **todos os inimigos comuns** (`ENEMIES_killAll`), sem drops; as mortes **contam para a meta**.
- **O chefe resiste à bomba**: sofre só **4 de dano** (`BOMB_BOSS_DMG`), nunca morre pela bomba (fica com no mínimo 1 HP) e **não sofre nada se estiver blindado**.

## Inventário (`core/inventory.c`)

**4 posições selecionáveis**: a posição **0 é a bomba** (mostra as cargas) e as posições **1–3 guardam itens de inventário** coletados (raio, escudo, gelo, fogo — a bomba coletada vira carga). Duplicatas ocupam posições separadas.

- **C** = seleciona a próxima posição (cíclico); **B** = ativa a posição selecionada.
- Ativar raio/gelo/fogo liga o **modo de tiro** correspondente (aparece no HUD com as cargas); ativar o escudo dá 3 s de invencibilidade; ativar a bomba explode.
- Começa **vazio** (só as bombas); esvaziado a cada novo jogo e no game over.

---

# 3. Inimigos

## A matriz forma × cor

Cada inimigo combina uma **forma** (perfil de resistência) com uma **cor** (comportamento). Todos são insetos-máquina com arte própria (besouro/mosca/aranha) que **encara o jogador** nas 8 direções — 3 geradas, 5 espelhadas por hardware (§6).

| | **Vermelho** (atira) | **Amarelo** (persegue) | **Roxo** (escudo cíclico) | **Laranja** (investida) |
|---|---|---|---|---|
| **Quadrado** (resistente) | Torreão | Batedor | Baluarte | Aríete |
| **Triângulo** (frágil/veloz) | Fuzileiro | Caçador | Escudeiro | Adaga |
| **Pentágono** (elite + truque) | Artilheiro (leque) | Alcateia (divide) | Fortaleza (invoca) | Meteoro (teleporta) |

## Tabela completa (valores dos `defs/*.c`)

Velocidade em unidades 26.6 por frame (`ENEMY_SPEED_FP` = 40 ≈ 0,63 px/frame). Vida em tiros para morrer.

| Inimigo | Tam. (px) | HP | Dano contato | Drop % | Velocidade | Timers / truque |
|---|---|---|---|---|---|---|
| **Torreão** (SQ vermelho) | 16 | 3 | 8 | 45% | 0 (fixo) | atira a cada 2,0 s |
| **Batedor** (SQ amarelo) | 16 | 3 | 8 | 40% | 40 | — |
| **Baluarte** (SQ roxo) | 32 | 6 | 15 | 75% | 20 | escudo: 2,5 s vulnerável / 2,0 s blindado |
| **Aríete** (SQ laranja) | 16 | 4 | 12 | 45% | 20 | investida, cooldown 1,5 s |
| **Fuzileiro** (TRI vermelho) | 16 | 1 | 6 | 20% | 55 | move e atira a cada 1,0 s |
| **Caçador** (TRI amarelo) | 16 | 1 | 8 | 20% | 90 (o mais veloz) | — |
| **Escudeiro** (TRI roxo) | 16 | 2 | 10 | 30% | 50 | escudo: 1,2 s / 0,8 s (curto e frequente) |
| **Adaga** (TRI laranja) | 16 | 1 | 10 | 25% | 40 | investida, cooldown 0,8 s |
| **Artilheiro** (PEN vermelho) | 24 | 3 | 10 | 60% | 0 (fixo) | **leque de 3 tiros** a cada 2,5 s |
| **Alcateia** (PEN amarelo) | 24 | 3 | 10 | 55% | 35 | ao morrer, **divide-se em 2 Caçadores** |
| **Fortaleza** (PEN roxo) | 32 | 4 | 15 | 80% | 15 | escudo 2,0 s / 2,5 s; **invoca 1 Caçador a cada 1,5 s enquanto blindado** |
| **Meteoro** (PEN laranja) | 24 | 3 | 14 | 60% | 20 | **teleporta para perto** antes de investir; cooldown 1,8 s |
| **Dummy** (teste) | 24 | 20 | 0 | 0% | 0 | alvo da fase teste 1 |
| **Alvo** (teste) | 24 | 1 | 0 | 0% | 0 | alvos do raio na fase teste 2 |
| **Lacraia** (CHEFE) | **48** | **25** | **20** | 100% | 32 | ver abaixo |

### Comportamentos por cor

- **Vermelho** (`enemy_red.c`): persegue se `speedFp > 0`; dispara mirado no jogador a cada `timerA` décimos de s. Com `EXTRA_SPREAD` dispara **leque de 3**. Primeiro tiro escalonado (`ENEMY_CD/2 + random % fps`) para dessincronizar.
- **Amarelo** (`enemy_yellow.c`): perseguição pura (`ENEMIES_chase`). Com `EXTRA_SPLIT`, ao morrer gera 2 Caçadores no lugar.
- **Roxo** (`enemy_purple.c`): persegue e alterna escudo — `timerA` s vulnerável / `timerB` s blindado. Blindado: **bloqueia tiros** (pisca para sinalizar) e é imune à cadeia/bomba. Com `EXTRA_SUMMON` invoca Caçadores enquanto blindado.
- **Laranja** (`enemy_orange.c`): aproxima → **telegrafa 0,2 s** (para mirando) → **investida reta 0,5 s a ~3,1 px/frame** (`DASH_SPEED_FP` = 200) → cooldown `timerA`. Com `EXTRA_TELEPORT`, pisca para um ponto próximo do jogador antes do bote.

## O chefe: Lacraia (`enemy_boss.c`)

Centopeia vermelha **48×48** (arte própria `INS_BOSS48`, desenhada como 4 sprites de 24×24). Aparece na **fase 16** (e na arena de teste, estágio 3). Contador mestre `tA` dirige todos os ciclos:

| Mecânica | Valor |
|---|---|
| Vida | 25 tiros |
| Dano de contato | 20 · Dano do tiro: **13** |
| **Blindagem cíclica** | invulnerável **3 s a cada 15 s** (12 s vulnerável) |
| **Invocação** | 2 Caçadores a cada **10 s** |
| **Alternância de modo** | a cada **4 s**: agressivo ↔ à distância |
| Modo agressivo | aproxima e usa **dash** (telegrafa e investe a `BOSS_DASH_FP` = 210) |
| Modo à distância | **recua** do jogador e dispara **leque de 5 tiros** (dano 13) a cada ~1,2 s |
| Resistência à bomba | sofre 4 (nunca morre por bomba; 0 se blindado) |
| Ao morrer | poça de sangue, drop garantido, `bossDefeated` → tela de fim |

## Mecânicas comuns (engine `enemies.c`)

- **Capacidade**: vetor de `MAX_ENEMIES` = 16; spawn regular só até `ENEMY_CAP` = 15 ativos (Alcateia/Fortaleza podem estourar até 16 ao dividir/invocar).
- **Spawn** (`ENEMIES_trySpawn`): sorteia o tipo do roster da fase; até 12 tentativas de posição com distância **≥ 56 px do jogador**.
- **Perseguição** (`ENEMIES_chase`): re-mira a cada `RETARGET_FRAMES` = 16 frames; entre re-miras só integra a velocidade (barato). Lentidão da lama aplicada por %.
- **Separação anti-empilhamento** (`ENEMIES_separate`): a cada 2 quadros (30 Hz), pares muito próximos recebem empurrões opostos — normalização por **tabela de recíprocos** (sem divisão no laço, regra do 68000).
- **Contato + knockback**: AABB contra a hitbox 16×16 do jogador; aplica o dano (com i-frames) e o inimigo móvel **recua a 2× a velocidade por 1/3 s** (stun). Fixos não recuam.
- **Congelado**: parado, sem comportamento nem dano de contato, **overlay ciano contínuo**.
- **Queimando**: 1 de dano a cada 2 s por 6 s; a cada tique dá um **pulso vermelho sólido**; mortes pela queimadura contam para a meta.
- **Feedback de dano**: ao sobreviver a um acerto (tiro/raio), o inimigo **brilha branco** por ~4 frames (`hitFlash`).
- **Morte** (`enemyDie`): poça de **sangue verde** no chão, sorteio de drop, divisão (Alcateia), flag do chefe.
- **Raio em cadeia** (`ENEMIES_chainDamage`): a partir do acerto, até 3 alvos em 80 px (blindados são imunes); arcos elétricos visuais.

> **Overlays de status** (gelo/fogo) e os **flashes** (branco de dano, vermelho de fogo) reaproveitam um único tile de xadrez (`TILE_STATUS`); a **cor vem da paleta** (PAL1 ciano, PAL0 branca/vermelha) — zero tiles extras. Detalhes em §6.

---

# 4. Itens

Itens caem de inimigos mortos **por tiro/queimadura** (a bomba não gera drops). Dois sorteios: **(1)** cai ou não — `dropChance` do tipo de inimigo (tabela acima); **(2)** qual item — proporcional ao `weight` de cada `ItemDef` (a soma não precisa dar 100).

## Tipos, pesos e efeitos

| Item | Peso | Categoria | Efeito |
|---|---|---|---|
| **Coração** | 40 | direto | Cura 15 HP (teto 100) |
| **Bomba** | 20 | inventário (vira carga) | +1 carga (teto 3) |
| **Bala** | 10 | direto | +1 bala no leque (até 5 por disparo) |
| **Botinha** | 10 | direto | +20% de velocidade (teto +100%) |
| **Escudo** | 5 | inventário | Ao ativar: invencível por 3 s (imune até a lava) |
| **Raio** | 5 | inventário | Ao ativar: próximos 5 acertos fazem cadeia (3 alvos, 80 px) |
| **Gelo** | 5 | inventário | Ao ativar: próximos 3 tiros congelam por 5 s |
| **Fogo** | 5 | inventário | Ao ativar: próximos 4 tiros aplicam queimadura (6 s, 1 dano/2 s) |

Soma dos pesos = 100 (coincidência atual; o sorteio usa a soma real).

## Regras de chão

- Máx. **8 itens** ativos (`MAX_ITEMS`); sem slot → o drop é perdido.
- **TTL de 10 s**; pisca nos últimos 2 s.
- Coleta automática por AABB 16×16; toca `sfxItemPickup` (blip ascendente).
- **Itens diretos** aplicam o efeito na hora; **itens de inventário** vão para uma posição livre (1–3). Inventário cheio: o item é consumido sem efeito.
- Arte 16×16 por char-map (`items_data.h`), pintada em `ITEMS_buildTiles`.

---

# 5. Fases e elementos de terreno

## Estrutura

`LEVEL_COUNT` = **16** (1–15 campanha + 16 = chefe). Cada fase é um `LevelDef` (dados puros) em `levels/defs/levelNN.c`: terreno (`lava`/`mud`, retângulos em tiles), `killTarget`, `spawnSeconds`, `spawnCount`, o **roster** de tipos, o **chão** (`floor`) e a **curva de música** por fase (`musCalmUntil`/`musEnemyMax`/`musStepCalm`/`musStepHot`; ver §6). A arte dos inimigos do roster é gerada **por fase** na VRAM (ver §6).

## Tabela das fases

| Fase | Meta | Spawn (s) | Por onda | Terreno | Chão | Roster |
|---|---|---|---|---|---|---|
| 1 | 10 | 5 | 1 | — | pedra | Torreão, Batedor |
| 2 | 12 | 5 | 1 | — | pedra | + Aríete |
| 3 | 14 | 4 | 1 | Lava | pedra | Batedor, Baluarte, Aríete |
| 4 | 16 | 4 | 1 | Lama | floresta | Torreão, Baluarte, **Caçador** |
| 5 | 18 | 4 | 1 | — | pedra | **Fuzileiro**, Caçador, Aríete |
| 6 | 20 | 3 | 1 | Lava | pedra | Fuzileiro, Caçador, **Adaga** |
| 7 | 22 | 3 | **2** | Lama | floresta | Caçador, **Escudeiro**, Baluarte |
| 8 | 24 | 3 | 2 | Lava | pedra | Fuzileiro, Caçador, Adaga, Aríete |
| 9 | 24 | 4 | 1 | — | pedra | **Artilheiro, Alcateia**, Caçador |
| 10 | 26 | 3 | 2 | Lama | floresta | Alcateia, **Meteoro**, Adaga |
| 11 | 28 | 3 | 2 | Lava+lama | mix | Artilheiro, **Fortaleza**, Caçador |
| 12 | 30 | 3 | 2 | Lava+lama | mix | Meteoro, Fuzileiro, Caçador, Baluarte |
| 13 | 34 | 2 | 2 | Lava | pedra | Baluarte, Caçador, Adaga, Artilheiro, Alcateia |
| 14 | 37 | 2 | **3** | Lava+lama | mix | Fortaleza, Meteoro, Alcateia, Caçador |
| 15 | 40 | 2 | 3 | Lava+lama | mix | Aríete, Fuzileiro, Caçador, Adaga, Artilheiro, Fortaleza, Meteoro |
| **16** | **chefe** | — | — | — | caverna | **Lacraia** (+ Caçadores invocados) |

Layouts de terreno (`layouts.c`, retângulos em tiles): `LAVA_PAIR` {5,6,10×6}+{25,15,10×6}, `MUD_PAIR` {6,15,10×6}+{24,5,10×6}; combos (fases com os dois) usam retângulos 8×5 em cantos opostos.

## Chão da arena (`floor.c`, campo `LevelDef.floor`)

Char-map 32×32 ladrilhado no **BG_B** (PAL3), escolhido por fase. Todas as variantes ficam residentes na VRAM (48+32 tiles):

| Variante | Uso | Visual |
|---|---|---|
| `FLOOR_STONE` (padrão) | fases sem lama | pedra escura (basketweave) |
| `FLOOR_FOREST` | fases de lama só | grama, terra, folhas, pedrinhas |
| `FLOOR_CAVE` | covil do chefe (16 / teste 3) | rocha úmida/arenosa |
| `FLOOR_MIX` | fases **lava+lama** | **rocha na arena + grama ao redor da lama** |

O **`FLOOR_MIX`** desenha dois chões na mesma fase: como o BG_B só tem uma paleta (PAL3), os dois tilesets **dividem 16 cores** (grama + rocha). A grama é pintada nos tiles a até `FLOOR_MIX_MUD_PAD` = 2 tiles de qualquer retângulo de lama; o resto (inclusive o entorno da lava) fica rocha.

Na preparação/pausa, os inimigos do roster aparecem como **sprites reais** alinhados pela base (`LEVEL_drawInfo` → `ENEMYGFX_drawOnMap`); o chefe (48 px) não é mostrado ali.

## Fase teste (sandbox, opção do menu)

3 estágios ligados por **portas** (`levels/test.c`):

1. **Dummies** (HP 20, inofensivos) + fileira com 1 item de cada tipo (reabastecida). Tem **lava + lama** (chão `FLOOR_MIX`), para testar dano/lentidão.
2. **Alvos** frágeis agrupados — demonstra a reação em cadeia do raio. Porta "CHEFE →".
3. **Arena do chefe** — a Lacraia com o comportamento completo (chão de caverna).

## Elementos de terreno

### Lava
Dano **progressivo** enquanto o centro do jogador está em cima: 5/s subindo +5 a cada segundo, teto 25/s (tick de 1 HP com intervalo `fps/dps`). **Ignora i-frames** (é `loseHp`); zera ao sair. Som ambiente de crepitar. Inimigos não são afetados.

### Lama
Lentidão progressiva **individual** (cada entidade acumula seu tempo): jogador **−30% ao entrar + 10%/s, teto −70%** (chega ao teto em ~4 s); inimigos **−3% ao entrar + 3%/s, teto −30%**. Zera ao sair. Som ambiente de passos ("squelch" a cada ~1/3 s).

---

# 6. Áudio e gráficos (técnico)

## Áudio

**Todo o áudio é PSG (SN76489)**, sintetizado em tempo real — sem amostras. Música de fundo e efeitos coexistem nos 4 canais por meio de um **árbitro** central.

> **Por que PSG, e não XGM/PCM:** o driver XGM corrompe a VRAM neste projeto (conflito com o uso intenso de DMA) e o driver PCM/DAC desregula com DMA ativa. O PSG é escrito direto pelo 68000 (sem Z80/DMA), então a música toca de forma estável — daí toda a trilha ser sintetizada no PSG.

### Árbitro (`system/audio/audio.c`)

Única via de escrita no PSG. Música e SFX **não** tocam nos registradores direto: a cada quadro apenas **requisitam** voz (tom ou ruído) com uma **prioridade**; o árbitro escolhe, por canal, o pedido de maior prioridade e escreve o PSG **uma vez por canal**. Isso elimina a antiga disputa por "ordem de escrita" e centraliza as defesas contra chiado: `PSG_setNoise`/frequência só são reescritos **quando mudam** (reescrever o ruído todo quadro reiniciava o gerador → chiado), e o canal ocioso é silenciado uma única vez.

- **Ordem por quadro**: `AUDIO_frameBegin()` → `MUSIC_update()` → `SFX_update()` → `AUDIO_frameEnd()`.
- **Prioridades**: `AMBIENT(1) < MUSIC(4) < SFX(8) < ALERT(12)`.
- **Anti-nota-presa**: `AUDIO_silenceAll()` é chamado antes de toda carga bloqueante (troca de fase, tela de título/pausa) para não deixar uma nota soando durante o intervalo sem quadros; a música retoma sozinha no quadro seguinte.

### Música (`system/audio/music.c` + `song_data.h`)

Chiptune **original**, tom **dark**, em Ré menor harmônico (cadência andaluza Dm–C–Bb–A); sequenciador de **64 passos** (16 × 4 compassos) em loop. Vozes: **melodia** (ch0), **arpejo** (ch1), **baixo** (ch2), **bateria** de ruído (ch3, bumbo + caixa).

**BPM dinâmico por ameaça**: o andamento sobe conforme os inimigos vivos (`MUSIC_setEnemies`), com *glide* suave (sem saltos). A curva é **configurável por fase** no `LevelDef` — `musCalmUntil`, `musEnemyMax`, `musStepCalm`, `musStepHot` (0 em cada campo = usa o padrão global de `music.h`); `startPhase`/`startTest` aplicam via `MUSIC_setRamp`. Padrão: calmo (~75 BPM) até 4 inimigos, subindo até ~225 BPM em 15. O **chefe** (fase 16) já começa acelerado (curva própria). BPM = 900 / frames-por-passo.

### Efeitos (`system/audio/sfx.c`)

Cada evento arma um timer; `SFX_update` requisita a voz ao árbitro com prioridade acima da música (que retoma o canal ao soltar). O **ambiente de terreno** é um **leito de ruído** de prioridade mínima no ch3 — a bateria e o combate passam por cima dele —, o que mantém a **melodia (ch0) sempre limpa** (antes o crepitar era um tom aleatório no ch0, que "roubava" a melodia).

| Função | Canal / prio | Som |
|---|---|---|
| `SFX_playerShot` | 1 (tom) / SFX | Tiro: pitch caindo de ~1400 Hz, 10 frames |
| `sfxItemPickup` | 2 (tom) / SFX | Coleta: blip **ascendente** 600→1400 Hz, 8 frames |
| `SFX_playerHit` | 2 (tom) / ALERT | **Dano sofrido** (só de inimigo): tom **grave descendente** ~300→110 Hz, 14 frames |
| `SFX_enemyShot` | 3 (ruído) / SFX | Ruído branco curto, 8 frames |
| `SFX_bombBlast` | 3 (ruído) / ALERT | Explosão: ruído grave, 30 frames |
| `SFX_ambient` | 3 (ruído) / AMBIENT | Lava (crepitar de ruído trêmulo) / lama (squelch periódico) — leito sob a bateria |

`SFX_silence` zera os timers e chama `AUDIO_silenceAll` (usado nas transições).

## Gráficos

### Arte procedural por char-maps

Não há bitmaps no build (exceto a derivação offline do fundo do título). Toda a arte vem de **char-maps** em `system/video/sprites/*.h`, pintados em tiles 4bpp no boot ou por fase. Os tiles base são só os **70** elementos fixos (projéteis, parede, porta, sombra, `TILE_STATUS`, poça de sangue, itens, ícones); os sprites de personagem/inimigo ficam nas regiões rotacionadas.

- `tilegen.c` — tiles fixos + os ícones 8×8 de `icons_data.h` (caveira, bomba, raio, faísca, escudo, gelo, fogo).
- `chars.c` — mech 32×32 (1 dos 9 personagens carregado por vez), **3 direções geradas** (N/NE/E) + 5 por flip = **48 tiles**; PAL2.
- `enemygfx.c` — insetos, **gerados por fase**, **3 direções** cada + 5 por flip. **Pools por tamanho** com descarte por vida útil: 5 slots de 16 px + 3 de 24 px + 2 de 32 px = **237 tiles** (`ENEMY_ROT_COUNT`). O chefe tem região própria (`BOSS_ROT`, 288 tiles, ainda em 8 direções — quadrantes manuais não flipam).
- `floor.c` — chão 32×32 no **BG_B** (PAL3), 3 variantes simples + 2 tilesets do mix = **80 tiles**.
- `titlebg.c` — fundo do título (índice 0 reservado — no MD ele rende a cor de fundo, não a da paleta).

### Espelhamento de hardware (flip H/V)

Mech e inimigos só geram **3 das 8 direções** (N, NE, E); as outras 5 são reflexões, obtidas ligando os bits `HFLIP`/`VFLIP` do sprite (S=vflip(N), W=hflip(E), NW=hflip(NE), SW=hflip+vflip(NE), etc.). Corta o custo de VRAM dessas rotações em **62%**.

**Orçamento de VRAM**: ~**835** tiles usados no pico de gameplay, de **1408** disponíveis (tilemaps em 0xB000) — ~**570 livres**. Chegou aí removendo ~100 tiles de arte legada (quadrados/base antigos) e adotando o flip. Cargas grandes usam **display desligado** (DMA com display ativo trunca).

### Lista de sprites (`spritelist.c`)

Reconstruída a cada frame, encadeada por link, enviada via `DMA_QUEUE`:

1. **Jogador** (32×32, fixo no link 0 — nunca descartado pelo VDP; usa flip conforme a direção).
2. **Inimigos**, com **rotação de flicker**: a varredura começa em um índice diferente por quadro, distribuindo o descarte do VDP (limite de 20 sprites/320 px por linha) entre todos — o piscar em cena cheia fica uniforme. Cada inimigo usa o slot da direção + os bits de flip. Blindados piscam de propósito; ao tomar dano brilham branco. Chefe = 4 sprites 24×24. Overlays de status por cima: **ciano contínuo** (gelo) e **pulso vermelho no tique** (fogo).
3. **Itens**, **projéteis**, **arcos do raio**.
4. **Sombra do jogador** (prioridade baixa, sob os demais).

### Decalques e flash

- **Sangue verde** (`blood.c`): ao morrer, um decalque 16×16 no **BG_A** (4 cópias espelhadas do tile `TILE_BLOOD`) — fica sob os sprites e sobre o chão, sem custo por frame.
- **Flash de tela** (`flash.c`): a explosão da bomba clareia a **paleta do chão (PAL3)** até o branco e decai em degraus.

### Paletas

| Paleta | Uso |
|---|---|
| PAL0 | Texto/HUD (letras no índice 15). Índices 1–14 = **paleta de flash**: brancos (dano) exceto o **índice 2 = vermelho** (pulso de fogo). Reaproveitada sem custo de VRAM |
| PAL1 | Objetos (1 contorno claro, 2 ciano/gelo, 3 vermelho, 4 amarelo, 5 tiro inimigo, 6/7 parede, 8 roxo, 9/10 lama, 11 escuro, 12 laranja, 13 cinza, 14 verde, 15 azul) |
| PAL2 | Mech do jogador |
| PAL3 | Chão (varia por fase; alvo do flash da bomba) |

> **Flash sem gastar VRAM**: o corpo do inimigo desenhado com **PAL0** fica todo branco (dano); o `TILE_STATUS` desenhado com PAL0 (índice 2 = vermelho) vira o overlay de fogo; com PAL1 (índice 2 = ciano) vira o gelo. Um tile, três efeitos, pela troca de paleta.
