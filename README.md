# Plaguefall 🦂

**Shooter de arena top-down para Sega Mega Drive / Genesis**, escrito em C com o [SGDK 2.11+](https://github.com/Stephane-D/SGDK). Sobreviva a ondas de insetos-máquina em 15 fases de campanha e enfrente a **Lacraia**, o chefe da fase final.

**Nova direção visual:** cangaço cyberpunk brasileiro. Os [13 inimigos gigantes](game/art/cangaco-insects-sized-v3/README.md) agora usam tamanhos nativos de 16×16, 24×24 e 32×32 (chefe48×48), oito direções, repouso e movimento, com [redesenho da perspectiva na versão 2](game/art/camera-60-redraw-v2/README.md), comparado visualmente a guias de câmera ortográfica a 60° acima do chão. A ROM atual, com a abertura animada, ocupa **768 KiB**; o cache de inimigos continua em **10 KiB de VRAM**. A abertura foi verificada no emulador em **50/60Hz**. O [protagonista humano Damião](game/art/cangaco-protagonista-iso60-v2/README.md) já substitui o mech na partida e é a opção inicial da galeria, com oito direções e animações. O cenário e a projeção do mapa ainda usam a implementação anterior. As folhas darkspace são estudos históricos.

Nossa Senhora Aparecida substitui a antena24×24 no objetivo PROTEGER, com a mesma lógica e sem aumentar VRAM/RAM. [Dinorah tem sprites32×48 e oito direções](game/art/cangaco-parceira-iso60-v1/README.md) e já aparece ao lado de Damião na [galeria PERSONAGENS](game/art/gallery-v1/README.md). Consulte o [inventário de sprites e pendências](game/art/INVENTARIO-SPRITES.md).

> ROM: `game/out/release/rom.bin` — roda em qualquer emulador de Mega Drive (testado no RetroArch + Genesis Plus GX) e, em teoria, no hardware real.

## O jogo

“Você já ouviu falar que o Diabo dá tudo que a gente quer? Mas sempre da maneira mais filha da puta possível?” Damião sonhava com astronautas, extraterrestres e foguetes que davam ré. Os foguetes voltaram trazendo ninhos — Damião chama os invasores de “baratas” — e agora ele luta por uma resistência humana num Brasil cyberpunk com tons de cangaço e religiosidade popular. Leia a [abertura e os arquivos de história](game/doc/historia/README.md).

Você controla **Damião, humano com implantes**, numa arena de tela única. Inimigos surgem em ondas; a maioria das fases exige **eliminar N inimigos**. Na fase 5, proteja Nossa Senhora Aparecida por 30 segundos; na 16, derrote a Lacraia. Vida persiste entre as fases — administre os itens e atravesse as quatro bifurcações da campanha.

### Controles

| Botão | Em jogo | Em telas |
|---|---|---|
| D-pad | Move nas 8 direções | Navega no menu |
| A | Atira (segure para autofire) | Começa a fase (preparação) |
| B | **Ativa** o item selecionado do inventário | Sai ao título (pausa) |
| C | **Troca** a seleção do inventário | Avança a fase (preparação) |
| START | Pausa / retoma | Confirma |
| A+B+C (segurar) | Pula a fase (debug) | — |

### Sistemas principais

- **16 fases**: 1–15 de campanha (dificuldade crescente, lava/lama como terreno) + **fase 16 só com o chefe** — derrote a Lacraia para ver a tela de fim.
- **14 tipos de inimigo** em uma matriz **forma × cor**: a forma dá a resistência (quadrado tanque / triângulo frágil-veloz / pentágono elite com truque), a cor dá o comportamento (vermelho atira, amarelo persegue, roxo ergue escudo, laranja investe). Elites: leque de tiros, divisão ao morrer, invocação de lacaios e teleporte.
- **Chefe Lacraia** (48×48): 25 HP, invulnerável em ciclos, invoca lacaios, alterna investida com dash e rajadas à distância; resistente à bomba.
- **Inventário de 4 posições** (bomba na posição 0): itens coletados entram na lista; C seleciona, B ativa. Duplicatas ocupam posições próprias.
- **8 itens**: coração (cura), bala (leque até 5), botinha (velocidade), escudo (invencibilidade), raio (reação em cadeia), **gelo** (congela 5 s), **fogo** (queimadura por tempo), bomba (limpa a tela).
- **Feedback**: poça de sangue verde ao matar, flash de tela na bomba, som de dano ao ser atingido por inimigo, contagem "PREPARE-SE" no início da fase.
- **Trilha dinâmica**: chiptune dark original no PSG cujo **BPM sobe com a ameaça** (mais inimigos = mais rápido), com curva ajustável por fase; efeitos e música dividem os canais via um árbitro que evita chiado e nota presa.
- **Fase teste** (sandbox, no menu): 3 estágios ligados por portas — dummies, alvos para o raio e a arena do chefe.

## Assets

Quase toda a arte é **gerada proceduralmente no boot** a partir de *char-maps* (mapas de caracteres) — não há PNG/bitmaps no build, só código e texto. Cada caractere vira um pixel de uma cor da paleta:

```text
INS_BEETLE16 (inimigo 16x16)          INS_BOSS48 (Lacraia 48x48, recorte)
   ....l......l....                      ....................oooooooo....................
   .....llooll.....                      ..................ooobbbbbboooo.................
   ......ebeo......                      ................oobbbbbbbbbbbboo................
   .....obbbbo.....                      ..............oobbbbhhhhhhhhbbbboo..............
   .....oobooo.....                      ..............obbbbhebbbbbbbhebbbo..............
   ....oooooooo....                      ..............obbbbeebbbbbbbeebbbo..............
   ....ohhbobbo....                      ..............obbbbbbbbbbbbbbbbbbo..............
   ..loohhbobbool..                      ...........llllobbbbbbbbbbbbbbbbolll............
```
Legenda típica: `o` contorno, `b` corpo (cor da família), `h` brilho, `e` olhos, `l` patas.

| Asset | Onde | O que é |
|---|---|---|
| Mechs do jogador | `sprites/chars_data.h` | 9 personagens 32×32 (3 famílias × 3 portes), rotacionados em 8 direções na VRAM |
| Insetos (inimigos) | `res/insects.res` + `art/cangaco-insects-v1/` | Serra-pau/mutuca/saúva/escorpião em 32×48, 8 direções, 4 frames de repouso e 6 de movimento |
| Itens | `sprites/items_data.h` | Char-maps 16×16 dos 8 itens |
| Ícones de HUD | `sprites/icons_data.h` | Caveira, bomba, raio, faísca, escudo, gelo, fogo (8×8) |
| Chão da arena | `sprites/floor_data.h` | Padrão 32×32 ladrilhado no BG_B (PAL3) |
| Fundo do título | `sprites/titlebg_data.h` | [Splash da caatinga](game/art/title-caatinga-v1/README.md), Damião, Dinorah, padre e insetos; 320×224, duas paletas por tile |
| Logo da splash | `sprites/logo_data.h` | FinalQuest redesenhado, moldura192×128, letras mais legíveis e exposição de1s |
| Mapa de VRAM | `sprites/tiles.h` | Índice de todos os tiles + regiões (rotações de inimigo, chefe, chars) |

Geradores: `system/video/tilegen.c` (tiles procedurais + paleta), `enemygfx.c` (cache de frames dos insetos, streaming da ROM e cinco vistas canônicas com simetria horizontal), `chars.c` (rotações do mech).

**Áudio**: tudo no PSG (SN76489), sintetizado em tempo real. Um **árbitro** (`system/audio/audio.c`) é a única via de escrita nos 4 canais — música e SFX apenas *requisitam* voz por prioridade a cada quadro, o que resolve as disputas de canal e o chiado. A **música** (`music.c` + `song_data.h`) é um chiptune dark original com **BPM dinâmico** que sobe com a ameaça (nº de inimigos), configurável **por fase**. Os **SFX** (`sfx.c`) — tiro, explosão, coleta, dano e o leito de ruído de lava/lama — preemptam a música e a devolvem ao soltar. Optou-se pelo PSG porque os drivers XGM/PCM conflitam com o uso intenso de DMA (ver §6 do GDD).

## Documentação de design

- **[GDD completo](game/doc/GDD.md)** — visão geral, controles, fluxo, HUD, jogador/tiros/bomba, os 15 tipos de inimigo com valores reais, itens, fases e terreno, áudio e gráficos. Gerado a partir do código: os números refletem a implementação.
- **[Plano de inimigos](game/doc/plano-inimigos.md)** — a matriz forma×cor e a progressão de introdução por fase.
- **[História](game/doc/historia/README.md)** — abertura, universo, personagens e campanha vinculada aos 20 nós existentes. O roteiro da ROM usa 22 cenas, com as duas versões de cada bifurcação e um final comum.
- **[Abertura animada](game/art/intro-monologo-v1/README.md)** — 12 quadros do monólogo de Damião antes do menu, com texto branco centralizado, enquadramento estável e fades; A completa/avança, START pula.
- **[Galeria de personagens](game/art/gallery-v1/README.md)** — Damião e Dinorah em oito direções, com animação de repouso; ESQ/DIR alterna entre os dois.
- **[Splash art e abertura](game/art/title-caatinga-v1/README.md)** — caatinga e personagens no menu, com logo FinalQuest menor e capturas no emulador.
- **[Retratos de conversa](game/art/dialogue-portraits-v1/README.md)** — Damião, Comando (padre) e Dinorah em 48×48, baseados nos concepts, com PNGs, paletas e prévia no emulador.
- **[Sistema de diálogos](game/doc/plano-historia.md)** — formato das cenas, retratos, controles e limites do texto.

## Compilar e rodar

```sh
cd game
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"   # rescomp precisa de Java
make                                                # gera out/release/rom.bin
```

Rodar no RetroArch (core Genesis Plus GX, via Rosetta):

```sh
arch -x86_64 /Applications/RetroArch.app/Contents/MacOS/RetroArch \
  -L "$HOME/Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib" \
  out/release/rom.bin
```

Alternativas: ares (`open -a ares out/release/rom.bin`, nativo arm64) ou BlastEm (tem debugger).

## Estrutura do código

```
game/src/
├── main.c                  # ponto de entrada (sobe o fluxo)
├── core/                   # máquina de estados (flow), inventário, contratos globais
├── actors/                 # jogador, tiros (jogador/inimigo), bomba
├── enemies/                # engine + comportamentos por cor; defs/ = um inimigo por arquivo
├── items/                  # engine + efeito de cada item; defs/ = dados
├── levels/                 # dispatcher, layouts, fase teste; defs/ = uma fase por arquivo
├── elements/               # terreno: lava, lama
└── system/
    ├── audio/              # árbitro do PSG + música (BPM dinâmico) + SFX
    └── video/              # tilegen, sprites/, telas (título, HUD, pausa, ajuda...)
```

Padrão **dado × lógica**: cada inimigo/item/fase tem seu arquivo de dados em `defs/` e a lógica compartilhada no módulo; os char-maps de arte ficam todos em `system/video/sprites/`.

---

# Ambiente de desenvolvimento (macOS / Apple Silicon)

Ambiente completo para desenvolver jogos de Mega Drive em C com o SGDK no macOS.

## Estrutura do repositório

```
MegaDrive/
├── game/                   # O jogo (Plaguefall) — ver acima
│   └── doc/                # Documentação
│       ├── GDD.md          # Game Design Document
│       ├── plano-inimigos.md
│       ├── sgdk-guia.html  # Guia completo da API SGDK em português (abra no navegador)
│       └── fragmentos/     # Fragmentos HTML por módulo (fonte do guia)
├── SGDK/                   # Clone oficial do SGDK (lib compilada em lib/libmd.a)
└── README.md
```

## Ferramentas instaladas

| Ferramenta | Origem | Uso |
|---|---|---|
| `m68k-elf-gcc` 16.1 (+binutils) | Homebrew | Cross-compiler 68000 |
| OpenJDK 26 | Homebrew (keg-only) | rescomp, sizebnd, lz4w (jars do SGDK) |
| `sjasm`, `bintos`, `xgmtool` | compilados de `SGDK/tools` para `SGDK/bin` | Assembler Z80 e conversores |
| CMake | Homebrew | Build das tools do SGDK |
| RetroArch + Genesis Plus GX | retroarch.com (build Intel, roda via Rosetta) | Emulador principal do projeto |
| ares | Homebrew cask (`ares-emulator`) | Alternativa nativa arm64, assinada |

Variáveis no `~/.zshrc` (bloco `SGDK / Mega Drive`): `GDK` aponta para o clone do SGDK e o `PATH` inclui o OpenJDK e `$GDK/bin`.

## Recompilar a biblioteca (só após atualizar o SGDK)

O make apaga os intermediários dos drivers Z80 antes de os `.c` consumirem os headers gerados; pré-gere-os antes:

```sh
cd $GDK
for f in $(find src -name "*.s80"); do
  base=${f%.s80}
  mkdir -p "out/release/$(dirname $base)"
  sjasm -isrc -iinc -iinc/snd -iout/release "$f" "out/release/$base.o80" out/release/out.lst
  bintos "out/release/$base.o80" "out/release/$base.s"
done
java -jar bin/rescomp.jar res/libres.res out/release/res/libres.rs
make -f makelib.gen
```

Se atualizar as tools nativas: `cmake -S . -B build -DCMAKE_SYSTEM_NAME=Generic && cmake --build build` (ignore o passo de arquivamento da lib do CMake no macOS — ele corrompe o `libmd.a`; use sempre o `makelib.gen` acima).

## Documentação do SGDK

- **Guia completo em português**: `game/doc/sgdk-guia.html` — referência função por função de todos os headers, introdução, build e rescomp. Também publicado em: https://claude.ai/code/artifact/669a50c5-a0ce-4c2f-9e12-d300db1b4971
- Doxygen oficial: http://stephane-d.github.io/SGDK/
- Wiki oficial: https://github.com/Stephane-D/SGDK/wiki
- Recursos: leia `SGDK/bin/rescomp.txt` para declarar sprites, imagens, música (.res)
