# RedRex — Game Design Document (GDD)

> **Plataforma:** Sega Mega Drive / Genesis · **Engine:** SGDK 2.11 (C, m68k-elf)
> **Gênero:** shooter de arena top-down, sobrevivência por fases
> **Documento gerado a partir do código-fonte** (`game/src/`) — os valores refletem a implementação real.
> Tempos convertidos assumindo **60 fps (NTSC)**; em PAL (`fps` = 50) as cadências se ajustam automaticamente.

> **Nova direção visual:** cangaço cyberpunk brasileiro, com figuras humanas, implantes cibernéticos, pedaços de armadura sobre tecido e tecnologia adaptada de objetos cotidianos. O protagonista usa arma de fogo; o [guerreiro Rex](../art/cangaco-protagonista-iso60-v2/README.md) já substitui o mech, com animação e oito direções. Os [13 inimigos nas resoluções nativas](../art/cangaco-insects-sized-v3/README.md) já foram convertidos em sprites e integrados, com auditoria de memória. A câmera ortográfica elevada a **60° acima do chão** continua sendo requisito: Rex e os 13 inimigos receberam um [redesenho na versão 2](../art/camera-60-redraw-v2/README.md), comparado visualmente a guias geométricos dessa câmera. A elevação exata de uma câmera 3D não é medida a partir dos PNGs 2D. Mantêm-se as direções `0=N, 1=NE, 2=L, 3=SE, 4=S, 5=SO, 6=O, 7=NO`. As folhas de robôs em `art/darkspace-8dir-v3/` são estudos anteriores. Nossa Senhora Aparecida substitui a antena no objetivo PROTEGER, mantendo24×24 e todas as regras do NPC. Dinorah tem sprites32×48 e oito direções em `art/cangaco-parceira-iso60-v1/`; seu comportamento e um segundo ator ainda não foram integrados. [Inventário e pendências](../art/INVENTARIO-SPRITES.md).

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

## Gameplay Loop

O jogador tenta matar os insetos que aparecem na tela antes que estes o matem. Caso o jogador não seja rápido o suficiente eles formam um enxame, tornando o jogo mais difícil. Ao completar o objetivo estabelecido no início de cada partida, o jogador passa para a próxima fase.

## Dificuldade: Inseto e Enxame

Em seu modo mais simples, enfrentar um inseto é mais fácil que enfrentar um enxame. Evitar a formação e combater enxames é a parte central da mecânica do jogo. Essa lógica pode ser invertida com insetos mais poderosos, como chefões, que representam um desafio maior que um enxame.

O jogo é dividido em fases que ficam cada vez mais difíceis. Para o level design é indicado reservar cenários mais desafiadores para fases mais avançadas. Alguns cenários de dificuldade crescente dentro do jogo:

1. Enfrentar insetos fracos  
2. Enfrentar insetos fortes  
3. Enfrentar um enxame de insetos fracos  
4. Enfrentar um enxame de insetos fracos e insetos fortes  
5. Enfrentar um enxame de insetos fortes  
6. Enfrentar um chefão  
7. Enfrentar um chefão e insetos fracos  
8. Enfrentar um chefão e insetos fortes  
9. Enfrentar um chefão e um enxame de insetos fracos

### Balanceamento de dificuldade

É a dinâmica entre insetos e enxames que torna o jogo **entediante, divertido ou frustrante**:

1. Se eliminar insetos for muito fácil o enxame nunca se forma e o jogo fica **entediante**.  
2. Se eliminar insetos for desafiador na medida certa o enxame se forma mas é possível derrotá-lo, tornando o jogo **divertido**.  
3. Se eliminar insetos for muito difícil o enxame fica muito desafiador e o jogo fica **frustrante**.  
   

Controlar a dificuldade de enfrentar enxames é a melhor forma de balancear a dificuldade do jogo.

É possível alterar o poder e durabilidade dos insetos para criar diferentes dificuldades no jogo: **Fácil, Médio ou Difícil.**

O modo de jogo **Difícil** também pode oferecer menos itens ao jogador. É importante para que o jogo não fique muito frustrante **ser possível passar todas as fases sem usar itens e poderes.**

## Condições de vitória

### Eliminar uma quantidade específica de insetos

