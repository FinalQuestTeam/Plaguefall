# Plaguefall — Game Design Document (GDD)

> **Plataforma:** Sega Mega Drive / Genesis · **Engine:** SGDK 2.11 (C, m68k-elf)
> **Gênero:** shooter de arena top-down, sobrevivência por fases
> **Documento gerado a partir do código-fonte** (`game/src/`) — os valores refletem a implementação real.
> Tempos convertidos assumindo **60 fps (NTSC)**; em PAL (`fps` = 50) as cadências se ajustam automaticamente.

> **Nova direção visual:** cangaço cyberpunk brasileiro, com figuras humanas, implantes cibernéticos, pedaços de armadura sobre tecido e tecnologia adaptada de objetos cotidianos. O protagonista usa arma de fogo; o [guerreiro Damião](../art/cangaco-protagonista-iso60-v2/README.md) já substitui o mech, com animação e oito direções. Os [13 inimigos nas resoluções nativas](../art/cangaco-insects-sized-v3/README.md) já foram convertidos em sprites e integrados, com auditoria de memória. A câmera ortográfica elevada a **60° acima do chão** continua sendo requisito: Damião e os 13 inimigos receberam um [redesenho na versão 2](../art/camera-60-redraw-v2/README.md), comparado visualmente a guias geométricos dessa câmera. A elevação exata de uma câmera 3D não é medida a partir dos PNGs 2D. Mantêm-se as direções `0=N, 1=NE, 2=L, 3=SE, 4=S, 5=SO, 6=O, 7=NO`. As folhas de robôs em `art/darkspace-8dir-v3/` são estudos anteriores. Nossa Senhora Aparecida substitui a antena no objetivo PROTEGER, mantendo24×24 e todas as regras do NPC. Dinorah tem sprites32×48 e oito direções em `art/cangaco-parceira-iso60-v1/`; seu comportamento e um segundo ator ainda não foram integrados. [Inventário e pendências](../art/INVENTARIO-SPRITES.md).

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

A campanha se passa num Brasil futuro com cangaço cyberpunk, religiosidade popular e resistência humana a um enxame alienígena cibernético. Damião trabalhava na manutenção de foguetes reutilizáveis e sonhava em viajar. As cargas retornaram contaminadas, as instalações viraram ninhos e ele ficou em terra, lutando com equipamento remendado e implantes.

A abertura parte de sua provocação: “Você já ouviu falar que o Diabo dá tudo que a gente quer? Mas sempre da maneira mais filha da puta possível?” O Diabo é a interpretação de Damião para a promessa cruel de progresso; a campanha não confirma um pacto sobrenatural. O Consórcio Ascensão escondeu alertas e manteve as entregas. A resistência tenta recuperar um corredor industrial no sertão, com apoio de uma rede de abrigos e rádios.

O cangaço aparece nas silhuetas, no equipamento recuperado, no conhecimento do território e no enfrentamento aos donos da infraestrutura. A santa da fase 5 é um ponto de fé e abrigo cuja base guarda uma estação de rádio. Defendê-la dá tempo a uma transmissão. As regras continuam sendo as do NPC estático existente.

[Universo e personagens](historia/universo.md) define a proposta completa e distingue contexto narrativo de sistemas ou arte ainda não integrados. A antiga premissa de soldado em treinamento, simulação militar e piloto de mech foi substituída por esta direção.

# História

O roteiro executável está em `levels/story.c`, com21 cenas-base, variantes das conversas 14–16 e oito epílogos. Os retratos são Damião, Padre, Dinorah e Escorpião. As falas nativas usam português acentuado. A animação existente de101 segundos abre o jogo antes do menu; a chegada à fase 1 mantém só o chamado do padre.

A campanha tem 16 etapas por percurso e 19 versões:

| Origem | Condição | Destino |
|---|---|---|
| 1 | Sem bomba / com bomba | 2A, igreja preservada / 2B, destroços sólidos |
| 5 | Sinal protegido / sinal perdido | 6A, resgate completo / 6B, perdas civis e portões |
| 12 | Dinorah viva / morta | 13A, 30 insetos e apoio final / 13B, 45 insetos e luto |

Igreja, resgate e Dinorah persistem depois das reconvergências e compõem oito encerramentos. Dinorah viva trabalha no console protegido e participa das conversas 14, 15 e 16. Morta, a operação final usa sequência automática e apoio do padre. O chefe emerge dos foguetes em chamas; derrotá-lo encerra o confronto local.

[História e impactos](historia/tratamento-proposto.md) · [Campanha por nó](historia/campanha.md) · [Implementação e playtests](campanha-implementada.md).

## Visão geral

**Plaguefall** é um shooter de arena *top-down* para Mega Drive. O jogador controla **Damião, humano cibernético32×48** (hitbox 16×16) em arenas com limites por fase, eliminando insetos gigantes que surgem em ondas. Os objetivos alternam combate, travessia, escolta, transporte e operação de equipamentos; na **fase 5**, proteger a Santa por 120 segundos; na **fase 16**, o objetivo é **derrotar o chefe Escorpião** — vencê-lo apresenta o diálogo final e a caixa de vitória, com opções de voltar ao título ou iniciar uma campanha nova.

