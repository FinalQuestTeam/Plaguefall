# Plaguefall — insetos gigantes — sprites cangaço cyberpunk v1

Treze inimigos convertidos dos concepts e integrados à ROM: serra-pau (sq),
mutuca (tri), saúva-soldado (pen) e escorpião (boss). Os IDs e nomes do projeto
foram preservados; Dummy e Alvo continuam como recursos de teste.

## Entrega

- [Pacote nativo SGDK](.).
- Prévias de [serra-pau](previews/sq-3x.png), [mutuca](previews/tri-3x.png),
  [saúva](previews/pen-3x.png) e [escorpião](previews/boss-3x.png).
- Ciclos animados: [sq](previews/sq-movement-3x.gif),
  [tri](previews/tri-movement-3x.gif), [pen](previews/pen-movement-3x.gif),
  [boss](previews/boss-movement-3x.gif).
- [Validação técnica](validation/report.json), [auditoria de memória](validation/memory.json)
  e [execução no emulador](validation/emulator/report.json).
- ROM compilada: ../../out/release/rom.bin.

## Formato

Cada pasta enemies/ID contém uma folha completa ID.png de **192 × 768 pixels**
e oito folhas directions/ID_DIRECAO.png de **192 × 96**.
A célula fixa é **32 × 48 pixels** (4 × 6 tiles).
Para cada direção, a primeira linha tem quatro frames de repouso e duas células
transparentes; a segunda tem seis frames de movimento.

A ordem é N, NE, L, SE, S, SO, O, NO. A animação na folha completa é
2 × direção + estado, com estado 0 para repouso e 1 para movimento.

Os PNGs são indexados de 4 bits, com índice 0 transparente e uma paleta global
de até 15 cores visíveis. Os componentes de cor são níveis RGB de 3 bits.
Não há alfa parcial, linhas de grade, margem externa ou texto nas folhas.
O contato com o chão está na linha 46 da célula, com margem transparente.
Prévias e GIFs são arquivos separados, ampliados por vizinho mais próximo.

A [revisão visual de 19/10/2026](../camera-60-audit/README.md) **reprovou a
perspectiva dos 13 inimigos**: as vistas não mantêm a câmera a **60° acima do
chão**. A arte ainda precisa ser redesenhada. Os testes técnicos abaixo não
certificam esse requisito. Cinco vistas
foram desenhadas (N, NE, L, SE, S); SO, O e NO usam simetria horizontal.
Não há espelhamento vertical ou rotação plana para criar frente/costas.
A simetria também espelha detalhes assimétricos de equipamento.

## Correspondência

| ID | Nome | Família |
|---|---|---|
| sq_red | Torreão | Serra-pau |
| sq_yellow | Batedor | Serra-pau |
| sq_purple | Baluarte | Serra-pau |
| sq_orange | Aríete | Serra-pau |
| tri_red | Fuzileiro | Mutuca |
| tri_yellow | Caçador | Mutuca |
| tri_purple | Escudeiro | Mutuca |
| tri_orange | Adaga | Mutuca |
| pen_red | Artilheiro | Saúva |
| pen_yellow | Alcateia | Saúva |
| pen_purple | Fortaleza | Saúva |
| pen_orange | Meteoro | Saúva |
| boss | Lacraia | Escorpião |

O escorpião mantém o nome legado Lacraia para preservar a narrativa e os IDs.

## Recursos e integração

A declaração opcional para o Sprite Engine do SGDK fica em enemies.res:

    SPRITE insect_sq_red "enemies/sq_red/sq_red.png" 4 6 FAST 6 NONE BALANCED FAST

As treze declarações foram compiladas pelo ResComp, com **208 animações e 1040
referências de frame**. Elas não são adicionadas ao build de produção, para
evitar duplicar dados e para manter o renderer manual existente.

O jogo usa res/insects.res, com BINs 4bpp sem compressão. Há **650 frames
canônicos na ROM**, cinco direções × dez poses × treze inimigos. O renderer
aplica HFLIP nas três vistas ocidentais. Cada instância ocupa um slot de 24
tiles na VRAM, dividido em uma peça 32 × 32 e outra 32 × 16. Os menus usam
ícones pequenos separados e mantêm a disposição anterior.

O carregador envia até **quatro frames por VBlank (3072 bytes)**, diretamente
da ROM, sem descompactar animações na RAM. Atualizações excedentes aguardam,
com rodízio dos slots; um inimigo recém-criado só aparece após a primeira carga.
Os slots mantêm o último frame disponível quando a fila está cheia.

