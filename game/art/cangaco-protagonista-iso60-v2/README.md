# Rex — sprites redesenhados, versão 2

Protagonista humano do cangaço cyberpunk brasileiro: chapéu metálico funcional, placas reaproveitadas, tecido, implante no braço e arma de fogo. O redesenho expõe o topo do chapéu e dos ombros e encurta a leitura das pernas para acompanhar a câmera elevada.

- [Baixar PNGs, paleta, recurso SGDK, prévias e relatórios](redrex-heroi-iso60-v2-sgdk.zip).
- [Folha mestra na resolução nativa](heroi/heroi.png).
- [Corrida nas oito direções, ampliada 4×](previews/heroi-movimento-4x.gif).
- [Repouso nas oito direções, ampliado 4×](previews/heroi-repouso-4x.gif).
- [Comparação com a versão anterior](../camera-60-redraw-v2/hero-before-after-4x.png).
- [Declaração de recurso SGDK separada](heroi.res).
- [Paleta indexada](palette.json) / [paleta GIMP](palette.gpl).
- [Prompt exato do redesenho](prompts/heroi.txt).

A declaração em `heroi.res` foi compilada pelo ResComp:

```text
SPRITE heroi "heroi/heroi.png" 4 6 FAST 6 NONE BALANCED FAST
```

| Direção | Folha 192×96 |
|---|---|
| N | [heroi_N.png](heroi/directions/heroi_N.png) |
| NE | [heroi_NE.png](heroi/directions/heroi_NE.png) |
| L | [heroi_L.png](heroi/directions/heroi_L.png) |
| SE | [heroi_SE.png](heroi/directions/heroi_SE.png) |
| S | [heroi_S.png](heroi/directions/heroi_S.png) |
| SO | [heroi_SO.png](heroi/directions/heroi_SO.png) |
| O | [heroi_O.png](heroi/directions/heroi_O.png) |
| NO | [heroi_NO.png](heroi/directions/heroi_NO.png) |

## Formato e validação

Cada direção tem uma folha **192×96**, com células **32×48**: quatro quadros de repouso e duas células vazias na primeira linha; seis quadros de movimento na segunda. A folha mestra **192×768** reúne as oito direções, na ordem N, NE, L, SE, S, SO, O, NO. Há 80 referências de quadro e 16 animações por personagem. Esses PNGs e as prévias são as matrizes completas. Na build atual, cada direção usa somente dois quadros de repouso e quatro de corrida, selecionados sem alterar os pixels ou o alinhamento das matrizes.

PNGs indexados de 4 bits, índice 0 transparente, até 15 cores visíveis, componentes RGB nos oito níveis do Mega Drive e alfa somente 0/255. A referência dos pés é a linha 46 da célula. As prévias são arquivos separados, ampliados por vizinho mais próximo.

Cinco vistas foram desenhadas; SO/O/NO usam espelhamento horizontal de SE/L/NE. Detalhes assimétricos também são espelhados. Não se usa espelhamento vertical para criar frente/costas.

A [revisão visual da câmera](../camera-60-redraw-v2/README.md) compara os PNGs nativos a guias geométricos projetados a **60° acima do chão**. Essa revisão não mede um ângulo 3D exato a partir dos desenhos 2D. Os relatórios técnicos mantêm essa distinção.

- [Validação de PNGs, paleta, quadros, espelhos, empacotamento e ResComp](validation/report.json).
- [Memória da ROM compilada e executada](validation/memory.json).
- [Registro de recorte, fonte e alinhamento por pose](validation/export.json).

O código de produção passou por 600 quadros de estresse: máximo de 80 sprites de hardware, 20 por linha e 320 pixels por linha. A ROM nova foi executada por 1159 quadros no Genesis Plus GX, incluindo Rex nas oito direções e os 13 tipos de inimigo. Isso verifica o emulador e as verificações de software; não é um teste em console físico.

## Memória do conjunto integrado

| Medida | Resultado |
|---|---:|
| ROM final | 510 KiB |
| Capacidade declarada no cabeçalho | 1024 KiB |
| Folga na capacidade declarada | 510 KiB |
| RAM estática | 6165 bytes |
| Heap livre observado | 47332 bytes |
| Maior bloco livre observado | 46818 bytes |
| Cache dos inimigos em VRAM | 10 KiB |
| Um quadro do protagonista em VRAM | 768 bytes |
| Reserva adicional de VRAM deste redesenho | 0 bytes |
| DMA máximo dos personagens por quadro | 5376 bytes |

Os limites H40 são compartilhados com tiros, efeitos, itens e outros sprites. O renderizador omite desenhos de menor prioridade ao atingir os limites; esses números não garantem uma quantidade fixa de personagens simultâneos. Há limite de quatro atualizações de quadro de inimigos mais uma do protagonista por quadro do jogo; sob pressão de DMA a atualização pode ser adiada.

## Origem e reprodução

Arte gerada/editada com **image_gen integrado**. Os prompts exatos estão em `prompts/` e as fontes em `originals/`. Os scripts fazem segmentação por alfa, registro, escala por vizinho mais próximo, conversão para paleta e empacotamento de tiles. Não desenham poses procedurais.

O exportador mantém os binários candidatos em `runtime/`. O jogo usa a seleção compacta de `game/res/actor_animation.json`, gerada diretamente dos PNGs por `game/tools/pack_actor_animation.py`; os candidatos históricos completos em `runtime/` preservam quatro quadros de repouso e seis de corrida. A revisão da câmera é associada ao hash do PNG; se uma nova exportação mudar a imagem, a revisão volta ao estado pendente.

A versão anterior permanece preservada. Os nove mechs de estudo e os placeholders `dummy`/`target` continuam legados. A projeção do cenário permanece a implementação existente.

O protagonista usa PAL2. Os 30 quadros canônicos em uso ocupam 23040 bytes de ROM, mais 32 bytes de paleta; cada quadro utiliza duas peças de hardware, 32×32 e 32×16. O exportador reutiliza a implementação técnica do pacote de inimigos desta mesma versão.

## Desempenho medido

A validação de memória e SAT não comprova FPS. A correção atual recupera 60 FPS com três inimigos na arena com lógica ativa; quinze ainda ficam perto de32 FPS, enquanto a referência ASCII chega a 40 FPS. Com a lógica congelada, a animação/desenho de até dezesseis mantém 60 FPS. Veja a [investigação de CPU](../cangaco-insects-sized-v3/validation/performance/README.md).
