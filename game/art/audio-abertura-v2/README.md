> **Versão anterior preservada.** A abertura atual é a [montagem aprovada de 14 planos e 18 cartelas](../audio-abertura-v3/README.md). Os dados e relatórios abaixo descrevem a revisão anterior.

# O Sonho Atendido — versão contínua

A trilha começa na aparição do logo **Plaguefall** e segue pelo monólogo inteiro, sem reiniciar nas trocas dos12 planos. O arranjo conserva os temas do sonho, dos ninhos, da reza e da decisão final, acrescenta uma introdução de4 segundos para o logo e sustenta o baixo entre as seções.

[Ouvir em MP3](o-sonho-atendido.mp3) · [Áudio real da ROM](o-sonho-atendido.wav) · [Ver o boot com a música contínua](ntsc/abertura.mp4) · [ROM atualizada](../../out/release/Plaguefall.bin). A [primeira versão por planos](../audio-abertura-v1/README.md) permanece arquivada.

**START** pula a abertura e segue ao menu, inclusive durante APRESENTA ou o logo Plaguefall. **A, B e C** não completam legendas, não avançam imagens e não pulam os cartões. Segurar START não confirma uma opção do menu. Os controles dos diálogos da campanha e da galeria continuam próprios dessas telas.

## Continuidade

A versão anterior silenciava o PSG ao carregar cada imagem, zerava a partitura em cada plano e reduzia o volume em todos os fades visuais. Agora existe uma única linha de eventos musicais, com relógio único desde o logo. As imagens não comandam o sequenciador nem seu volume. Há somente uma entrada suave no logo e uma saída no fim da sequência ou ao pular com START.

O relógio roda pelo callback de interrupção vertical, independente das cargas de imagens no laço principal. Ele escreve apenas no PSG, pelo árbitro existente, sem acessar o VDP. A abertura assume o árbitro durante esse intervalo e remove o callback antes de inicializar a música normal do menu. As mudanças de callback e de estado são protegidas contra interrupção.

A grade continua em quartos de segundo, com relógio de300 Hz: cinco unidades por quadro NTSC, seis por quadro PAL. A composição reserva96 segundos:4 de introdução,89 de storyboard e3 de sustentação final para absorver as cargas. A exibição normal termina antes dessa reserva final e aplica seu fade de saída. Não há loop. As quatro músicas anteriores e suas gravações foram preservadas.

## Verificação

- [NTSC](ntsc/report.json) e [PAL](pal/report.json): o relógio musical avança exatamente uma vez por quadro, sem pausas ou resets desde o logo até o fim do monólogo, incluindo todos os fades e cargas de imagem. Também conferem os12 planos, legendas, partículas, A/B/C ignorados, START no cartão/logo/monólogo, botões segurados, menu, galeria e início da campanha. Os testes usam controles e leitura de RAM, sem escrever no estado do jogo.
- [Validação de áudio, memória e hashes](validation.json): gravação audível nas12 transições, sem clipping, e preservação dos arquivos anteriores.
- [Teste nativo](../../tests/audio/opening_test.c): ASan/UBSan, reprodução contínua por94 segundos em50/60 Hz, limite de pausas musicais, final sem loop, fade de START sem reinício, remoção do callback e estado da música normal preservado.

[Partitura editável](../../tools/compose_opening.py) · [Eventos gerados](../../src/system/audio/opening_data.h) · [Motor](../../src/system/audio/opening.c).

Na raiz do repositório, com o SGDK configurado:

```sh
python3 game/tools/compose_opening.py --check
make -C game OUT_DIR=out/abertura-continua OUT_DIR_LIB="$PWD/SGDK/out/release"
arch -x86_64 /usr/bin/python3 game/art/intro-monologo-v1/verify_emulator.py \
  --rom game/out/abertura-continua/rom.bin --symbols game/out/abertura-continua/rom.out \
  --output /private/tmp/plaguefall-continuous-ntsc \
  --opening-audio /private/tmp/o-sonho-atendido.wav --movie
```

Acrescente `--pal` para a segunda região. O núcleo Genesis Plus GX instalado neste Mac é Intel.