A **fase 1** usa um mundo de **512×384**, câmera com janela320×224, padrões residentes em BG_B com atualização circular de linhas, sangue em BG_A e HUD fixo em WINDOW. Igreja e objetos periféricos possuem colisão; a bomba altera parte da igreja e decide a saída2B. Limites validados: quatro inimigos e seis tiros de cada lado,60 FPS NTSC/50 FPS PAL no emulador. [Arte, testes e próximos formatos](fases-cenarios.md).

As arenas aprovadas das fases iniciais usam cenários maiores com câmera. As fases que conservam a arena fixa reservam o topo para o painel de 24 px; o limite dos pés deixa espaço para o corpo de Damião abaixo dele.

| Dimensão da arena fixa | Valor (tiles) | Valor (pixels) |
|---|---|---|
| Largura (`ARENA_TILES_W`) | 40 | 320 |
| Altura, incluindo borda (`ARENA_TILES_H`) | 25 | 200 |
| Origem da borda (`ARENA_TILE_X`, `ARENA_TILE_Y`) | (0, 3) | (0, 24) |

Limites dos pés na arena fixa: `INNER_MIN_X` = 8, `INNER_MIN_Y` = 56, `INNER_MAX_X` = 311, `INNER_MAX_Y` = 215. Os mundos com câmera mantêm os limites próprios. A câmera considera o painel maior e prioriza manter Damião visível no limite sul da defesa.

## Controles

Só o Joypad 1 (`JOY_1`) é lido. Comandos de menu/itens usam **detecção de borda** (comparação com `prevJoy`).

| Botão | Em jogo (`ST_PLAY`) | Em telas |
|---|---|---|
| D-pad | Move nas 8 direções | Navega no menu / troca página da ajuda |
| A | Atira (segurar = autofire na cadência) | Começa a fase (preparação) / confirma |
| B | **Ativa** o item selecionado do inventário | Sai ao título (pausa) |
| C | **Troca** a seleção do inventário | Avança a fase (preparação) |
| START | Pausa / retoma | Repete na derrota, cancela a confirmação de saída e confirma a opção no final. |
| A+B+C (segurar) | **(Debug)** pula para a próxima fase (uma vez por combo) | — |

## Fluxo e estados do jogo

Máquina de estados em `core/flow.c` (a tela-título roda antes do laço, em `title.c`):

| Estado | Descrição |
|---|---|
| `ST_PREP` | Preparação: "FASE n", meta, intervalo de spawn e os **sprites** dos inimigos da fase. A começa; C avança de fase. |
| `ST_PLAY` | Jogo ativo (inclui a contagem "PREPARE-SE" de 3 s congelada). |
| `ST_PAUSE` | Pausa: infos da fase; START retoma, B sai ao título. |
| `ST_OVER` | Caixa de derrota com repetir a fase ou voltar ao título (confirmação adicional). START repete diretamente; A confirma a seleção. Repetir restaura a vida; sempre deixa o bornal e volta ao básico. A coleta recupera a fotografia pré-morte conforme a etapa (1–5 tudo, 6–11 menos um nível e um item, 12–16 no máximo uma melhoria de cada que existia). |
| `ST_DONE` | Cartão central de objetivo por 2 s (3 s na perda do sinal); A/START podem seguir após uma nova pressão e 350 ms. Resolve a saída (`GRAPH_resolve`) e segue ao diálogo/mapa. |
| `ST_MAP` | **Mapa de rotas** (`routemap.c`): o grafo desenhado dos próprios dados (nós `mapCol/mapRow`, ligações das saídas), caminho percorrido "O", próxima fase "*" piscando, resto "."; A/START segue à preparação. |
| `ST_STORY` | **Console de holodeck** (`screens/story.c`, `screens/radio.c`, roteiro em `levels/story.c`): monitor superior preto com texto amarelo; retratos 48×48 fixos nos dois monitores inferiores, Damião à esquerda e interlocutor à direita. O campo `side` mantém as cores originais de quem fala e escurece quem escuta. Texto de 26 caracteres por linha, até quatro linhas com entrelinha de 16 px. A completa/avança e START pula. Cada cena toca uma vez por campanha, em ANTES ou DEPOIS. |
| `ST_END` | Caixa central de vitória após o diálogo final; aguarda escolha. A/START confirmam voltar ao título ou jogar novamente com o estado de campanha reiniciado. |

### Fluxo geral

