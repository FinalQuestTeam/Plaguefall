# Ladainha de Ferro

Quarta faixa original de Plaguefall, inspirada em igreja e incorporada em **ASSETS → MÚSICAS**. As três faixas anteriores permanecem disponíveis.

A composição combina frases longas que sugerem canto, harmonia sustentada com articulação de órgão, baixo pedal e entradas agudas como sinos. Os acentos industriais ficam mais presentes em combate. Não há citação de hino existente nem amostras acústicas: tudo é sintetizado no PSG do Mega Drive, sem reverberação.

São 16 compassos de 2/4, em Ré menor, com Dm–Bb–Gm–A7 e resolução final em Dm. O andamento padrão vai de aproximadamente 64,3 a 90 BPM e se mantém em PAL e NTSC; as curvas de ameaça das fases continuam disponíveis.

- Calma, 31 segundos: [MP3](ladainha-calma.mp3) · [WAV](ladainha-calma.wav).
- Combate, 22 segundos: [MP3](ladainha-combate.mp3) · [WAV](ladainha-combate.wav).
- [ROM com Assets e as quatro faixas](../../out/release/rom.bin).
- [Partitura gerada](../../src/system/audio/song_data_church.h) · [Compositor editável](../../tools/compose_music.py).
- [Validação de áudio e preservação](validation.json) · [Interface em NTSC](../gallery-v1/assets-player/ntsc/report.json) · [Interface em PAL](../gallery-v1/assets-player/pal/report.json).

As prévias foram capturadas da ROM de bancada no Genesis Plus GX, com a quarta faixa selecionada pelos controles do jogo. CIMA/BAIXO seleciona na galeria, A pausa/retoma e C alterna calma/combate.

## Reprodução

A partir da raiz do repositório, com as ferramentas SGDK configuradas:

```sh
python3 game/tools/compose_music.py --variant igreja --check
make -C game OUT_DIR=out/assets OUT_DIR_LIB="$PWD/SGDK/out/release"
make -C game/tools/music-bench OUT_DIR=out/assets OUT_DIR_LIB="$PWD/SGDK/out/release"
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --rom game/tools/music-bench/out/assets/rom.bin --track 3 --seconds 31 \
  --output /private/tmp/ladainha-calma.wav
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --rom game/tools/music-bench/out/assets/rom.bin --track 3 --enemies 15 --seconds 22 \
  --output /private/tmp/ladainha-combate.wav
```

O comando de captura usa o núcleo Intel instalado neste ambiente; em outro computador, ajuste o interpretador e o caminho do núcleo conforme `game/tools/music-bench/render_audio.py`.
