# Bancada de áudio

Ferramenta opcional para ouvir e capturar as quatro músicas da galeria com
o mesmo motor de produção. Substitui a antiga pasta `music-test/` da raiz;
as cópias de músicas externas e os builds experimentais foram removidos.

Na raiz do repositório, com o SGDK configurado:

```sh
make -C game/tools/music-bench OUT_DIR_LIB="$PWD/SGDK/out/release"
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py \
  --track 3 --seconds 31 --output /private/tmp/ladainha.wav
```

ESQ/DIR escolhe a faixa; B volta à primeira; CIMA/BAIXO altera a ameaça;
A alterna a ameaça automática e START reinicia a faixa escolhida. O capturador
aceita `--track 0..3`, `--enemies 0..15` e `--pal`. Neste Mac o núcleo instalado
é Intel, por isso a captura usa Rosetta.

O build em `out/` é local e ignorado pelo Git. Os wrappers de `src/` incluem
diretamente o sequenciador e o árbitro de `game/src/system/audio/`.
Os testes nativos ficam em `game/tests/audio/` e são executados por
`python3 game/tools/check.py`.
