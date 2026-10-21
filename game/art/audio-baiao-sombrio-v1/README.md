# Baião de Ferrugem — Breu

Terceira variação da trilha de Plaguefall, mais sombria que Entardecer. As duas versões anteriores continuam preservadas, com partitura, prévias e ROMs próprias.

A melodia desce de registro, mantém notas longas e aproxima Ré e Mi bemol para criar tensão. O Si bemol e a dominante alterada reforçam o caráter sombrio. A harmonia é Dm(b9)–Eb(add9)–Bb(add9)–A7(b9), com dois compassos de 2/4 por acorde e variação na segunda metade. O acompanhamento fica mais grave, o vibrato é mais contido e a percussão metálica deixa mais silêncio entre os ataques. A alternância de baixo e as síncopes continuam sustentando o baião.

O andamento padrão é **75 BPM** na calma e **112,5 BPM** no cerco máximo. As curvas próprias da retirada e da Lacraia continuam valendo. O PSG é o mesmo: não há amostras acústicas nem efeitos adicionados à gravação.

- [Ouvir Breu — calma, 26 segundos](breu-calmo.mp3) / [WAV](breu-calmo.wav).
- [Ouvir Breu — combate, 18 segundos](breu-combate.mp3) / [WAV](breu-combate.wav).
- [ROM separada com Breu](source/game-rom.bin).
- [Partitura](../../src/system/audio/song_data_dark.h).
- [Validação e dados das capturas](validation.json).
- [Primeira versão — Baião de Ferrugem](../audio-baiao-industrial-v1/README.md).
- [Segunda versão — Entardecer](../audio-baiao-melancolico-v1/README.md).

As prévias foram gravadas no Genesis Plus GX executando a ROM da bancada com o motor e a partitura reais. Os MP3s foram codificados dos WAVs sem normalização, mudança de velocidade ou outros efeitos.

## Reproduzir

Da raiz do projeto:

```sh
python3 game/tools/compose_music.py --variant sombrio
python3 game/tools/compose_music.py --variant sombrio --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4 \
  OUT_DIR=out/sombrio OUT_DIR_LIB="$PWD/SGDK/out/release" \
  EXTRA_FLAGS='-Isrc -DMUSIC_DARK=1'
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game/tools/music-bench -j4 \
  OUT_DIR=out/sombrio OUT_DIR_LIB="$PWD/SGDK/out/release" \
  EXTRA_FLAGS='-Isrc -DMUSIC_DARK=1'
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --rom game/tools/music-bench/out/sombrio/rom.bin \
  --output /private/tmp/breu-calmo.wav --seconds 26
```

Use `--enemies 15` para gravar o combate e `--pal` para capturar a região PAL. Compile apenas um perfil por vez: `MUSIC_DARK=1` seleciona Breu, `MUSIC_MELANCHOLIC=1` seleciona Entardecer, e a ausência das duas definições mantém a versão original.

Os três perfis passaram nos testes do motor real com ASan/UBSan: relógio PAL/NTSC, loops, envelopes, prioridade dos efeitos, retomada da música e silêncio. As duas versões anteriores foram conferidas por SHA-256 e não foram sobrescritas.