A condição de vitória mais simples no jogo é eliminar uma quantidade específica de inimigos. Esse objetivo pode ser fácil ou difícil dependendo do tempo de spawn dos insetos.

### Sobreviver por um tempo específico

Em vez de matar um determinado número de inimigos, o jogador precisa sobreviver por um tempo específico. Ainda é importante matar insetos para evitar ou reduzir enxames, o que facilita sobreviver por mais tempo.

### Proteger NPC por um tempo específico

Típica missão de resgate, um NPC precisa ser protegido por um tempo específico. O jogo pode apresentar ocasiões onde insetos são aliados do jogador e além de atacar podem ser derrotados. Essa dinâmica pode ser incorporada na narrativa.

### Achar um item específico

Ao derrotar um inimigo é possível que apareça um item. Qual item aparece também é algo aleatório. Achar um item específico pode ser uma condição de vitória.

### Matar todos os insetos

Em vez de matar um número específico de insetos, uma condição de vitória pode ser a de matar todos os insetos na fase.

### Matar o chefão

Nas fases com chefão a condição é matar apenas um inimigo.

## Rejogabilidade

### Rumores e “Internet Old School”

A época dos cartuchos precedeu a internet e o acesso à informação sobre determinados jogos era escassa. Nos primórdios da internet, os fãs conversavam sobre um jogo em fóruns onde existiam vários rumores e lendas urbanas sobre aspectos raros de um jogo.

Um fator de rejogabilidade pode ser criado ao reinventar esse efeito. Cada cartucho pode conter particularidades geradas por meio de códigos únicos em cada versão. Isso é mantido em segredo e, como a mesma coisa não pode ser reproduzida por todos, muitos vão acusar um jogador que alega descobrir um desses segredos de estar mentindo.

Isso pode fomentar rumores e testes para descobrir esses segredos, fomentando uma espécie de “internet old school” moderna.

### Personalização

Se for possível jogar de maneiras diferentes, alguns jogadores vão querer jogar o jogo várias vezes para descobrir tudo que é possível.

#### Código Konami

O uso do código Konami deve fazer algo. ↑ ↑ ↓ ↓ ← → ← → B A. Uma opção é gerar um item na tela. Esse tipo de mecânica pode fazer com que o jogador queira explorar mais o jogo.

#### Cartuchos personalizados

Cada cartucho pode gerar códigos específicos para propósitos específicos. Gerar um código como forma de save state, por exemplo. Individualizar a geração de código irá prevenir que esses sejam espalhados na internet.

### Personagens

O jogo possui diferentes personagens que podem apresentar diferenças entre eles. Uma opção é fazer com que um novo personagem seja liberado após finalizar o jogo uma vez. O personagem pode começar com tiro duplo em vez de tiro comum.

### Códigos Colecionáveis

Pode existir uma área no jogo para inserir códigos, alguns comuns em todo jogo e outros exclusivos para cada cartucho que precisam ser descobertos jogando. Esses códigos podem liberar algo no jogo, talvez itens colecionáveis.

### História não linear

A história se adapta à forma como o jogador joga. Ver novas versões da história incentiva rejogabilidade.

# Atmosfera e ambientação

A campanha se passa num Brasil futuro com cangaço cyberpunk, religiosidade popular e resistência humana a um enxame alienígena cibernético. Rex trabalhava na manutenção de foguetes reutilizáveis e sonhava em viajar. As cargas retornaram contaminadas, as instalações viraram ninhos e ele ficou em terra, lutando com equipamento remendado e implantes.

A abertura parte de sua provocação: “Você já ouviu falar que o Diabo dá tudo que a gente quer? Mas sempre da maneira mais filha da puta possível?” O Diabo é a interpretação de Rex para a promessa cruel de progresso; a campanha não confirma um pacto sobrenatural. O Consórcio Ascensão escondeu alertas e manteve as entregas. A resistência tenta recuperar um corredor industrial no sertão, com apoio de uma rede de abrigos e rádios.

O cangaço aparece nas silhuetas, no equipamento recuperado, no conhecimento do território e no enfrentamento aos donos da infraestrutura. A santa da fase 5 é um ponto de fé e abrigo cuja base guarda uma estação de rádio. Defendê-la dá tempo a uma transmissão. As regras continuam sendo as do NPC estático existente.

