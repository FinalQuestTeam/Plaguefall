# Fábrica — validação da ROM integrada

ROM: `bb9955bf90a25dab36aa280281909f5d08d98a0d9b313d8508849d68aa382a16` — 2359296 bytes. NTSC e PAL concluíram com `exitcode: 0` e `passed: true`. Esta revisão foi novamente executada na ROM final; a ROM não foi modificada durante os testes.

| Fase | Insetos | Tiros por grupo | Stress NTSC/PAL | CPU pico NTSC/PAL | Bot FPS NTSC/PAL | Vida final bot NTSC/PAL |
|---|---:|---:|---:|---:|---:|---:|
| 9 | 3 | 4 | 60.00/50.00 | 57.23%/31.05% | 60.00/50.00 | 80/0 |
| 10 | 4 | 6 | 60.00/50.00 | 86.38%/60.55% | 59.00/49.55 | 85/55 |
| 11 | 3 | 6 | 60.00/50.00 | 73.63%/47.56% | 59.95/50.00 | 44/52 |

## Objetivos e colisões

O corredor de 2560 pixels foi concluído por controle, com combate isolado. Os dez ninhos foram destruídos por disparos de A, sem editar seus estados; o contador de mortes comum foi ignorado. Uma bomba atingiu exatamente os dois ninhos no enquadramento inicial, preservando os demais. Pausa e retomada preservaram o progresso. As três válvulas foram abertas por proximidade, e manter A impediu a operação.

Os limites norte, sul, oeste e leste dos três mapas passaram nas sondas por controle. As duas esteiras passaram nas duas fases que compartilham a fábrica. O posicionamento inicial das sondas e o isolamento de combate usam RAM; a tentativa de movimento, disparo ou interação usa somente controle, com guarda contra escrita na RAM.

## Arte no emulador

Foram inspecionadas as imagens reais `9-entry.png`, `9-camera-middle.png`, `9-camera-exit.png`, `10-entry.png` e `11-entry.png`. As fachadas industriais, o portão de destino, as fornalhas, as janelas e as esteiras aparecem de acordo com os mapas convertidos.

A auditoria confirmou também que o índice 0 das paletas é preto, respeitando a transparência do hardware. Comparou todo o atlas da rua (638 tiles, 20416 bytes) e da fábrica (472 tiles, 15104 bytes) diretamente entre ROM e VRAM. Também comparou 1120 células visíveis de BG_B por enquadramento, incluindo 324–475 células com atributos de espelhamento H/V. A entrada, o meio e a pré-saída da rua e as entradas de 10/11 tiveram zero divergências nas duas regiões.

## Limites da amostra de dificuldade

O bot faz uma patrulha curta de movimentos e disparos; ele não tenta completar o objetivo em combate. Na fase 9 PAL, morreu após 15,76 segundos de jogo ativo; o vídeo inclui 1,48 segundo de encerramento da morte. A medição de FPS exclui esse trecho congelado, resultando em 50 FPS ativos. As outras amostras duram vinte segundos. Isso não constitui avaliação humana de dificuldade nem prova de vitória em combate.

O stress prepara, a cada frame, uma formação visível com o teto de inimigos e os dois pools de tiros preenchidos. A saturação separada usa os spawns reais do jogo e confirmou os tetos 3/4/3. FPS é a razão entre frames de simulação e VBlanks emulados, não a velocidade do computador hospedeiro. Não houve teste em console físico.

## Arquivos

- `ntsc/report.json`, `pal/report.json`: resultados completos e hashes das fontes.
- `ntsc/execution.json`, `pal/execution.json`: códigos de saída.
- `ntsc/*-playtest.mp4`, `pal/*-playtest.mp4`: vídeos das três fases.
- `ntsc/9-camera-*.png`, `pal/9-camera-*.png`: fachadas e portão ao longo da câmera.
- Fontes completas e exportação: `../../campaign-whole-scenes-v1/factory/`.