1. **Splash** (logo FinalQuest) → **monólogo animado** (14 quadros e 18 cartelas, uma vez por boot, somente START pula) → **Tela-título** (splash da caatinga + menu: **NOVO JOGO / COMO JOGAR / FASE TESTE**).
2. **Preparação** (`ST_PREP`) → A para começar.
3. **3 → 2 → 1** em um pequeno instrumento sobre o cenário (3 s congelado) → **VAI!**, com movimento e tiro liberados no zero. A etiqueta permanece 21 quadros em NTSC ou 18 em PAL; não estende o congelamento. Soltar A durante a contagem arma o disparo, sem deixar a confirmação do menu disparar sozinha.
4. Meta atingida → `ST_DONE` → história do DEPOIS (se houver) → **mapa de rotas** (`ST_MAP`) → história do ANTES do nó destino (se houver) → preparação da próxima (decidida pelas condições de saída do grafo). Morte → `ST_OVER` → recomeça a mesma fase. Objetivo falhado em nó **com rota de falha** (`OBJ_FALHOU`) → "SINAL PERDIDO / A MISSAO CONTINUA" → segue pela rota de falha (sem game over).
5. **Fase 16**: o chefe é gerado no início; derrotá-lo → diálogo final → `ST_END` → título ou campanha nova na fase 1.

### Temporizações (60 fps NTSC)

| Evento | Código | Segundos |
|---|---|---|
| Contagem 3/2/1 | `fps * 3` | 3 s; movimento e tiro liberados no zero |
| Etiqueta VAI! | `(fps * 35 + 99) / 100` | ~350 ms sobre combate ativo |
| Primeiro inimigo (`FIRST_SPAWN_S`) | `1 * fps` | 1 s após o congelamento |
| Cartão de objetivo | A/START após soltar o botão e aguardar 350 ms | Aguarda confirmação, tanto no sucesso quanto na mudança de rota |
| Intervalo entre ondas | `spawnSeconds * fps` | por fase (2–5 s) |

### Persistência

- **Entre sessões, sem SRAM:** o **Sinal do Último Chão** usa seis símbolos de um alfabeto de 16 sprites de 32×32, incluindo o emblema STE do sindicato. O jogador fotografa/anota a sequência exibida na entrada da fase ou na pausa e usa **Sintonizar** no título. Preserva nó A/B, três consequências narrativas e melhorias de tiro/velocidade do começo da fase. Ao carregar: 100 HP, duas bombas, inventário vazio e efeitos temporários zerados; objetivo, inimigos e posição recomeçam. O caminho e as cenas já concluídas são reconstruídos. A pausa consulta o checkpoint original, sem incorporar coletas posteriores. A derrota mantém esse código e sua repetição normal não exibe novamente a tela do sinal. Os códigos podem ser reutilizados.
- **Formato do sinal:** seis nibbles, 24 bits: versão de 2 bits (`1`), velocidade em 3 bits (0–5 melhorias), potência menos um em 3 bits (0–4), consequências em 3 bits, nó em 5 bits (1–19) e CRC-8 de 8 bits (polinômio `0x07`, inicial `0xA7`, dois bytes do payload, mais significativo primeiro). A ordem dos símbolos é parte do formato e não deve ser alterada sem migração/versão. Código malformado, versão desconhecida e consequências incompatíveis com o nó são recusados. Fase Teste não produz códigos da campanha.
- **Entre fases**: HP, cargas de bomba, itens do inventário e bônus acumulados (leque de balas, velocidade) **persistem**.
- **Na derrota**: tentar novamente é a seleção inicial; START repete diretamente, A confirma a seleção e voltar ao título exige confirmação. A vida volta a 100 e o equipamento ao básico, em todas as etapas, até recolher a bolsa. `DEATH_capture` fotografa melhorias, inventário/cargas, bombas, modo de tiro e escudo ao entrar na derrota; `DEATH_retry` reinicia e `DEATH_startPhase` emite uma bolsa. As rotas A/B seguem a etapa correspondente.
- **Etapas 1–5**: o bornal devolve todas as melhorias de tiro/velocidade, bombas, itens/cargas, modo de tiro e tempo restante de escudo existentes na morte.
- **Etapas 6–11**: o bornal guarda as melhorias anteriores menos uma de tiro e uma de velocidade (20 pontos percentuais), até o básico de um projétil e +0%, sem piso 3. Remove o último item ocupado da fotografia; quando não há itens, desconta uma bomba. Modo de tiro e escudo guardados retornam com a coleta.
- **Etapas 12–16**: a bolsa devolve no máximo uma melhoria de tiro (+1 projétil) se havia alguma, e uma de velocidade (+20%) se havia alguma. As condições são independentes: se não havia bônus de um atributo, não concede esse atributo. Itens, bombas e efeitos não voltam.
- **Bolsa**: sempre existe após a derrota, inclusive vazia. Procura chão sem obstáculos/lava perto da queda ou da entrada; não nasce sobre o jogador nem desaparece por tempo. Coletas novas não entram na fotografia nem são removidas: as melhorias guardadas são somadas respeitando os tetos. Itens guardados que não couberem ficam na bolsa, sem repetir melhorias já devolvidas. Uma nova morte substitui o conteúdo pela fotografia mais recente; morrer sem recolher perde a bolsa anterior. Não entra no sorteio comum de inimigos e não atravessa fases/campanhas.
- **Treino**: as salas comuns conservam o reinício com vida cheia, duas bombas e equipamento básico. A sala 10 usa a captura, queda, coleta e penalidade reais para testar as três etapas; B repõe a configuração e C troca o trecho. Novo jogo usa o equipamento inicial.
- Cura tem **teto de 100 HP**.