[Universo e personagens](historia/universo.md) define a proposta completa e distingue contexto narrativo de sistemas ou arte ainda não integrados. A antiga premissa de soldado em treinamento, simulação militar e piloto de mech foi substituída por esta direção.

# História

O roteiro executável está em `levels/story.c`: 22 cenas, com uma chegada para cada um dos 20 nós, uma cena depois da fase 15 e o final depois da 16. Usa quatro retratos: Rex, Comando (padre) e Dinorah derivados dos concepts; Lacraia com arte anterior. As falas são em MAIÚSCULA SEM ACENTO. Comando é o padre que coordena os abrigos; Rex chama os invasores de “baratas”. Dinorah participa por rádio antes da fase 7, sem ator aliado na arena. A completa/avança a fala; START pula a cena. Cada cena toca uma vez por partida.

A campanha tem 16 fases por percurso e quatro bifurcações já implementadas:

| Origem | Condição | Destino e contexto |
|---|---|---|
| 1 | Sem bomba / usou bomba | 2A, rua de serviço / 2B, baixio com lama após denunciar a posição |
| 5 | Protegeu o ponto / objetivo falhou | 6A, avanço / 6B, retirada com cerco mais apertado |
| 9 | Sem dano / sofreu dano | 10A, acesso técnico / 10B, desvio por lava e lama |
| 12 | Menos de 60 s / 60 s ou mais | 13A, passagem direta com lava / 13B, canal com lama |

A seleção narrativa acompanha o nó e o momento ANTES/DEPOIS. Não há uma segunda condição independente para escolher slides, nem seleção por quantidade de itens ou corações. Após convergir, as falas comuns funcionam com qualquer caminho anterior. O resultado da fase 5 é tratado nas chegadas a 6A/6B, pois a saída DEPOIS da 5 também pode ocorrer após falha roteada.

Rex vai da frustração com o sonho de viajar à decisão de defender quem ficou em terra. Lacraia oferece uma viagem como parte da carga; ele recusa. Vencer o chefe interrompe o comando local do enxame e permite o retorno à comunidade. O final é único e não declara o Brasil inteiro livre.

[Abertura completa](historia/abertura.md) · [Campanha por nó](historia/campanha.md) · [Sistema de diálogos](plano-historia.md).

## Visão geral

**RedRex** é um shooter de arena *top-down* para Mega Drive. O jogador controla **Rex, humano cibernético32×48** (hitbox 16×16) numa arena de tela única, eliminando insetos gigantes que surgem em ondas. Na maioria das fases o objetivo é **matar N inimigos** (`killTarget`); na **fase 5**, proteger a santa por 30 segundos; na **fase 16**, o objetivo é **derrotar o chefe Lacraia** — vencê-lo mostra a tela de fim ("PARABENS! FIM") e volta ao título.

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
| `ST_DONE` | "FASE CONCLUIDA!" por 3 s; a saída do grafo é resolvida (`GRAPH_resolve`) e vai ao mapa. |
| `ST_MAP` | **Mapa de rotas** (`routemap.c`): o grafo desenhado dos próprios dados (nós `mapCol/mapRow`, ligações das saídas), caminho percorrido "O", próxima fase "*" piscando, resto "."; A/START segue à preparação. |
| `ST_STORY` | **História** (`screens/story.c` + roteiro em `levels/story.c`): diálogo com retratos 48x48 (esq. em cima, dir. embaixo), máquina de escrever; A avança/completa, START pula. Toca 1x por run, nos momentos ANTES (chegada ao nó, antes da preparação) e DEPOIS (vitória, antes do mapa/fim). |
| `ST_END` | Fim de jogo (chefe derrotado): "PARABENS! FIM"; START volta ao título. |

### Fluxo geral

1. **Splash** (logo FinalQuest) → **Tela-título** (fundo em bitmap-art + menu: **NOVO JOGO / FASE TESTE / COMO JOGAR**).
2. **Preparação** (`ST_PREP`) → A para começar.
3. **"PREPARE-SE 3-2-1"** (3 s congelado) → jogo ativo.
4. Meta atingida → `ST_DONE` → história do DEPOIS (se houver) → **mapa de rotas** (`ST_MAP`) → história do ANTES do nó destino (se houver) → preparação da próxima (decidida pelas condições de saída do grafo). Morte → `ST_OVER` → recomeça a mesma fase. Objetivo falhado em nó **com rota de falha** (`OBJ_FALHOU`) → "A MISSAO CONTINUA..." → segue pela rota de falha (sem game over).
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

