> Pacote histórico de células uniformes32×48. A build atual usa os [insetos redesenhados por tamanho](../cangaco-insects-sized-v3/README.md).

# Inimigos brasileiros gigantes — sprites redesenhados, versão 2

Treze inimigos com perspectiva elevada refeita, mantendo nomes e IDs do projeto. Serra-pau, mutuca, saúva-soldado e escorpião continuam orgânicos, com placas reaproveitadas e implantes discretos.

- [Baixar os 13 inimigos: PNGs, paleta, recursos SGDK, prévias e relatórios](.).
- [Declarações de recurso SGDK separadas](enemies.res).
- [Paleta compartilhada PAL1](palette.json) / [paleta GIMP](palette.gpl).
- [Revisão por personagem e todas as poses nativas](../camera-60-redraw-v2/README.md).

| ID | Nome do projeto | Família | Folha mestra nativa |
|---|---|---|---|
| `sq_red` | Torreão | besouro serra-pau | [sq_red.png](enemies/sq_red/sq_red.png) |
| `sq_yellow` | Batedor | besouro serra-pau | [sq_yellow.png](enemies/sq_yellow/sq_yellow.png) |
| `sq_purple` | Baluarte | besouro serra-pau | [sq_purple.png](enemies/sq_purple/sq_purple.png) |
| `sq_orange` | Aríete | besouro serra-pau | [sq_orange.png](enemies/sq_orange/sq_orange.png) |
| `tri_red` | Fuzileiro | mutuca | [tri_red.png](enemies/tri_red/tri_red.png) |
| `tri_yellow` | Caçador | mutuca | [tri_yellow.png](enemies/tri_yellow/tri_yellow.png) |
| `tri_purple` | Escudeiro | mutuca | [tri_purple.png](enemies/tri_purple/tri_purple.png) |
| `tri_orange` | Adaga | mutuca | [tri_orange.png](enemies/tri_orange/tri_orange.png) |
| `pen_red` | Artilheiro | formiga saúva-soldado | [pen_red.png](enemies/pen_red/pen_red.png) |
| `pen_yellow` | Alcateia | formiga saúva-soldado | [pen_yellow.png](enemies/pen_yellow/pen_yellow.png) |
| `pen_purple` | Fortaleza | formiga saúva-soldado | [pen_purple.png](enemies/pen_purple/pen_purple.png) |
| `pen_orange` | Meteoro | formiga saúva-soldado | [pen_orange.png](enemies/pen_orange/pen_orange.png) |
| `boss` | Lacraia | escorpião-amarelo-do-Nordeste | [boss.png](enemies/boss/boss.png) |

## Prévias de movimento

- [Serra-pau: oito direções, ampliação 3×](previews/sq-movement-3x.gif).
- [Mutuca: oito direções, ampliação 3×](previews/tri-movement-3x.gif).
- [Saúva-soldado: oito direções, ampliação 3×](previews/pen-movement-3x.gif).
- [Lacraia / escorpião: oito direções, ampliação 3×](previews/boss-movement-3x.gif).

As folhas por direção estão em `enemies/ID/directions/ID_DIRECAO.png`. Os prompts iniciais e as correções estão em `prompts/`, nomeados pelo ID. As mutucas tiveram as antenas corrigidas; as saúvas receberam novas vistas L/O; Fortaleza tem seis poses extras para a corrida lateral. Meteoro compartilha uma pose neutra entre repouso e passagem da corrida L/O para substituir um quadro cortado da fonte.

## Formato e validação

Cada direção tem uma folha **192×96**, com células **32×48**: quatro quadros de repouso e duas células vazias na primeira linha; seis quadros de movimento na segunda. A folha mestra **192×768** reúne as oito direções, na ordem N, NE, L, SE, S, SO, O, NO. Há 80 referências de quadro e 16 animações por personagem. Esses PNGs e as prévias são as matrizes completas. Na build atual, cada direção usa somente dois quadros de repouso e quatro de corrida, selecionados sem alterar os pixels ou o alinhamento das matrizes.

