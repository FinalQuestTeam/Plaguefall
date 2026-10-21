# Plaguefall — Baião de Ferrugem

**Distribuição atual na campanha:** as quatro músicas coexistem na ROM e agora são escolhidas por fase. A igreja começa com Ladainha de Ferro; abrigo e despedidas usam Entardecer; investigação usa Breu; avanços industriais usam Baião de Ferrugem. [Mapa completo e justificativas](fases-cenarios.md). Os perfis e ROMs alternativos descritos abaixo permanecem como histórico das composições.

A primeira versão da nova trilha combina inspiração no baião com pulsos industriais. A intenção é ter balanço e identidade nordestina sem perder a tensão da invasão. A melodia é original; não adapta uma música existente.

## O que mudou

A faixa anterior usava Ré menor harmônico, a sequência Dm–C–Bb–A, arpejos constantes e bateria de bumbo/caixa. A nova partitura usa Ré mixolídio, com aproximações cromáticas em Sol sustenido, harmonia D7–C–G–D7 e frases com pausas e antecipações. São 16 compassos de 2/4, com variação na segunda metade e uma volta curta para o começo do loop.

| Voz | Papel na nova trilha |
|---|---|
| PSG 0 | Melodia sincopada, notas com duração própria, sustentação, soltura e vibrato discreto. A articulação sugere uma voz de palheta. |
| PSG 1 | Respostas curtas nos contratempos e pulsos extras quando o cerco aperta. Continua cedendo aos tiros do jogador. |
| PSG 2 | Tônica e quinta com espaços entre ataques e uma pequena queda de altura no início de cada nota. |
| PSG 3 | Baques abafados, estalos secos, ruído periódico metálico e viradas curtas. |

É uma interpretação para o PSG: não há gravações de sanfona, zabumba ou triângulo, nem novos drivers de áudio. O canal periódico usa sua própria frequência e não toma o canal do baixo.

## Escuta

As prévias foram capturadas da ROM da bancada no Genesis Plus GX, com o mesmo motor e a mesma partitura do jogo. Não são uma simulação em sintetizador externo. O MP3 foi apenas codificado a partir do WAV, sem efeitos ou normalização.

- [Versão calma — 100 BPM, aproximadamente 20 segundos](../art/audio-baiao-industrial-v1/baiao-calmo.mp3).
- [Versão de combate — 150 BPM, aproximadamente 14 segundos](../art/audio-baiao-industrial-v1/baiao-combate.mp3).
- [Trilha anterior, para comparação](../art/audio-baiao-industrial-v1/anterior.mp3).
- [Dados das capturas e validação](../art/audio-baiao-industrial-v1/validation.json).

## Dinâmica e integração

Até quatro inimigos, a curva padrão fica em 100 BPM. Com quinze, chega a 150 BPM. A ameaça também acrescenta pulsos de acompanhamento e reforça ataques metálicos, preservando o desenho rítmico. A fase 6B usa aproximadamente 112–150 BPM; o Escorpião usa aproximadamente 129–180 BPM.

O relógio musical usa 300 unidades por segundo: cinco por quadro NTSC, seis por quadro PAL. Assim, os valores `musStepCalm` e `musStepHot` continuam sendo durações nominais de quadros NTSC, com o mesmo andamento nas duas regiões. A consulta `MUSIC_stepInBar()` agora retorna 0–7, correspondente ao compasso 2/4.

O árbitro de áudio continua sendo a única via de escrita no PSG. A prioridade é ambiente < música < efeitos < alertas; a música volta a requisitar a voz após o efeito terminar.

## Partitura e bancada

Edite os dezesseis compassos em [compose_music.py](../tools/compose_music.py). Cada coluna é uma semicolcheia: `.` deixa a voz anterior terminar; `D5:2` toca Ré por duas colunas, com uma curta soltura. Execute da raiz do projeto:

```sh
python3 game/tools/compose_music.py
python3 game/tools/compose_music.py --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game/tools/music-bench -j4
```

A bancada `game/tools/music-bench` inclui diretamente o motor e a partitura de `game/src/system/audio`, evitando manter uma cópia independente. CIMA/BAIXO muda o número de inimigos; A liga a subida/descida automática; START reinicia o sequenciador.

Para gravar a ROM da bancada com o core Intel instalado neste Mac:

```sh
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --output /private/tmp/baiao-calmo.wav --seconds 20
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --output /private/tmp/baiao-combate.wav --seconds 14 --enemies 15
```

O gravador verifica que o áudio não ficou silencioso e aceita `--pal` para capturar a outra região.

## Verificação

O teste de áudio compila o sequenciador e o árbitro reais com chamadas PSG instrumentadas. Confere o andamento em PAL/NTSC, a faixa válida dos envelopes, voltas do loop, curvas extremas, silêncio e prioridade/retomada dos efeitos:

```sh
cc -std=c99 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -Igame/tests/audio -Igame/src/system/audio \
  game/tests/audio/music_test.c game/src/system/audio/music.c \
  game/src/system/audio/audio.c -o /private/tmp/plaguefall-music-test
/private/tmp/plaguefall-music-test
```

A validação no emulador também percorre a abertura, o menu, os personagens e o início do combate nas duas regiões.

## Variação preservada — Entardecer

[Entardecer](../art/audio-baiao-melancolico-v1/README.md) é uma alternativa mais melancólica, com partitura própria em `song_data_melancholic.h`. Usa Ré dórico, melodia em registro mais baixo, notas mais longas, mais pausas e a harmonia Dm(add9)–C(add9)–G(add9)–Am7. O andamento padrão vai de 90 a aproximadamente 129 BPM; as curvas específicas de fase continuam valendo.