## Tela-título, splash e ajuda

- **Splash** (`splash.c`): logo [FinalQuest redesenhado](../art/finalquest-logo-v2/README.md), em192×128 centralizado; fades de0,2s,1s de exibição e possibilidade de pular.
- **Monólogo animado** (`intro.c`): [14 quadros e 18 cartelas do storyboard](../art/intro-monologo-v2/README.md) entre FinalQuest e o menu, 101 segundos de exibição, com as trocas de imagem. Texto branco centralizado em até36×4, fundo preto com transição suave desde a arte, fades visuais e música contínua desde o logo Plaguefall. Sem nome, contador ou instruções na tela. O enquadramento é fixo;12 partículas de poeira, brasa e fuligem usam posições fracionárias e até1 pixel de deslocamento por frame. Usa924 tiles para a imagem mais3 para partículas, antes da inicialização dos recursos da arena. O último quadro dura6s; as trocas de cartela nos planos 08, 11, 12 e 13 conservam a imagem e a música; o fundo do menu já fica empacotado na ROM para evitar a montagem pixel a pixel no fim. A, B e C são ignorados; somente START pula. Não se repete ao voltar ao título. A conversa antes da fase 1 mantém apenas o chamado do padre e a resposta de Damião.
- **Título** (`title.c`): [splash art da caatinga](../art/title-caatinga-v1/README.md), com Damião, Dinorah, padre Comando sem chapéu e insetos biomecânicos. Imagem320×224 em `titlebg_data.h`, duas paletas de16 cores por tile; mesmo espaço temporário de1120 tiles. Menu à esquerda: **NOVO JOGO / COMO JOGAR / FASE TESTE**, todo o texto branco, com cursor `>` para a seleção. O tema Baião de Ferrugem toca em sua versão calma aqui (ver Áudio). O backdrop preto é restaurado ao entrar.
- **Galeria de assets removida do menu:** fontes e relatórios históricos permanecem em [gallery-v1](../art/gallery-v1/README.md).
- **Como Jogar** (`help.c`): **8 páginas** navegáveis com ESQ/DIR ou A; B/START voltam ao título ou à pausa de origem. Controles, itens diretos, inventário, cores/famílias dos inimigos, habilidades das saúvas, missões/rotas, bolsa em todas as derrotas, recuperação pré-morte e regras por trecho da campanha. A última página mostra o sprite real do bornal.

## HUD da resistência (24 px)

Painel opaco de 320×24 em WINDOW, com fonte e ícones nativos de 8×8, metal escuro e bordas em cobre. Usa a paleta existente de objetos.

| Área | Conteúdo |
|---|---|
| Esquerda, x=0–103 | Objetivo em duas linhas: eliminações/meta, vida e tempo da Santa, direção/progresso da travessia, vida/estado de Dinorah ou vida atual do Escorpião. |
| Centro, x=108–209 | Quatro espaços de equipamento com ícone e quantidade; borda dourada identifica a seleção. |
| x=214–233 | Caixa azul com modo de tiro e cargas; desaparece quando as cargas acabam. |
| Direita, x=242–309 | `VIDA 000–100` e barra; vermelho abaixo de 26 de vida, vazia em zero. |

O inventário muda apenas quando sua assinatura muda. Atualizações de objetivo editam somente os números; a fila envia no máximo 16 tiles por quadro (512 bytes), preservando margem para sprites/câmera. O painel usa 120 tiles da reserva de ícones de menu, sem reduzir o cache de inimigos durante a partida. A contagem regressiva usa temporariamente 180 tiles da cauda desse cache, com proteção no alocador e liberação após o aviso de início. Os sprites ficam sob o painel opaco. Nas salas técnicas, o diagnóstico ocupa as linhas abaixo dele.

[Capturas da ROM, limites de desempenho e testes PAL/NTSC](../art/hud-resistencia-v1/integracao/README.md).

---

# 2. Jogador, tiros, bomba e inventário

## O jogador

Damião **32×48** (sprite em duas peças, PAL2, oito direções) mantém a **hitbox16×16**. Movimento em **fixed-point26.6**. Cinco vistas canônicas N/NE/L/SE/S; SO/O/NO usam somente HFLIP. Runtime com dois quadros de repouso e quatro de movimento, transmitidos para um frame em VRAM — ver §6.

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
| Origem | arma de Damião (`PSHOT_MUZZLE_FWD` = 13 px à frente, 5 px à direita) |
| Dano | 1 por bala (HP dos inimigos é medido em tiros) |