A paleta dos inimigos compartilha a PAL1 dos objetos existentes, preservando
os índices funcionais de tiros, itens e efeitos. A aparência de cores desses
objetos acompanha a nova paleta; jogador e chão continuam usando PAL2 e PAL3.

O renderer aplica admissão por linha e global a inimigos, itens, tiros e raio:
até **80 sprites**, **20 por linha** e **320 pixels por linha**. Em uma
concentração excessiva, desenhos de prioridade menor podem ser omitidos,
com rodízio dos inimigos. Esses limites não garantem visibilidade simultânea
de todos os personagens.

## Memória verificada na build inicial dos inimigos

A ROM atual também inclui o [protagonista Damião](../cangaco-protagonista-v1/README.md):
896 KiB, 5124 bytes de RAM estática e frame de jogador de 768 bytes na reserva
existente. O relatório memory.json acompanha a ROM atual; a tabela abaixo
preserva os números da integração inicial dos inimigos.

| Recurso | Medida |
|---|---:|
| ROM final, com alinhamento e checksum | 786432 bytes (768 KiB) |
| Capacidade declarada da ROM | 1048576 bytes (1 MiB) |
| Folga no limite declarado | 262144 bytes |
| Dados estáticos de RAM (data + bss) | 5112 bytes |
| Crescimento de RAM estática | 726 bytes |
| Heap livre observado no emulador | 48386 bytes |
| Maior bloco livre observado | 46848 bytes |
| Cache de frames de inimigos na VRAM | 12288 bytes |
| Fim da área de tiles de gameplay | byte 29536 |
| Início da fonte | byte 46080 |
| Folga entre gameplay e fonte | 16544 bytes |
| Redução de VRAM frente ao renderer anterior | 11328 bytes |

A auditoria verifica os bytes dos BINs dentro da ROM e o hash da ROM executada.
O teste com Genesis Plus GX rodou 988 quadros, incluindo as oito orientações em
um cenário controlado com todos os 13 tipos; só a RAM volátil do emulador foi
alterada para montar essa cena. Foram observados no máximo 36 sprites totais,
13 por linha e 272 pixels por linha. O teste de estresse do código de produção
simulou mais 600 quadros com 16 inimigos, tiros e efeitos, atingindo os limites
de 20 sprites e 320 pixels por linha sem ultrapassá-los. Também verificou a
recusa do 81º sprite e falhas de entrada na fila DMA.

Esses resultados valem para esta configuração e não substituem nova auditoria
quando aumentarem entidades, resolução, frames ou outros recursos.
Não houve teste em um console físico.

## Procedência e limites artísticos

Os desenhos foram produzidos com a ferramenta integrada image_gen, a partir
dos concepts. Os originais ficam em originals/ e os prompts completos em
prompts/. A exportação técnica recorta e registra os frames, remove fragmentos desconectados
distantes do corpo ou menores que 3% da silhueta principal, reduz por vizinho mais próximo e mapeia
para a paleta fixa; não desenha poses.

O primeiro atlas do serra-pau tinha oito linhas; foram utilizadas as cinco
vistas canônicas. O escorpião recebeu uma folha adicional para corrigir N e NE.
Essa folha forneceu oito poses por vista: repouso usa 0–3 e movimento usa 2–7,
compartilhando duas poses de passagem entre os estados.
validation/export.json registra recortes, escolhas e escalas.

As checagens verificam formato, alinhamento, diversidade de poses e diferença
entre frames incluindo a emenda do ciclo. Não certificam anatomia perfeita,
ângulo geométrico exato ou fluidez de todas as pernas. Cabe revisão de pixel art
na resolução nativa antes de tratar a arte como final de produção.

Esta pasta contém os inimigos. O protagonista também já foi integrado, com
seus [arquivos próprios](../cangaco-protagonista-v1/README.md). O cenário e a
projeção do mapa conservam a implementação anterior.

## Reprodução

Na raiz do projeto:

    python3 game/art/cangaco-insects-v1/export_sprites.py
    python3 game/art/cangaco-insects-v1/validate_sprites.py
    make -C game -j4
    arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-v1/tests/smoke_emulator.py
    python3 game/art/cangaco-insects-v1/audit_memory.py
    python3 game/art/cangaco-insects-v1/package_assets.py

O comando arch corresponde ao núcleo Intel já instalado nesta máquina.
O runner aceita --core CAMINHO para usar outro núcleo Genesis Plus GX compatível
com a arquitetura do Python. As capturas intermediárias são PPM e o empacotador
gera os PNGs. Pillow, Java, Clang e a toolchain SGDK local são necessários.
O ZIP contém as folhas nativas, prévias, prompts e relatórios; os originais de
geração e as ferramentas de reprodução permanecem no projeto.
