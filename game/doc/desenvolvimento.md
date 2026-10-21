# Desenvolvimento e validação

O jogo usa C, SGDK e um compilador `m68k-elf-gcc`. No ambiente macOS deste projeto, OpenJDK fornece os JARs `rescomp` e `sizebnd`; a captura no Genesis Plus GX usa Python Intel via Rosetta.

## SDK e build

O SGDK é um submódulo fixado pelo repositório. Em um clone novo, inicialize-o:

```sh
git submodule update --init SGDK
```

O Makefile procura `SGDK/` na raiz e também consegue reutilizar o SDK da checkout principal em uma worktree. `GDK` pode apontar explicitamente para outra instalação. O ambiente atual tem as ferramentas nativas em `SGDK/bin` e a biblioteca `SGDK/lib/libmd.a` compilada. As mudanças locais dos binários do SDK não fazem parte do jogo; seu estado de trabalho é ignorado pelo Git do projeto, mantendo o commit do submódulo fixado.

Na raiz:

```sh
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
make -C game -j4 OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/tools/check.py
```

A ROM principal é `game/out/release/rom.bin`. Somente essa ROM de distribuição é versionada em `game/out/`. Dependências, objetos, símbolos e compilações de variantes são locais e ignorados. `make -C game clean` limpa o build; reconstrua a ROM antes de versionar uma atualização.

## Testes

`game/tools/check.py` verifica as quatro partituras, o catálogo e a partitura contínua da abertura. Compila e executa os testes do motor real com ASan/UBSan para os três perfis iniciais e para a abertura. Todos os executáveis temporários ficam fora do repositório e são removidos ao terminar.

Os testes de integração usam o Genesis Plus GX instalado:

```sh
arch -x86_64 /usr/bin/python3 game/art/intro-monologo-v1/verify_emulator.py \
  --rom game/out/release/rom.bin --symbols game/out/release/rom.out \
  --output /private/tmp/plaguefall-intro-ntsc \
  --opening-audio /private/tmp/plaguefall-intro-ntsc/opening.wav
arch -x86_64 /usr/bin/python3 game/art/gallery-v1/verify_music_tab.py \
  --rom game/out/release/rom.bin --symbols game/out/release/rom.out \
  --output /private/tmp/plaguefall-gallery-ntsc
```

Repita com `--pal` e outro diretório de saída para a segunda região. `--movie` no teste da abertura grava o boot real. Os testes enviam comandos do controle e leem estado; não escrevem na RAM do jogo. Ajuste o interpretador e `--core` se o núcleo instalado tiver outra arquitetura.

A [bancada de áudio](../tools/music-bench/README.md) é opcional e compartilha o motor do jogo. Substitui a antiga pasta `music-test/` da raiz. Saídas de captura devem ir para uma pasta temporária. Capturas repetidas de cada quadro e gravações PAL de conferência são regeneradas pelos testes, sem cópias redundantes no repositório. Prévias musicais aprovadas, partituras, artes e relatórios de referência ficam em `game/art/`; não são intermediários de compilação. Relatórios antigos registram a revisão que foi testada, não o estado atual da ROM. O [relatório consolidado atual](build-validation.json) identifica a ROM principal pelo SHA-256.

## Reprodução

```sh
arch -x86_64 /Applications/RetroArch.app/Contents/MacOS/RetroArch \
  -L "$HOME/Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib" \
  game/out/release/rom.bin
```

## Referências

- [Guia SGDK em português](sgdk-guia.html).
- [GDD](GDD.md), [direção sonora](musica.md) e [inventário de arte](../art/INVENTARIO-SPRITES.md).
- A biblioteca e ferramentas do SDK são construídas separadamente; alterações de arte e de código do jogo não exigem recompilar o SDK.