Cada disparo reserva o leque completo antes de criar as balas. Usa vagas livres e, se o pool atingir o teto da fase (`shotCap`, seis em várias arenas), substitui projéteis anteriores em rodízio para não cortar o novo leque. A quantidade simultânea permanece no limite da fase.

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

Cada inimigo combina uma **forma** (perfil de resistência) com uma **cor** (comportamento). As famílias visuais atuais são serra-pau (quadrado), mutuca (triângulo) e saúva (pentágono), com implantes e placas reaproveitadas. O chefe se chama Escorpião e usa o concept do escorpião-amarelo-do-Nordeste. Há oito direções, com cinco vistas desenhadas e três por espelhamento horizontal (§6).

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
| **Dummy** (teste) | 24 | 20 | 0 | 0% | 0 | dummy da bancada de itens |
| **Alvo** (teste) | 24 | 1 | 0 | 0% | 0 | alvos de cadeia da bancada de itens |
| **Escorpião** (CHEFE) | **48** | **25** | **20** | 100% | 32 | ver abaixo |

### Comportamentos por cor

- **Vermelho** (`enemy_red.c`): persegue se `speedFp > 0`; dispara mirado no jogador a cada `timerA` décimos de s. Com `EXTRA_SPREAD` dispara **leque de 3**. Primeiro tiro escalonado (`ENEMY_CD/2 + random % fps`) para dessincronizar.
- **Amarelo** (`enemy_yellow.c`): perseguição pura (`ENEMIES_chase`). Com `EXTRA_SPLIT`, ao morrer gera 2 Caçadores no lugar.
- **Roxo** (`enemy_purple.c`): persegue e alterna escudo — `timerA` s vulnerável / `timerB` s blindado. Blindado: **bloqueia tiros** (escudo dourado flutuante de 8×8; corpo sempre visível) e é imune à cadeia/bomba. Com `EXTRA_SUMMON` invoca Caçadores enquanto blindado.
- **Laranja** (`enemy_orange.c`): aproxima → **telegrafa 0,2 s** (para mirando) → **investida reta 0,5 s a ~3,1 px/frame** (`DASH_SPEED_FP` = 200) → cooldown `timerA`. Com `EXTRA_TELEPORT`, pisca para um ponto próximo do jogador antes do bote.

## O chefe: Escorpião (`enemy_boss.c`)

Escorpião **48×48** (ID `boss`; quatro peças de32×32,32×16,16×32 e16×16). Aparece na **fase 16** e nas salas técnicas que usam o comportamento real. Tem duas fases: a segunda começa uma única vez ao chegar a **12 de vida ou menos**, inclusive ao saltar esse valor por dano. O contador `tA` controla a primeira fase e as invocações; flags em `tB` mantêm a segunda fase e a alternância dos ataques, sem ampliar a estrutura do inimigo.

| Mecânica | Valor |
|---|---|
| Vida | 25 tiros |
| Dano de contato | 20 · Dano do tiro: **13** |
| **Blindagem cíclica** | Somente na primeira fase: invulnerável **3 s a cada 15 s**, com escudo visível. Removida na segunda fase. |
| **Invocação** | Tenta preencher até **2 Caçadores vivos** a cada **10 s**, nas duas fases. Não acumula um terceiro. A fase 16 permite chefe + dois lacaios. |
| **Alternância da primeira fase** | A cada **4 s**: agressivo ↔ à distância. |
| Primeira fase agressiva | Aproxima, prepara a investida por ~0,3 s e avança em linha reta por ~0,5 s, com direção travada e velocidade210 em ponto fixo. |
| Primeira fase à distância | Recua e dispara **leque de 5 tiros**, dano13, a cada ~1,2 s. |
| **Transição aos12HP** | Parada de **0,8 s**, brilho somente no corpo e sinal sonoro. A mudança fica registrada até morte/reinício; não repete durante a luta. |
| **Segunda fase: investidas** | Aproxima por0,6 s e faz **duas investidas de0,5 s**. Cada uma tem aviso de~0,35 s, com direção travada; a segunda mira novamente antes de começar. |
| **Segunda fase: contra-ataque** | Após a segunda investida, permanece parado, sem atirar e vulnerável por **1,2 s**. Contato com o jogador e separação dos lacaios não interrompem essa janela. |
| **Segunda fase: disparos** | Recua por3 s, alternando leques de5 mais abertos e mais fechados, dano13 e cadência~1,2 s. Depois repete o ciclo de investidas. |
| **Pools de tiros** | Até10 projéteis inimigos e4 do jogador na fase16. O chefe aguarda cinco vagas antes de disparar; não apaga tiros ativos, não corta o leque e não pula a alternância enquanto espera. |
| Resistência à bomba | sofre 4 (nunca morre por bomba; 0 se blindado) |
| Ao morrer | poça de sangue, drop garantido, `bossDefeated` → tela de fim |

