# Damião — protagonista cangaço cyberpunk — sprites v1

O protagonista humano do concept v3 já substitui o mech na partida.
Ele aparece como opção inicial da galeria ASSETS, identificado como
DAMIAO. Os nove mechs antigos permanecem na galeria como
arte legada. O recurso e os arquivos usam o ID heroi.

## Arquivos

- [Spritesheet nativa completa](heroi/heroi.png): 192×768, oito direções.
- [Prévia das oito posições](previews/heroi-8dir-4x.png).
- [Corrida animada](previews/heroi-movimento-4x.gif).
- [Repouso animado](previews/heroi-repouso-4x.gif).
- [Pacote de PNGs, paleta, prévias e prompt](.).
- [Prompt completo](prompts/heroi.txt).
- [Verificação técnica](validation/report.json) e [memória da ROM](validation/memory.json).
- [Galeria no emulador](validation/emulator/hero-gallery.png).

## Formato

Célula fixa 32×48 (4×6 tiles). Cada direção tem uma folha 192×96, com quatro
frames de repouso e duas células vazias na linha 0; seis frames de corrida na
linha 1. A folha completa alterna essas linhas para N, NE, L, SE, S, SO, O, NO.
São 16 animações e 80 referências de frame.

| Direção | Arquivo |
|---|---|
| N | [heroi_N.png](heroi/directions/heroi_N.png) |
| NE | [heroi_NE.png](heroi/directions/heroi_NE.png) |
| L | [heroi_L.png](heroi/directions/heroi_L.png) |
| SE | [heroi_SE.png](heroi/directions/heroi_SE.png) |
| S | [heroi_S.png](heroi/directions/heroi_S.png) |
| SO | [heroi_SO.png](heroi/directions/heroi_SO.png) |
| O | [heroi_O.png](heroi/directions/heroi_O.png) |
| NO | [heroi_NO.png](heroi/directions/heroi_NO.png) |

Os PNGs são indexados de 4 bits, índice 0 transparente, até 15 cores visíveis
numa única paleta RGB de 3 bits. Não há alfa parcial, linhas ou texto nas folhas.
Os pés têm referência na linha 46. As prévias são arquivos separados, ampliados
por vizinho mais próximo.

A [revisão visual de 19/10/2026](../camera-60-audit/README.md) **reprovou a
perspectiva deste conjunto**: as vistas não mantêm a câmera elevada a 60° acima
do chão. Os testes técnicos abaixo não certificam esse requisito; a arte ainda
precisa ser redesenhada.
Foram desenhadas N, NE, L, SE e S. As vistas ocidentais usam simetria horizontal;
isso também espelha o lado dos implantes e da arma. Não há espelhamento vertical
nem rotação plana para gerar frente/costas. O chapéu metálico, a arma de fogo,
a pele exposta e o braço cibernético foram preservados do concept.

## Recursos e integração

A declaração opcional para o Sprite Engine está em [heroi.res](heroi.res):

    SPRITE heroi "heroi/heroi.png" 4 6 FAST 6 NONE BALANCED FAST

Se o PNG for copiado para gfx/heroi.png, use a declaração solicitada originalmente:

    SPRITE heroi "gfx/heroi.png" 4 6 FAST 6 NONE BALANCED FAST

As duas linhas usam o mesmo formato; apenas o caminho muda.
A declaração fornecida foi compilada no ResComp com 16 animações e 80 frames.

O jogo mantém o renderer manual e usa res/heroi.res: frames.bin e palette.bin,
sem duplicar os recursos SPRITE na ROM. O módulo herogfx.c envia um frame de
768 bytes para os primeiros 24 tiles da reserva de 48 tiles do jogador, usando
PAL2. Cada frame usa duas peças: 32×32 e 32×16. O restante da reserva mantém a
compatibilidade com a galeria legada.

Há 50 frames canônicos na ROM (cinco vistas × dez poses), totalizando 38400
bytes, mais 32 de paleta. A atualização do jogador tem prioridade sobre o DMA
dos inimigos. No máximo um frame de jogador e quatro de inimigos são enviados
por quadro: 3840 bytes. Caso a fila esteja cheia, mantém-se o último frame.

A hitbox de movimento continua em coordenadas de chão. O desenho se alinha pelos
pés e os tiros do jogador recebem um deslocamento visual de 16 pixels na altura
da arma; a simulação dos tiros e das colisões permanece no plano de chão.
A galeria usa temporariamente 120 tiles do cache de inimigos, invalidando o
cache para a próxima partida.

## Memória e testes da ROM combinada

- ROM: 917504 bytes (896 KiB), dentro de 1 MiB; 131072 bytes de folga.
- RAM estática: 5124 bytes; o protagonista acrescentou 12 bytes.
- Heap livre observado: 48374 bytes; maior bloco livre de 47860 bytes.
- Frame do protagonista: 768 bytes na VRAM, sem aumentar a reserva existente.
- Cache de frames dos inimigos: 12288 bytes.
- Folga entre os tiles de gameplay e a fonte: 16544 bytes.
- Quatro paletas totais; o protagonista ocupa a PAL2 já reservada ao jogador.

O validador confere dimensões, paleta, alfa, alinhamento, quatro/seis poses
distintas e a emenda dos ciclos. Compara também os PNGs com os bytes 4bpp da ROM.
O código de produção passou por 600 quadros de estresse com jogador, 16 inimigos,
tiros e efeitos, respeitando 80 sprites totais, 20 por linha e 320 pixels por
linha. O teste inclui recusa por orçamento e falha na fila DMA.

O Genesis Plus GX executou a ROM final por 1159 quadros, passando pela galeria
do protagonista e pelas oito direções em uma cena controlada com os 13 inimigos.
Foram observados 37 sprites totais, 13 por linha e 272 pixels por linha.
O relatório registra o hash exato da ROM executada. Só a RAM volátil do emulador
foi modificada para montar a cena controlada. Não houve teste em console físico.

## Procedência e reprodução

Arte gerada com a ferramenta integrada image_gen, usando o concept v3 como
referência. O original permanece em originals/heroi.png. O script exporta os
desenhos fornecidos, remove fragmentos de recorte, registra e reduz por vizinho
mais próximo, depois indexa a paleta; não desenha poses por código.

Verificações técnicas não certificam ângulo geométrico exato, anatomia perfeita
ou fluidez de todas as poses. Os PNGs nativos permanecem disponíveis para revisão
de pixel art. O cenário ainda conserva a projeção anterior.

Na raiz do projeto:

    python3 game/art/cangaco-protagonista-v1/export_sprites.py
    python3 game/art/cangaco-protagonista-v1/validate_sprites.py
    make -C game -j4
    arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-v1/tests/smoke_emulator.py
    python3 game/art/cangaco-insects-v1/audit_memory.py
    python3 game/art/cangaco-protagonista-v1/package_assets.py

O runner Intel corresponde ao núcleo de emulação instalado nesta máquina.
A exportação reutiliza a ferramenta técnica de cangaco-insects-v1.