As prévias anteriores permanecem nos mesmos arquivos. Sua partitura, gerador, motor e ROM de bancada também foram arquivados em `game/art/audio-baiao-industrial-v1/source/`; a ROM original do jogo foi guardada em `game/out/baiao-industrial-v1/rom.bin`.

Para gerar apenas a partitura alternativa:

```sh
python3 game/tools/compose_music.py --variant melancolico
python3 game/tools/compose_music.py --variant melancolico --check
```

O jogo com Entardecer foi compilado separadamente em `game/out/melancolico/rom.bin`, com `MUSIC_MELANCHOLIC=1`. A compilação padrão e a ROM em `game/out/release/rom.bin` continuam com a versão original. As instruções completas de compilação e captura estão no [pacote da variação](../art/audio-baiao-melancolico-v1/README.md).

## Terceira variação — Breu

[Breu](../art/audio-baiao-sombrio-v1/README.md) intensifica o caráter sombrio: melodia e acompanhamento mais graves, tensão entre Ré e Mi bemol, vibrato contido e mais espaços entre os ataques metálicos. Usa a harmonia Dm(b9)–Eb(add9)–Bb(add9)–A7(b9), com andamento padrão de 75 a 112,5 BPM. As curvas próprias de cada fase continuam valendo.

As três versões têm partituras, gravações e ROMs separadas:

| Versão | Partitura | Perfil de compilação | ROM |
|---|---|---|---|
| Baião de Ferrugem | `song_data.h` | Padrão | `game/out/release/rom.bin` |
| Entardecer | `song_data_melancholic.h` | `MUSIC_MELANCHOLIC=1` | `game/out/melancolico/rom.bin` |
| Breu | `song_data_dark.h` | `MUSIC_DARK=1` | `game/out/sombrio/rom.bin` |

`python3 game/tools/compose_music.py --variant sombrio` exporta somente Breu; acrescente `--check` para conferir sua partitura. Os arquivos e as ROMs das duas versões anteriores foram mantidos sem alterações. A reprodução e a captura da terceira estão documentadas no [pacote de Breu](../art/audio-baiao-sombrio-v1/README.md).

## Audição no jogo — terceira aba de ASSETS

A ROM atual inclui as quatro partituras simultaneamente: Baião de Ferrugem, Entardecer, Breu e Ladainha de Ferro. Na galeria, ESQ/DIR percorre Damião, Dinorah e Músicas. Na terceira aba, CIMA/BAIXO escolhe a faixa e inicia sua reprodução; A pausa/retoma e C alterna calma/combate. B ou START sai. A audição não escolhe uma nova trilha permanente para a campanha.

O catálogo `song_catalog_data.h` deriva das quatro partituras. `python3 game/tools/compose_music.py --catalog` o exporta e `--catalog --check` verifica a reprodução exata. Exportar uma partitura individual também atualiza o catálogo, sem reescrever as outras partituras individuais.

O motor seleciona os dados, o andamento e o vibrato de cada faixa em tempo de execução. A primeira chamada a `MUSIC_previewTrack()` guarda a reprodução e a curva de ameaça em uma estrutura fixa, sem alocação dinâmica. As trocas seguintes reiniciam a faixa escolhida. `MUSIC_endPreview()` restaura o estado salvo; o teste nativo compara as frequências e os envelopes seguintes aos da reprodução sem audição. Os [testes da galeria](../art/gallery-v1/README.md) também gravam as quatro faixas, verificam silêncio ao pausar e percorrem o retorno à campanha em 50 e 60 Hz.

## Quarta faixa — Ladainha de Ferro

[Ladainha de Ferro](../art/audio-igreja-v1/README.md) é uma composição original inspirada na sonoridade de igreja: frases lentas que sugerem canto, harmonia sustentada com articulação de órgão, baixo pedal e notas agudas como sinos. O tom é Ré menor, com Dm–Bb–Gm–A7 e resolução final em Dm. O andamento padrão vai de aproximadamente 64,3 a 90 BPM; as curvas próprias de fase continuam valendo. Os acentos de combate mantêm o caráter industrial do jogo.

A faixa usa somente síntese PSG, sem amostras de órgão, sinos ou reverberação, e não cita um hino existente. Sua partitura fica em `song_data_church.h`, exportada com `python3 game/tools/compose_music.py --variant igreja`. Ela aparece como quarta entrada em **ASSETS → MÚSICAS**; as três partituras e os pacotes de gravação anteriores foram preservados.

## Trilha da abertura — O Sonho Atendido

[O Sonho Atendido](../art/audio-abertura-v3/README.md) foi ajustada para os14 planos e18 cartelas do storyboard e substitui a música de fundo reaproveitada durante o monólogo de boot. A versão contínua tem4 segundos iniciais para o logo Plaguefall,101 segundos para o monólogo e uma sustentação final, com tema ascendente no sonho, sua transformação na cena do trabalhador, tensão metálica na carga e nos insetos, uma pausa de capela na reza e pulso crescente após o chamado do padre. O final resolve em Ré menor.

É uma partitura própria em `opening_data.h`, gerada por `tools/compose_opening.py`, com execução em `opening.c`. A partitura roda uma única vez, desde o logo Plaguefall, por interrupção vertical. As cargas de imagem e os fades visuais não reiniciam, pausam ou silenciam a música. Somente START pula a abertura; A, B e C não afetam as legendas ou a sequência. O relógio de300 Hz mantém a duração em PAL e NTSC, usando o mesmo árbitro PSG. As quatro faixas de galeria e campanha permanecem intactas. [Ouvir](../art/audio-abertura-v3/o-sonho-atendido.mp3) · [Ver com a abertura](../art/intro-monologo-v2/emulator-ntsc/abertura.mp4).
