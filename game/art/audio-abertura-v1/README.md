# O Sonho Atendido — trilha da abertura

Composição original para os [12 planos do storyboard](../../doc/historia/storyboard-abertura.md), integrada ao monólogo de boot de Plaguefall. Tem 89 segundos de música planejada, mais as pequenas cargas entre imagens. Usa somente os três canais de tom e o canal de ruído do PSG, sem samples nem música externa.

[Ouvir em MP3](o-sonho-atendido.mp3) · [WAV capturado da ROM](o-sonho-atendido.wav) · [Vídeo completo no emulador](ntsc/abertura.mp4) · [ROM atualizada](source/game-rom.bin). O vídeo inclui os cartões anteriores e a chegada ao menu; o áudio isolado contém apenas o monólogo, com seus fades e o chiado de rádio já existente. Não há dublagem.

## Direção musical

O motivo de Damião começa em Ré, sobe por Fá e Lá e ganha Si natural na lembrança do foguete, em Ré dórico. Ele reaparece com Si bemol na cena do trabalhador, transformando a promessa em perda. Mi bemol e Dó sustenido trazem atrito quando aparecem os ninhos. O baixo sincopado sugere baião, enquanto notas curtas e ruído periódico criam os estalos de metal.

A reza reduz a densidade e usa vozes sustentadas e uma nota aguda de sino. O chamado do padre começa com dois segundos de espaço para o rádio, depois ganha pulso. A última frase sobe até Ré e resolve em Ré menor, com soltura antes do menu. A composição acompanha a decisão de proteger pessoas sem transformar a apresentação do corpo remendado em fanfarra.

| Plano | Tempo de roteiro | Tratamento |
|---|---|---|
| 01 · A pergunta | 00:00–00:05 | Rádio discreto, silêncio inicial e notas espaçadas. |
| 02 · A promessa | 00:05–00:10 | Linha descendente e atrito de semitom. |
| 03 · O sonho | 00:10–00:18 | Melodia ascendente mais luminosa e baixo sincopado. |
| 04 · Agora | 00:18–00:22 | Retorno grave e seco ao presente. |
| 05 · Quem não voltou | 00:22–00:29 | Frase exposta, baixo sustentado e um clique. |
| 06 · Baratas | 00:29–00:37 | Notas deslocadas e estalos periódicos. |
| 07 · A carga de retorno | 00:37–00:47 | Crescimento de pulsos e percussão industrial. |
| 08 · O trabalhador que ficou | 00:47–00:56 | O tema do sonho retorna com Si bemol. |
| 09 · O preço de ficar | 00:56–01:06 | Frase que sobe, quintas abertas e decisão. |
| 10 · Reza e munição | 01:06–01:13 | Textura de capela, harmonia sustentada e sino. |
| 11 · O chamado | 01:13–01:24 | Espaço para o rádio, seguido de pulso crescente. |
| 12 · Ficar no chão | 01:24–01:29 | Ascensão final, resolução em Ré menor e soltura. |

## Integração

[compose_opening.py](../../tools/compose_opening.py) contém a partitura editável; [opening_data.h](../../src/system/audio/opening_data.h) contém seus eventos gerados. A grade usa quartos de segundo, equivalentes a semicolcheias a60 BPM. Os eventos especificam voz, frequência, duração, volume e articulação. Há sustentação com ataque suave, notas percussivas, sinos sintetizados e ruído metálico.

[opening.c](../../src/system/audio/opening.c) usa um relógio de300 Hz: cinco unidades por quadro NTSC ou seis por quadro PAL. `INTRO_run()` inicia o trecho correspondente ao carregar cada imagem. A completa a legenda e depois avança para a próxima imagem e seu trecho musical; START encerra a sequência. O volume acompanha os32 níveis do fade visual. Cada trecho termina sem loop. A faixa não depende do número de inimigos.

O árbitro continua sendo a única via de escrita no PSG. O breve rádio do padre tem prioridade sobre o ruído musical. Ao terminar, a abertura silencia suas vozes e o fluxo existente inicializa a música do menu. As quatro faixas anteriores, suas partituras e gravações foram preservadas; continuam disponíveis em Assets → Músicas.

## Verificação e reprodução

- [Relatório NTSC](ntsc/report.json) e [PAL](pal/report.json): os12 planos escolhem os12 trechos correspondentes, com áudio distinto e audível; A ressincroniza e START encerra a trilha antes do menu. O teste também percorre cartões, legendas, controles segurados, galeria, missão inicial e retorno da partida. Somente controles e leitura de RAM, sem alteração do estado pelo teste.
- [Validação, hashes e memória](validation.json): áudio real sem clipping e preservação dos arquivos anteriores.
- [Teste nativo](../../tests/audio/opening_test.c): ASan/UBSan, limites dos envelopes,12 trechos distintos, PAL/NTSC, fim sem loop, fades, mudanças antecipadas de plano, prioridade dos SFX e estado da música da campanha preservado. O teste das quatro faixas anteriores também passou.

Na raiz do repositório:

```sh
python3 game/tools/compose_opening.py --check
make -C game OUT_DIR=out/abertura OUT_DIR_LIB="$PWD/SGDK/out/release"
arch -x86_64 /usr/bin/python3 game/art/intro-monologo-v1/verify_emulator.py \
  --rom game/out/abertura/rom.bin --symbols game/out/abertura/rom.out \
  --output /private/tmp/plaguefall-opening-ntsc \
  --opening-audio /private/tmp/o-sonho-atendido.wav --movie
```

Acrescente `--pal` para a segunda região. Neste Mac o núcleo Genesis Plus GX instalado é Intel; ajuste o interpretador em outro ambiente. `--output` mantém as capturas separadas das versões anteriores.