As duas fases usam os sprites atuais de48×48, oito direções, repouso/movimento e morte. O aviso mantém a orientação da investida; no recuo, o chefe continua encarando Damião. Pausa congela os temporizadores e reinício restaura25HP e a primeira fase. [Implementação e validação NTSC/PAL](../art/boss-phase2-v1/README.md).

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
| **Bornal de recuperação** | 0 (fora do sorteio) | direto, após qualquer derrota | Fotografia pré-morte: tudo em 1–5, menos um nível/item em 6–11, até uma melhoria de cada que existia em 12–16; sem prazo |

Soma dos pesos = 100 (coincidência atual; o sorteio usa a soma real).

## Regras de chão

- Máx. **8 itens** ativos (`MAX_ITEMS`); sem slot → o drop é perdido.
- Itens comuns têm **TTL de 10 s** e piscam nos últimos 2 s; o bornal e os itens permanentes do treino não expiram.
- Coleta automática por AABB 16×16; toca `sfxItemPickup` (blip ascendente).
- **Itens diretos** aplicam o efeito na hora; **itens de inventário** vão para uma posição livre (1–3). Inventário cheio: o item comum é consumido sem efeito; itens guardados no bornal permanecem nele até existir espaço.
- Arte 16×16 por char-map (`items_data.h`), pintada em `ITEMS_buildTiles`.

---

# 5. Fases e elementos de terreno

## Estrutura

A ordem vive em `levels/graph.c`: 19 nós, 16 etapas por partida e três bifurcações. `LevelDef` define objetivo, mapa, rota, roster, música e limites por fase. As máscaras de colisão usam passo de linha variável e 4 KB no total, cobrindo os mundos de 3072×320 sem ampliar a reserva anterior de RAM. Os objetos animados entram depois do atlas do cenário e respeitam a reserva comum de 640 tiles.

A tabela abaixo corresponde à ROM integrada de 23/10/2026. [Resultados, controles e método dos ensaios](campanha-implementada.md).

| Fase | Objetivo | Limite de insetos | Tiros por lado |
|---|---|---:|---:|
| 1 | Sobreviver 90 s | 4 | 6 |
| 2A | Eliminar 15 insetos | 4 | 6 |
| 2B | Eliminar 15 insetos; entulho sólido | 4 | 6 |
| 3 | Percorrer 2560 px | 4 | 6 |
| 4 | Eliminar 20 insetos | 4 | 6 |
| 5 | Proteger 120 s | 3 | 6 |
| 6A | Escolta 3072 px | 3 | 4 |
| 6B | Escolta 3072 px;2 válvulas e 2 portões | 3 | 4 |
| 7 | Transportar 5 cargas | 4 | 6 |
| 8 | Eliminar 3 prioritários | 6 | 6 |
| 9 | Percorrer 2560 px | 3 | 4 |
| 10 | Destruir 10 ninhos | 4 | 6 |
| 11 | Liberar 3 válvulas | 3 | 6 |
| 12 | Escolta 3072 px; morte permanente deDinorah | 3 | 4 |
| 13A | Eliminar 30;Dinorah protegida | 5 | 6 |
| 13B | Eliminar 45;Dinorah morta | 5 | 6 |
| 14 | Ligar 5 geradores | 4 | 4 |
| 15 | Proteger 120 s | 3 | 4 |
| 16 | Derrotar o chefe | 4 | 4 |

## Chão da arena (`floor.c`, campo `LevelDef.floor`)

Char-map 32×32 ladrilhado no **BG_B** (PAL3), escolhido por fase. Todas as variantes ficam residentes na VRAM (48+32 tiles):

| Variante | Uso | Visual |
|---|---|---|
| `FLOOR_STONE` (padrão) | fases sem lama | pedra escura (basketweave) |
| `FLOOR_FOREST` | fases de lama só | grama, terra, folhas, pedrinhas |
| `FLOOR_CAVE` | covil do chefe (16) | rocha úmida/arenosa |
| `FLOOR_MIX` | fases **lava+lama** | **rocha na arena + grama ao redor da lama** |

O **`FLOOR_MIX`** desenha dois chões na mesma fase: como o BG_B só tem uma paleta (PAL3), os dois tilesets **dividem 16 cores** (grama + rocha). A grama é pintada nos tiles a até `FLOOR_MIX_MUD_PAD` = 2 tiles de qualquer retângulo de lama; o resto (inclusive o entorno da lava) fica rocha.

Na preparação/pausa, os inimigos do roster aparecem como **sprites reais** alinhados pela base (`LEVEL_drawInfo` → `ENEMYGFX_drawOnMap`); o chefe (48 px) não é mostrado ali.

## Fase Teste — seletor da campanha

O menu **FASE TESTE** oferece as 19 versões reais da campanha e os oito encerramentos. Esquerda/direita alternam as abas de fases e finais. Cima/baixo escolhem, C avança nove posições nas fases, A entra ou reproduz, e B/START voltam. Uma prévia de final retorna ao mesmo item ao terminar ou pular com START. A pausa permite reiniciar a fase ou trocar a seleção. As salas técnicas de validação foram retiradas do seletor.

