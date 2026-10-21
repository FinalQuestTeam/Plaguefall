# Baião de Ferrugem — Entardecer

Variação mais melancólica da trilha de Plaguefall. A primeira versão continua preservada em [audio-baiao-industrial-v1](../audio-baiao-industrial-v1/README.md), incluindo prévias, partitura, motor e ROM da bancada no diretório `source/`.

Entardecer usa Ré dórico: a terça menor e as frases descendentes dão uma cor mais triste; a sexta maior mantém alguma abertura. A melodia tem registro mais baixo, notas mais longas e menos ataques. A harmonia é Dm(add9)–C(add9)–G(add9)–Am7. O padrão de tônica/quinta e as síncopes do baião continuam presentes; a percussão deixa mais espaço e mantém os acentos industriais no combate.

O andamento padrão é 90 BPM na calma e aproximadamente 129 BPM no cerco máximo. As curvas próprias da retirada e da Lacraia continuam tendo seus valores específicos.

- [Ouvir a versão calma — 22 segundos](entardecer-calmo.mp3) / [WAV](entardecer-calmo.wav).
- [Ouvir a versão de combate — 16 segundos](entardecer-combate.mp3) / [WAV](entardecer-combate.wav).
- [ROM do jogo com Entardecer](source/game-rom.bin).
- [Partitura](../../src/system/audio/song_data_melancholic.h).
- [Dados das capturas e validação](validation.json).

As gravações são saídas do Genesis Plus GX executando a ROM da bancada com a partitura e o motor reais do jogo. Não há efeitos ou alteração de velocidade aplicados aos WAVs; os MP3s são apenas versões comprimidas.

## Reproduzir

Da raiz do projeto:

```sh
python3 game/tools/compose_music.py --variant melancolico
python3 game/tools/compose_music.py --variant melancolico --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4 \
  OUT_DIR=out/melancolico OUT_DIR_LIB="$PWD/SGDK/out/release" \
  EXTRA_FLAGS='-Isrc -DMUSIC_MELANCHOLIC=1'
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game/tools/music-bench -j4 \
  OUT_DIR=out/melancolico OUT_DIR_LIB="$PWD/SGDK/out/release" \
  EXTRA_FLAGS='-Isrc -DMUSIC_MELANCHOLIC=1'
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --rom game/tools/music-bench/out/melancolico/rom.bin \
  --output /private/tmp/entardecer-calmo.wav --seconds 22
```

Sem a definição `MUSIC_MELANCHOLIC`, a compilação padrão continua usando a versão original. `compose_music.py --check` também continua verificando a partitura original; a variante tem um cabeçalho próprio e não o substitui.
