# Plaguefall

Shooter de arena para **Sega Mega Drive / Genesis**, escrito em C com o SGDK. Damião, um trabalhador com prótese cibernética, protege uma comunidade do sertão industrial dos insetos trazidos por foguetes. A direção mistura cangaço, cyberpunk brasileiro e religiosidade popular.

![Menu de Plaguefall](game/art/menu-logo-v1/menu-3x.png)

[Baixar a ROM](game/out/release/rom.bin) · [Ver a abertura](game/art/audio-abertura-v2/ntsc/abertura.mp4) · [GDD](game/doc/GDD.md)

## Estado atual

- **Damião** é o protagonista jogável, com oito direções e animações de repouso e movimento. **Dinorah** aparece na galeria e nas conversas da campanha.
- **Campanha:** 16 etapas por partida, representadas por20 nós e quatro bifurcações. Há13 inimigos de combate, incluindo o chefe **Lacraia**, e dois tipos de treino. Os objetivos incluem eliminar ondas, sobreviver, coletar itens e proteger Nossa Senhora Aparecida.
- **Abertura:** FinalQuest → APRESENTA → logo Plaguefall → monólogo ilustrado em12 planos → menu. A música **O Sonho Atendido** começa no logo Plaguefall e segue continuamente pelas imagens. Somente **START** pula; A, B e C não completam textos nem avançam cenas. A abertura toca uma vez por boot.
- **Menu Assets:** três abas — Damião, Dinorah e Músicas. Permite ouvir **Baião de Ferrugem**, **Entardecer**, **Breu** e **Ladainha de Ferro**, com pausa e alternância entre calma e combate. Sair da audição restaura a música anterior.
- **Áudio:** síntese PSG em tempo real, com ritmo e acentos de combate ligados à ameaça. As versões nordestina industrial, melancólica, sombria e de inspiração em igreja permanecem preservadas.
- **Arte:** personagens32×48, inimigos16/24/32 pixels e chefe48×48, oito direções e perspectiva elevada. Os recursos ativos são exportados para tiles, paletas e frames na ROM; parte do cenário e dos efeitos continua procedural.
- **ROM principal:**896 KiB, conferida no Genesis Plus GX em PAL e NTSC. Memória estática e hash estão no [relatório de build](game/doc/build-validation.json).

A revisão narrativa sobre a fuga da igreja, o resgate e a demolição dos ninhos está documentada como **proposta**, ainda não aplicada integralmente à campanha. Consulte [História](game/doc/historia/README.md) para distinguir o roteiro executável do tratamento futuro.

## Controles

| Botão | Partida | Outras telas |
|---|---|---|
| Direcional | Move em oito direções | Navega no menu e nas abas de Assets |
| A | Atira; segurar ativa autofire | Inicia a fase; completa/avança diálogos da campanha |
| B | Usa o item selecionado | Na pausa, volta ao título; em Assets, sai |
| C | Troca o item selecionado | Na preparação, percorre fases para depuração |
| START | Pausa/retoma | Confirma no menu; pula a abertura e as conversas |
| A+B+C segurados | Pula a fase para depuração | — |

**Durante o boot, somente START tem ação.** Na aba Músicas, CIMA/BAIXO escolhe a faixa, A pausa/retoma e C alterna calma/combate. ESQ/DIR troca de aba; B/START sai. A faixa da galeria não muda permanentemente a trilha da campanha.

## Itens

| Item | Efeito |
|---|---|
| Marmita do abrigo | Recupera15 pontos de vida |
| Divisor de disparo | Adiciona projéteis, até cinco por disparo |
| Servo de passada | Aumenta a velocidade |
| Carga de desmonte | Explosão de área |
| Capacitor de proteção | Invencibilidade temporária |
| Bobina de subestação | Tiros com reação em cadeia |
| Refil de arrefecimento | Congela inimigos |
| Refil de maçarico | Aplica queimadura |

Os três primeiros têm efeito na coleta; os demais usam o inventário. C seleciona e B ativa. A vida persiste entre fases. A opção **Fase Teste** permanece no jogo como sandbox de desenvolvimento.

## Compilar e conferir

Requisitos: SGDK, `m68k-elf-gcc`, Make, Java e Python3. No macOS deste projeto:

```sh
git submodule update --init SGDK
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
make -C game -j4 OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/tools/check.py
```

O build gera **`game/out/release/rom.bin`**, a única ROM principal versionada. Os testes nativos usam uma pasta temporária e verificam partituras, PAL/NTSC, envelopes, prioridade dos efeitos, as quatro faixas e a continuidade da abertura. [Configuração, emulador e testes de integração](game/doc/desenvolvimento.md).

## Organização

```text
game/
├── src/                 # código do jogo, telas, áudio e renderização
├── res/                 # recursos usados pelo SGDK
├── art/                 # fontes, exports, prévias e relatórios de arte/áudio
├── doc/                 # design, história e desenvolvimento
├── tests/audio/         # testes nativos mantidos
├── tools/               # geradores e validação
│   └── music-bench/     # bancada opcional; compartilha o áudio de produção
└── out/release/rom.bin  # ROM principal; demais saídas são locais
SGDK/                    # submódulo do SDK
```

Compilações experimentais, objetos, dependências e arquivos de sistema foram retirados do versionamento. As músicas preservadas e as artes de referência continuam em `game/art/`; relatórios históricos descrevem suas respectivas revisões.

## Documentação

- [GDD](game/doc/GDD.md) · [Desenvolvimento e validação](game/doc/desenvolvimento.md).
- [História e campanha](game/doc/historia/README.md) · [Storyboard](game/doc/historia/storyboard-abertura.md).
- [Direção sonora e partituras](game/doc/musica.md) · [Abertura com música contínua](game/art/audio-abertura-v2/README.md).
- [Assets e galeria musical](game/art/gallery-v1/README.md) · [Inventário de sprites](game/art/INVENTARIO-SPRITES.md).
- [Itens e ícones atuais](game/art/cangaco-itens-v2/README.md) · [Arte do projeto](game/art/README.md).
- [Guia SGDK em português](game/doc/sgdk-guia.html).