### Arquivo do antigo sandbox

As antigas salas técnicas eram selecionadas pelo menu **FASE TESTE**, sem portas entre arenas. **START** abre pausa com continuar, configurar, reiniciar, trocar sala, ajuda e título. As configurações são locais ao treino e não alteram as fases da campanha.

| Sala | Objetivo e controles de ensaio |
|---|---|
| **Galeria de inimigos** | Os 12 tipos comuns e o Escorpião permanecem no lugar. Repouso/caminhada, oito direções, velocidade de animação 1×/½×/¼×, seleção de inimigo e reprodução de morte única ou repetida. Reposição após dois segundos. |
| **Bancada de itens** | Dummy central com 1/20/100 HP, oito itens com reposição opcional, dois alvos extras para raio em cadeia e vida inicial 25/50/100. Usa coleta, inventário e dano reais. |
| **Regras de morte (sala 10)** | Treino sem inimigos com as políticas reais das etapas 1–5, 6–11 e 12–16. A morre, B repõe, C troca o trecho. START configura tiro, velocidade, itens e bombas iniciais. Mortes repetidas e coleta do bornal usam os módulos de produção; o painel mostra os valores e o contador de mortes. |
| **Defesa da Santa** | Cenário da fase 5, Santa com 100 HP e objetivo de 30 segundos. Ataques pausados, padrão de campanha ou pressão contínua; opção sem derrota para Damião. Sucesso/falha congela o resultado até reiniciar ou trocar sala. |
| **Colisões e perigos** | Arena de 512×384 com muros, cantos, corredor de 32 px, obstáculo azul baixo que bloqueia pés e deixa tiros passar, lava e lama reais. Vida inicial configurável. |
| **Comportamento e chefe** | IA real, tipo específico ou misto, 1/4/8/16 inimigos, vida normal ou sem derrota. O Escorpião usa um chefe e seus lacaios reais. |
| **Carga e performance** | 1/4/8/16 inimigos, 0/6/16 tiros por grupo, escudo/gelo/fogo, mortes repetidas e modo sem derrota. Mostra FPS de simulação por VBlank, carga de CPU, pico e contagens de objetos. |

As salas técnicas usam diagnóstico no topo e recursos nativos compactos. A defesa preserva o HUD e o cenário da campanha. O HUD da resistência de 24 px está integrado; os dados técnicos aparecem abaixo dele. Na sobrecarga máxima pode haver queda de FPS: o propósito da sexta sala é expor esse limite. [Guia e validação das salas](../art/training-v2/README.md).

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

**Baião de Ferrugem**, composição original de inspiração nordestina e industrial. São **16 compassos de 2/4 / 128 semicolcheias**, em Ré mixolídio, com Sol sustenido como aproximação cromática de Lá. Harmonia D7–C–G–D7, dois compassos por acorde, repetida com variação melódica. A melodia tem durações explícitas, pausas, sustentação e vibrato discreto; o acompanhamento é sincopado, o baixo alterna tônica/quinta e a percussão combina baques, estalos secos e ruído periódico metálico. São sugestões de articulação no PSG, sem amostras acústicas de sanfona, zabumba ou triângulo. [Partitura editável e prévias](musica.md).

**BPM dinâmico por ameaça**: o andamento sobe conforme os inimigos vivos (`MUSIC_setEnemies`), com *glide* suave (sem saltos). A curva é **configurável por fase** no `LevelDef` — `musCalmUntil`, `musEnemyMax`, `musStepCalm`, `musStepHot` (0 em cada campo = usa o padrão global de `music.h`); `startPhase`/`startTest` aplicam via `MUSIC_setRamp`. Padrão: **100 BPM** até 4 inimigos, subindo até **150 BPM** em 15. A ameaça também acrescenta pulsos no ch1 e reforça acentos metálicos no ch3. O **chefe** usa aproximadamente **129–180 BPM**, e a retirada 6B usa **112–150 BPM**. Os valores `musStep*` são durações equivalentes a quadros NTSC; um relógio de 300 Hz mantém o andamento em PAL e NTSC. BPM = 900 / duração nominal do passo. A prioridade dos SFX continua preservada.

### Trilha da abertura (`system/audio/opening.c`)

[O Sonho Atendido](../art/audio-abertura-v3/README.md) é uma composição original para os 101 segundos dos 14 planos e 18 cartelas do storyboard. Começa na aparição do logo Plaguefall e segue sem loop, resets ou pausas nas mudanças de imagem, com mudança de tema entre sonho e presente, tensão industrial, pausa na reza e pulso após o rádio. O volume só tem fade na entrada do logo e na saída natural ou com START. A, B e C não avançam nem completam o monólogo. Usa o árbitro PSG e um relógio de300 Hz por interrupção vertical para manter os tempos em PAL/NTSC. As quatro partituras da galeria permanecem preservadas.

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
Inimigos nativos16×16,24×24,32×32 e chefe48×48; Damião permanece32×48. O runtime usa dois frames de repouso e quatro de movimento. As matrizes históricas32×48 permanecem arquivadas.
Os demais elementos continuam procedurais por char-maps.

