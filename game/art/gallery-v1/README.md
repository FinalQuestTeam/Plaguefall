# Galeria de personagens — Rex e Dinorah

O menu **PERSONAGENS** mostra somente **Rex (1/2)** e **Dinorah (2/2)**. ESQ/DIR alterna entre os dois e dá a volta na lista. A, B ou START retorna ao menu principal.

![Dinorah na galeria](emulator/dinorah-idle-0-2x.png)

[Rex na galeria](emulator/rex-idle-0-2x.png) · [ROM atual](../../out/release/rom.bin).

Cada personagem aparece em oito direções, com dois quadros de repouso de 32×48. A animação usa a cadência existente: 24 ticks por quadro em NTSC e 20 em PAL. SO/O/NO usam os espelhos horizontais das vistas SE/L/NE, preservando as matrizes dos sprites aprovados.

## Integração

A galeria é implementada em `src/system/video/screens/chardemo.c`. Os mechs antigos saíram da lista. Seus estudos de arte permanecem no repositório como acervo.

Dinorah usa o [binário reduzido já existente](../cangaco-parceira-iso60-v1/runtime/frames.bin), declarado em `res/dinorah.res`. Os 30 quadros canônicos ocupam 23040 bytes de ROM. A paleta é exatamente a mesma de Rex e usa PAL2.

As cinco vistas e os dois quadros de repouso do personagem em exibição ficam em 240 tiles temporários (7680 bytes), dentro do cache existente de 320 tiles dos inimigos. Uma checagem no compilador impede exceder essa reserva. As oito direções usam 16 sprites de hardware, duas peças por figura. Não há DMA de imagens durante a animação: somente o índice do quadro muda.

Os auxiliares de prévia saíram do módulo de renderização de Rex e passaram para a galeria. A partida continua usando o renderizador e o carregamento de Rex existentes.

## Verificação

- [Teste no Genesis Plus GX](emulator/report.json): navegação pelos dois personagens, volta nas duas direções, duas poses por personagem, oito vistas, espelhos e saída ao menu/início da campanha.
- [Comparação de pixels](pixel-validation.json): as 32 vistas capturadas (2 personagens × 2 poses × 8 direções) correspondem exatamente aos PNGs nativos, considerando a paleta do emulador.
- [Compilação, recursos e memória](build-validation.json).