PNGs indexados de 4 bits, índice 0 transparente, até 15 cores visíveis, componentes RGB nos oito níveis do Mega Drive e alfa somente 0/255. A referência dos pés é a linha 46 da célula. As prévias são arquivos separados, ampliados por vizinho mais próximo.

Cinco vistas foram desenhadas; SO/O/NO usam espelhamento horizontal de SE/L/NE. Detalhes assimétricos também são espelhados. Não se usa espelhamento vertical para criar frente/costas.

A [revisão visual da câmera](../camera-60-redraw-v2/README.md) compara os PNGs nativos a guias geométricos projetados a **60° acima do chão**. Essa revisão não mede um ângulo 3D exato a partir dos desenhos 2D. Os relatórios técnicos mantêm essa distinção.

- [Validação de PNGs, paleta, quadros, espelhos, empacotamento e ResComp](validation/report.json).
- [Memória da ROM compilada e executada](validation/memory.json).
- [Registro de recorte, fonte e alinhamento por pose](validation/export.json).

O código de produção passou por 600 quadros de estresse: máximo de 80 sprites de hardware, 20 por linha e 320 pixels por linha. A ROM nova foi executada por 1159 quadros no Genesis Plus GX, incluindo Damião nas oito direções e os 13 tipos de inimigo. Isso verifica o emulador e as verificações de software; não é um teste em console físico.

## Memória do conjunto integrado

| Medida | Resultado |
|---|---:|
| ROM final | 640 KiB |
| Capacidade declarada no cabeçalho | 1024 KiB |
| Folga na capacidade declarada | 384 KiB |
| RAM estática | 6008 bytes |
| Heap livre observado | 47490 bytes |
| Maior bloco livre observado | 46976 bytes |
| Cache dos inimigos em VRAM | 12 KiB |
| Um quadro do protagonista em VRAM | 768 bytes |
| Reserva adicional de VRAM deste redesenho | 0 bytes |
| DMA máximo dos personagens por quadro | 3840 bytes |

Os limites H40 são compartilhados com tiros, efeitos, itens e outros sprites. O renderizador omite desenhos de menor prioridade ao atingir os limites; esses números não garantem uma quantidade fixa de personagens simultâneos. Há limite de quatro atualizações de quadro de inimigos mais uma do protagonista por quadro do jogo; sob pressão de DMA a atualização pode ser adiada.

## Origem e reprodução

Arte gerada/editada com **image_gen integrado**. Os prompts exatos estão em `prompts/` e as fontes em `originals/`. Os scripts fazem segmentação por alfa, registro, escala por vizinho mais próximo, conversão para paleta e empacotamento de tiles. Não desenham poses procedurais.

O exportador mantém os binários candidatos em `runtime/`. O jogo usa a seleção compacta de `game/res/actor_animation.json`, gerada diretamente dos PNGs por `game/tools/pack_actor_animation.py`; os candidatos históricos completos em `runtime/` preservam quatro quadros de repouso e seis de corrida. A revisão da câmera é associada ao hash do PNG; se uma nova exportação mudar a imagem, a revisão volta ao estado pendente.

A versão anterior permanece preservada. Os nove mechs de estudo e os placeholders `dummy`/`target` continuam legados. A projeção do cenário permanece a implementação existente.

Os inimigos usam uma única paleta PAL1 compartilhada com os objetos existentes. Os 390 quadros canônicos em uso ocupam 299520 bytes de ROM, mais 7680 bytes de ícones e 32 bytes de paleta. Cada quadro animado utiliza duas peças de hardware, 32×32 e 32×16.

## Desempenho medido

A validação de memória e SAT não comprova FPS. A correção atual recupera 60 FPS com três inimigos na arena com lógica ativa; quinze ainda ficam em 30 FPS, enquanto a referência ASCII chega a 40 FPS. Com a lógica congelada, a animação/desenho de até dezesseis mantém 60 FPS. Veja a [investigação de CPU](../cangaco-insects-iso60-v2/validation/performance/README.md).
