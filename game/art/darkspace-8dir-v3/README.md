# Plaguefall — sprites dos inimigos

Arquivos organizados pelos mesmos identificadores de `game/src/enemies/defs/`,
na ordem de `ENEMY_DEFS`. Cada pasta reúne a folha completa, as oito direções,
as prévias e o original do respectivo inimigo.

[Baixar o pacote organizado](.).

## Organização

```text
enemies/
  sq_red/
    README.md
    sq_red.png                 # folha completa: 192×768
    sq_red_turntable.png       # oito vistas: 256×48
    directions/
      sq_red_N.png             # 192×96 por direção
      sq_red_NE.png
      sq_red_L.png
      sq_red_SE.png
      sq_red_S.png
      sq_red_SO.png
      sq_red_O.png
      sq_red_NO.png
    previews/
      sq_red_turntable.gif
      sq_red_run.gif
    originals/
      sq_red.png
    validation/
      sq_red_opt.png
  sq_yellow/
  sq_purple/
  sq_orange/
  tri_red/
  tri_yellow/
  tri_purple/
  tri_orange/
  pen_red/
  pen_yellow/
  pen_purple/
  pen_orange/
  dummy/
  target/
  boss/
```

Os originais ficam no projeto; o ZIP inclui os PNGs nativos, prévias, catálogos,
paleta e recursos. `validation/*_opt.png` é uma prévia de divisão em peças de
hardware, não uma spritesheet de produção.

## Correspondência com o código

| Índice | Pasta / arquivo | Nome em EnemyDef | Constante |
|---|---|---|---|
| 0 | [sq_red](enemies/sq_red/README.md) | Torreao | `ENEMY_SQ_RED` |
| 1 | [sq_yellow](enemies/sq_yellow/README.md) | Batedor | `ENEMY_SQ_YEL` |
| 2 | [sq_purple](enemies/sq_purple/README.md) | Baluarte | `ENEMY_SQ_PUR` |
| 3 | [sq_orange](enemies/sq_orange/README.md) | Ariete | `ENEMY_SQ_ORG` |
| 4 | [tri_red](enemies/tri_red/README.md) | Fuzileiro | `ENEMY_TRI_RED` |
| 5 | [tri_yellow](enemies/tri_yellow/README.md) | Cacador | `ENEMY_TRI_YEL` |
| 6 | [tri_purple](enemies/tri_purple/README.md) | Escudeiro | `ENEMY_TRI_PUR` |
| 7 | [tri_orange](enemies/tri_orange/README.md) | Adaga | `ENEMY_TRI_ORG` |
| 8 | [pen_red](enemies/pen_red/README.md) | Artilheiro | `ENEMY_PEN_RED` |
| 9 | [pen_yellow](enemies/pen_yellow/README.md) | Alcateia | `ENEMY_PEN_YEL` |
| 10 | [pen_purple](enemies/pen_purple/README.md) | Fortaleza | `ENEMY_PEN_PUR` |
| 11 | [pen_orange](enemies/pen_orange/README.md) | Meteoro | `ENEMY_PEN_ORG` |
| 12 | [dummy](enemies/dummy/README.md) | Dummy | `ENEMY_DUMMY` |
| 13 | [target](enemies/target/README.md) | Alvo | `ENEMY_TARGET` |
| 14 | [boss](enemies/boss/README.md) | Lacraia | `ENEMY_BOSS` |

A tabela foi derivada dos arquivos C. `catalog.json` e `manifest.json` também
registram o símbolo `ENEMYDEF_*`, a constante, o índice e todos os caminhos.
O identificador anterior da arte está preservado em `legacy_art_id`.
Os prompts originais e as referências foram mantidos como proveniência.

## Formato e direções

- 15 inimigos; **120 folhas por direção** e **15 folhas completas**.
- Célula fixa de **32×48**; quatro frames de repouso e seis de corrida por direção.
- Folha individual **192×96**: duas linhas, com duas células vazias no fim do repouso.
- Folha completa **192×768**: 16 linhas, alternando repouso e corrida de cada direção.
- PNG indexado de 4 bits; paleta compartilhada, até 15 cores visíveis e índice 0 transparente.
- Câmera elevada a 60° como direção artística; frente, costas e laterais desenhadas.

A ordem coincide com `ENEMYGFX_faceDir()` e `FACE_DIR`:

| Direção | Índice | Animação de repouso | Animação de corrida |
|---|---|---|---|
| N | 0 | 0 | 1 |
| NE | 1 | 2 | 3 |
| L | 2 | 4 | 5 |
| SE | 3 | 6 | 7 |
| S | 4 | 8 | 9 |
| SO | 5 | 10 | 11 |
| O | 6 | 12 | 13 |
| NO | 7 | 14 | 15 |

`directions.h` e `directions.json` contêm esse mapeamento.
A animação completa é `2 * direcao + estado`, sendo repouso = 0 e corrida = 1.

## Recursos SGDK

As declarações em [enemies.res](enemies.res) usam os nomes do projeto:

```text
SPRITE enemy8_sq_red "enemies/sq_red/sq_red.png" 4 6 FAST 6 NONE BALANCED FAST
SPRITE enemy8_tri_yellow "enemies/tri_yellow/tri_yellow.png" 4 6 FAST 6 NONE BALANCED FAST
SPRITE enemy8_boss "enemies/boss/boss.png" 4 6 FAST 6 NONE BALANCED FAST
```

Cada recurso tem 16 animações e 80 referências de frame.
`palette.json` e `palette.gpl` fornecem a paleta comum.

## Validação e histórico da arte

A reorganização é feita por movimentação e renomeação de arquivos, sem alteração
dos bytes das imagens. Os hashes antes/depois estão em
[validation/organization.json](validation/organization.json).

A validação confere dimensões, paleta, alfa, células vazias, alinhamento e
equivalência entre folhas individuais e completas; depois compila os novos
caminhos/símbolos no ResComp e lê as contagens das estruturas geradas.
Resultado detalhado em [validation/report.json](validation/report.json).
São 240 animações e 1.200 referências de frame; a versão anterior já havia
compilado com 1 a 3 peças VDP por frame. Os novos caminhos e símbolos também
foram recompilados com sucesso, preservando essas contagens.

Os desenhos foram produzidos com `image_gen`. Os originais gerados acima da
resolução final foram reduzidos por vizinho mais próximo e exportados com alfa
binário e paleta fixa. As vistas não foram obtidas por rotação plana nem
espelhamento vertical. Algumas linhas geradas contêm 11 ou 12 poses; a seleção
de quatro poses iniciais e seis finais está em `validation/export.json`.

O ângulo é um alvo artístico 2D. Anatomia, orientação das armas e giro do tronco
podem variar entre poses de corrida; a arte ainda exige revisão antes da versão
de produção. A validação técnica não certifica a geometria ou a fluidez de cada
desenho. A integração no renderer e os testes da ROM continuam pendentes.

## Ferramentas

Na raiz do repositório:

```sh
python3 game/art/darkspace-8dir-v3/export_sheets.py
python3 game/art/darkspace-8dir-v3/validate_sheets.py
python3 game/art/darkspace-8dir-v3/package_assets.py
```

`organize_by_project.py` registra a migração dos nomes antigos para os
identificadores C. Os pacotes e metadados anteriores à organização ficam
preservados em `validation/`; as versões anteriores de arte continuam em suas
pastas históricas.