Rex **32×48** (sprite em duas peças, PAL2, oito direções) mantém a **hitbox16×16**. Movimento em **fixed-point26.6**. Cinco vistas canônicas N/NE/L/SE/S; SO/O/NO usam somente HFLIP. Runtime com dois quadros de repouso e quatro de movimento, transmitidos para um frame em VRAM — ver §6.

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
| Origem | arma de Rex (`PSHOT_MUZZLE_FWD` = 13 px à frente, 5 px à direita) |
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

Cada inimigo combina uma **forma** (perfil de resistência) com uma **cor** (comportamento). As famílias visuais atuais são serra-pau (quadrado), mutuca (triângulo) e saúva (pentágono), com implantes e placas reaproveitadas. O chefe usa o concept do escorpião, preservando o nome Lacraia. Há oito direções, com cinco vistas desenhadas e três por espelhamento horizontal (§6).

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

Escorpião **48×48** (ID `boss`, nome Lacraia preservado; quatro peças de32×32,32×16,16×32 e16×16). Aparece na **fase 16** (e na arena de teste, estágio 3). Contador mestre `tA` dirige todos os ciclos:

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

A **ordem da campanha vive no grafo de rotas** (`levels/graph.c`): cada fase é um nó (`NODE_COUNT` = **16**; 1–15 campanha + 16 = chefe, nó **final** = sem saídas) com **saídas condicionais** avaliadas ao vencer (bomba/dano/tempo/falha do objetivo — bifurcações ativas: **1→2A/2B** (sem bomba/com bomba), **5→6A/6B** (a fase 5 é PROTEGER o aliado 30 s; falhar NÃO é game over — vai à 6B "retirada" via `OBJ_FALHOU`), **9→10A/10B** (sem dano/com dano) e **12→13A/13B** (venceu em <60 s/não); cada par reconverge na fase seguinte). As condições leem as **estatísticas da fase** (`core/stats.c`: bombas usadas, dano sofrido, tempo, objetivo falhado), zeradas a cada início de fase. Plano completo em `doc/plano-rotas.md`. Cada fase é um `LevelDef` (dados puros) em `levels/defs/levelNN.c`: terreno (`lava`/`mud`, retângulos em tiles), `killTarget`, `spawnSeconds`, `spawnCount`, o **roster** de tipos, o **chão** (`floor`) e a **curva de música** por fase (`musCalmUntil`/`musEnemyMax`/`musStepCalm`/`musStepHot`; ver §6). A arte dos inimigos do roster é gerada **por fase** na VRAM (ver §6).

## Tabela das fases

| Fase | Meta | Spawn (s) | Por onda | Terreno | Chão | Roster |
|---|---|---|---|---|---|---|
| 1 | 10 | 5 | 1 | — | pedra | Torreão, Batedor |
| 2A | 12 | 5 | 1 | — | pedra | + Aríete *(rota sem bomba na 1)* |
| 2B | 12 | 5 | 1 | Lama | floresta | Torreão, Batedor, Aríete *(rota com bomba na 1)* |
| 3 | 14 | 4 | 1 | Lava | pedra | Batedor, Baluarte, Aríete |
| 4 | 16 | 4 | 1 | Lama | floresta | Torreão, Baluarte, **Caçador** |
| 5 | **proteger o aliado 30 s** | 4 | 1 | — | pedra | **Fuzileiro**, Caçador, Aríete |
| 6A | 20 | 3 | 1 | Lava | pedra | Fuzileiro, Caçador, **Adaga** *(protegeu o aliado)* |
| 6B | 20 | **2** | 1 | Lava | pedra | Fuzileiro, Caçador, Adaga *(retirada: o aliado caiu; música já tensa)* |
| 7 | 22 | 3 | **2** | Lama | floresta | Caçador, **Escudeiro**, Baluarte |
| 8 | 24 | 3 | 2 | Lava | pedra | Fuzileiro, Caçador, Adaga, Aríete |
| 9 | 24 | 4 | 1 | — | pedra | **Artilheiro, Alcateia**, Caçador |
| 10A | 26 | 3 | 2 | Lama | floresta | Alcateia, **Meteoro**, Adaga *(venceu a 9 sem dano)* |
| 10B | 26 | 3 | 2 | **Lava+lama** | mix | Alcateia, Meteoro, Adaga *(levou dano na 9)* |
| 11 | 28 | 3 | 2 | Lava+lama | mix | Artilheiro, **Fortaleza**, Caçador |
| 12 | 30 | 3 | 2 | Lava+lama | mix | Meteoro, Fuzileiro, Caçador, Baluarte |
| 13A | 34 | 2 | 2 | Lava | pedra | Baluarte, Caçador, Adaga, Artilheiro, Alcateia *(venceu a 12 em <60 s)* |
| 13B | 34 | 2 | 2 | **Lama** | floresta | Baluarte, Caçador, Adaga, Artilheiro, Alcateia *(demorou na 12)* |
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