- tilegen.c: 83 tiles fixos e PAL1 compartilhada entre objetos e inimigos.
- enemygfx.c: pool limitado de320 tiles (10240 bytes), com blocos de4 tiles, liberação e reutilização por entidade, mais
  15 slots de 16 tiles para ícones. Até quatro frames por VBlank (128/288/512/1152 bytes por frame conforme tamanho),
  com fila circular e adiamento das atualizações excedentes.
- ROM: 390 frames canônicos, cinco direções × seis poses × treze tipos.
  As três vistas ocidentais usam apenas HFLIP. Frente e costas são distintas.
- BOSS_ROT: 72 tiles reservados aos dois retratos de história, separados do cache.
- herogfx.c: Damião 32×48 em duas peças, um frame de 24 tiles dentro da reserva existente de 48 tiles, PAL2. Cinco vistas desenhadas e três por HFLIP; repouso de dois frames e corrida de quatro. Até 768 bytes adicionais de DMA por quadro, com prioridade sobre os inimigos.
- O gerador e os nove mechs antigos foram removidos do runtime. A antiga tela ASSETS foi retirada do menu inicial.
- floor.c: 80 tiles no BG_B, PAL3. Cenário e projeção de mapa ainda são os anteriores.

**Build atual:** ROM de3.014.656 bytes (2944 KiB), com cabeçalho para cartucho linear de4 MiB. A continuação usa códigos, sem gravar no cartucho. A [validação do sinal](../art/sinal-ultimo-chao-v1/native/validation/delivery.json) registra a ROM e os testes atuais desta integração; relatórios anteriores identificam suas respectivas builds.
[Compilação e testes da abertura](../art/intro-monologo-v2/build-validation.json). A auditoria anterior dos inimigos
observou47332 bytes de heap livre; esse número pertence àquela build. Os tiles de gameplay terminam no byte27488,
a fonte começa no byte 46080 e há 18592 bytes de intervalo livre.
Relatórios e capturas em art/cangaco-insects-sized-v3/validation/.
O relatório performance/README.md separa os testes de memória dos FPS; quinze inimigos com lógica completa ainda ficam abaixo da referência ASCII.

### Lista de sprites (`spritelist.c`)

Reconstruída a cada frame, encadeada por link, enviada via `DMA_QUEUE`:

1. **Jogador Damião** (32×48, duas peças 32×32 e 32×16, nos primeiros links; HFLIP nas vistas ocidentais).
2. **Inimigos**, com **rotação de flicker**: a varredura começa em um índice diferente por quadro, distribuindo o descarte do VDP (limite de 20 sprites/320 px por linha) entre todos — o piscar em cena cheia fica uniforme. Os inimigos comuns usam uma peça16/24/32; o chefe usa quatro peças (32×32,32×16,16×32,16×16) com espelhamento que reposiciona as colunas. A admissão por software respeita 80 sprites totais, 20 por linha e 320 pixels por linha. Blindados piscam de propósito; ao tomar dano brilham branco. O chefe usa célula48×48. Overlays de status por cima: **ciano contínuo** (gelo) e **pulso vermelho no tique** (fogo).
3. **Itens**, **projéteis**, **arcos do raio**.
4. **Sombra do jogador** (prioridade baixa, sob os demais).

### Decalques e flash

- **Sangue verde** (`blood.c`): ao morrer, um decalque 16×16 no **BG_A** (4 cópias espelhadas do tile `TILE_BLOOD`) — fica sob os sprites e sobre o chão, sem custo por frame.
- **Flash de tela** (`flash.c`): a explosão da bomba clareia a **paleta do chão (PAL3)** até o branco e decai em degraus.

### Paletas

| Paleta | Uso |
|---|---|
| PAL0 | Texto de menus/diagnósticos (letras no índice 15; índice1 preto nos mundos com câmera). Índices 1–14 = **paleta de flash**: brancos (dano) exceto o **índice 2 = vermelho** (pulso de fogo). Reaproveitada sem custo de VRAM |
| PAL1 | HUD da resistência e objetos (1 contorno claro, 2 ciano/gelo, 3 vermelho, 4 amarelo, 5 tiro inimigo, 6/7 parede, 8 roxo, 9/10 lama, 11 escuro, 12 laranja, 13 cinza, 14 verde, 15 azul) |
| PAL2 | Damião / galeria histórica |
| PAL3 | Chão (varia por fase; alvo do flash da bomba) |

> **Flash sem gastar VRAM**: o corpo do inimigo desenhado com **PAL0** fica todo branco (dano); o `TILE_STATUS` desenhado com PAL0 (índice 2 = vermelho) vira o overlay de fogo; com PAL1 (índice 2 = ciano) vira o gelo. Um tile, três efeitos, pela troca de paleta.
