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

O arquivo para abrir no emulador é `game/out/release/Plaguefall.bin`. O build também entrega `Plaguefall.png` (arte existente do menu) e `Plaguefall.json` (identificação e hashes). O SGDK continua gerando `game/out/release/rom.bin`, idêntico byte a byte ao arquivo nomeado, para compatibilidade com os testes. Somente `Plaguefall.bin` é versionada como ROM em `game/out/`, acompanhada da capa PNG e dos metadados JSON; `rom.bin` é uma saída local ignorada. Dependências, objetos, símbolos e compilações de variantes são locais e ignorados. `make -C game clean` limpa o build; reconstrua a ROM antes de versionar uma atualização.

## Textos e fonte em português

Escreva os textos exibidos ao jogador em **MAIÚSCULAS COM ACENTOS**, em UTF-8 NFC. O repertório adicional é `ÀÁÂÃÉÊÍÓÔÕÚÇ`; as posições internas `a..l` representam esses caracteres, na mesma ordem. Os nomes de inimigos também usam maiúsculas. A fonte permanece com 96 tiles de 8×8 pixels: 3072 bytes na VRAM, tanto na variante transparente dos painéis quanto na opaca da abertura, mapa e arenas.

O Makefile pré-processa cada unidade C, passa os literais por `tools/encode_text.py` e compila o arquivo `.i` resultante. A conversão acontece depois dos includes e macros; identificadores, formatos como `%s` e `%u`, comentários e mapas de pixels ASCII continuam intactos. Cada letra exibida ocupa um byte na ROM, preservando `strlen`, centralização, quebra de linhas e digitação. Não substitua manualmente as letras acentuadas pelas posições internas nos arquivos de autoria.

Os desenhos dos 12 glifos ficam em `res/text/glyphs.json`. Depois de editá-los, rode `python3 game/tools/build_text_font.py` na raiz para gerar `res/text/font.bin`, `res/intro/font.bin` e a máscara compartilhada por rádio, HUD e resultados. O exportador da abertura utiliza a mesma fonte e conserva os acentos do storyboard. `tools/check.py` verifica a reprodução desses recursos, a codificação compilada e a preservação dos outros 84 glifos.

As capturas e os relatórios desta integração estão em `art/texto-acentuado-v1/validation/`, separados dos registros históricos das interfaces. A abertura foi conferida também pixel a pixel em NTSC/PAL:

```sh
python3 game/art/intro-monologo-v2/verify_pixels.py --capture-root game/art/texto-acentuado-v1/validation
```

## Testes

`python3 game/tools/test_death_rules.py` executa os módulos reais de morte, jogador, tiros, bombas, inventário e itens com ASan/UBSan em 50/60 Hz. Verifica as 20 fases/rotas, a fotografia pré-morte, a remoção do piso 3, bônus finais condicionais, bolsa vazia, inventário cheio, perdas repetidas e recuperação sem duplicação, permanência por mais de 65.535 quadros e reposicionamento seguro. `python3 game/art/bolsa-recuperacao-v1/export.py --check` verifica o sprite 16×16 e o contorno claro. Ambos fazem parte de `check.py`.

`arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py --output /private/tmp/plaguefall-death-ntsc` verifica as políticas nas 20 fases, a bolsa em todas as etapas, seus pixels reais na VRAM e a coleta única; repita com `--pal`. `test_interface_emulator.py` confere as oito páginas de ajuda, incluindo o bornal, no título e na pausa.

`python3 game/tools/test_player_aim.py` verifica o `player.c` de produção com ASan/UBSan, incluindo a parada nas quatro diagonais, soltura dos eixos em ordens diferentes, autofire parado e mudanças intencionais de mira. `arch -x86_64 /usr/bin/python3 game/tools/test_player_aim_emulator.py` confere a ROM real no sandbox, os dois frames de idle na VRAM e a velocidade diagonal dos projéteis; repita com `--pal`. Os testes de emulador não escrevem na RAM do jogo.

`game/tools/check.py` verifica as quatro partituras, o catálogo e a partitura contínua da abertura. Compila e executa os testes do motor real com ASan/UBSan para os três perfis iniciais e para a abertura. Todos os executáveis temporários ficam fora do repositório e são removidos ao terminar.

Os testes de integração usam o Genesis Plus GX instalado:

`arch -x86_64 /usr/bin/python3 game/tools/test_menu_flicker_emulator.py` verifica a troca de seleção no título, salas de teste, configurações, pausa, confirmações, derrota e vitória. Compara cada quadro fora das linhas que podem mudar, detectando apagões e alterações indevidas no fundo; repita com `--pal`. As capturas de falha e o relatório ficam em `/private/tmp/plaguefall-menu-flicker/`. A navegação usa somente o controle; a preparação de derrota e final declara as alterações de RAM.

```sh
arch -x86_64 /usr/bin/python3 game/art/intro-monologo-v2/verify_emulator.py \
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
  game/out/release/Plaguefall.bin
```

## Nome e capa no OpenEmu

O cabeçalho doméstico e internacional da ROM já identifica `PLAGUEFALL`. O nome `rom` vinha do arquivo padrão do SGDK. `release` e `debug` agora executam `tools/package_rom.py` depois de `padROM`, publicando o nome do jogo sem modificar o conteúdo compilado. Confira com `python3 game/tools/package_rom.py --check`.

O OpenEmu guarda nome e imagem na própria biblioteca e tenta obter metadados no OpenVGDB. Uma nova versão pode mudar o hash da ROM, e um jogo em desenvolvimento pode não ser reconhecido nessa base. Uma capa ao lado do `.bin` não é importada automaticamente. Importe `Plaguefall.bin`; na biblioteca, clique com o botão direito no jogo → **Adicionar Arte de Capa…** → selecione `Plaguefall.png`. Entradas antigas podem ser corrigidas em **Renomear Jogo**. [Guia oficial de capas](https://github.com/OpenEmu/OpenEmu/wiki/User-guide:-Box-art).

O OpenEmu pode copiar ROMs para sua biblioteca. Recompilar o projeto não atualiza uma cópia já importada: para testar o build atual, abra o arquivo nomeado recém-gerado. Essa publicação não modifica automaticamente ROMs, saves ou preferências do emulador.

## Recursos substituídos

A [limpeza do runtime](../art/runtime-cleanup-v1/README.md) retirou os antigos mechs, os demais desenhos de insetos substituídos, seis ícones sem uso e a trilha XGM obsoleta. Dinorah usa somente os dez frames de repouso da galeria. Fontes e dados idênticos de cenário são compartilhados; `install_stage_art.py --check` verifica as referências e os pixels aprovados.

## Referências

- [Guia SGDK em português](sgdk-guia.html).
- [GDD](GDD.md), [direção sonora](musica.md) e [inventário de arte](../art/INVENTARIO-SPRITES.md).
- A biblioteca e ferramentas do SDK são construídas separadamente; alterações de arte e de código do jogo não exigem recompilar o SDK.