### Arte e carregamento

Os 13 inimigos usam PNGs indexados exportados offline e BINs 4bpp em res/insects.res.
Inimigos nativos16×16,24×24,32×32 e chefe48×48; Rex permanece32×48. O runtime usa dois frames de repouso e quatro de movimento. As matrizes históricas32×48 permanecem arquivadas.
Os demais elementos continuam procedurais por char-maps.

- tilegen.c: 83 tiles fixos e PAL1 compartilhada entre objetos e inimigos.
- enemygfx.c: pool limitado de320 tiles (10240 bytes), com blocos de4 tiles, liberação e reutilização por entidade, mais
  15 slots de 16 tiles para ícones. Até quatro frames por VBlank (128/288/512/1152 bytes por frame conforme tamanho),
  com fila circular e adiamento das atualizações excedentes.
- ROM: 390 frames canônicos, cinco direções × seis poses × treze tipos.
  As três vistas ocidentais usam apenas HFLIP. Frente e costas são distintas.
- BOSS_ROT: 72 tiles reservados aos dois retratos de história, separados do cache.
- herogfx.c: Rex 32×48 em duas peças, um frame de 24 tiles dentro da reserva existente de 48 tiles, PAL2. Cinco vistas desenhadas e três por HFLIP; repouso de dois frames e corrida de quatro. Até 768 bytes adicionais de DMA por quadro, com prioridade sobre os inimigos.
- chars.c: nove mechs históricos, mantidos apenas na galeria.
- floor.c: 80 tiles no BG_B, PAL3. Cenário e projeção de mapa ainda são os anteriores.

**Build auditada:** ROM de524288 bytes dentro de 1 MiB; RAM estática de6165 bytes;
47332 bytes de heap livre observados. Os tiles de gameplay terminam no byte27488,
a fonte começa no byte 46080 e há 18592 bytes de intervalo livre.
Relatórios e capturas em art/cangaco-insects-sized-v3/validation/.
O relatório performance/README.md separa os testes de memória dos FPS; quinze inimigos com lógica completa ainda ficam abaixo da referência ASCII.

### Lista de sprites (`spritelist.c`)

Reconstruída a cada frame, encadeada por link, enviada via `DMA_QUEUE`:

1. **Jogador Rex** (32×48, duas peças 32×32 e 32×16, nos primeiros links; HFLIP nas vistas ocidentais).
2. **Inimigos**, com **rotação de flicker**: a varredura começa em um índice diferente por quadro, distribuindo o descarte do VDP (limite de 20 sprites/320 px por linha) entre todos — o piscar em cena cheia fica uniforme. Os inimigos comuns usam uma peça16/24/32; o chefe usa quatro peças (32×32,32×16,16×32,16×16) com espelhamento que reposiciona as colunas. A admissão por software respeita 80 sprites totais, 20 por linha e 320 pixels por linha. Blindados piscam de propósito; ao tomar dano brilham branco. O chefe usa célula48×48. Overlays de status por cima: **ciano contínuo** (gelo) e **pulso vermelho no tique** (fogo).
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
| PAL2 | Rex / galeria histórica |
| PAL3 | Chão (varia por fase; alvo do flash da bomba) |

> **Flash sem gastar VRAM**: o corpo do inimigo desenhado com **PAL0** fica todo branco (dano); o `TILE_STATUS` desenhado com PAL0 (índice 2 = vermelho) vira o overlay de fogo; com PAL1 (índice 2 = ciano) vira o gelo. Um tile, três efeitos, pela troca de paleta.
