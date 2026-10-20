# Inimigos — Darkspace / Steampunk — v1

15 inimigos reinterpretados como soldados e autômatos de ficção científica sombria,
com aço, latão, caldeiras, pistões e armaduras inspiradas nos insetos originais.
Artes geradas com a ferramenta integrada `image_gen`; prompts completos em
`manifest.json`. As referências são estéticas; não são personagens licenciados.

## Entrega

- `gfx/`: 15 PNGs **indexados de 4 bits, 192×96**, fundo transparente no índice 0.
- Cada folha: **6×2 células de 32×48**, equivalentes a **4×6 tiles**.
- Linha 0: **4 frames de repouso + 2 células totalmente transparentes**.
- Linha 1: **6 frames de corrida**, todos voltados para a direita.
- `palette.json`: 16 entradas fixas, RGB e palavras de cor VDP `0xBGR`.
- `palette.gpl`: mesma paleta para importação em editor de pixel art.
- `enemies.res`: as 15 declarações de recursos, separadas das imagens.
- `previews/*-6x.png`: folhas ampliadas 6× por vizinho mais próximo.
- `previews/roster-4x.png`: catálogo com uma pose de cada inimigo.
- `previews/roster-idle.gif` e `roster-run.gif`: prévias dos ciclos, ampliadas 4×.
- `originals/`: cópias intactas das imagens geradas, acima da resolução nativa.
- `validation/report.json`: verificações das exportações finais.
- `validation/rescomp.log`: compilação real dos recursos pelo SGDK local.

Os fundos, nomes e composição de apresentação existem apenas nas prévias.
Os PNGs de `gfx/` não contêm rótulos, grade, cenário ou margens externas à grade.

## Personagens

| Arquivo | Inimigo | Identidade visual |
|---|---|---|
| `torreao.png` | Torreão | Atirador vermelho pesado, caldeira e canhão compacto |
| `batedor.png` | Batedor | Perseguidor amarelo com armadura de besouro |
| `baluarte.png` | Baluarte | Tanque roxo, ombreiras e armadura reforçada |
| `ariete.png` | Aríete | Soldado laranja de investida e pistões |
| `fuzileiro.png` | Fuzileiro | Atirador vermelho ágil, visor angular e rifle |
| `cacador.png` | Caçador | Interceptor amarelo com estruturas de mosca |
| `escudeiro.png` | Escudeiro | Interceptor roxo com escudo de antebraço |
| `adaga.png` | Adaga | Assassino laranja com lâminas curtas |
| `artilheiro.png` | Artilheiro | Elite vermelha com canhão de três tubos |
| `alcateia.png` | Alcateia | Elite amarela com cápsulas de drones |
| `fortaleza.png` | Fortaleza | Comandante roxo blindado, pods e caldeira |
| `meteoro.png` | Meteoro | Elite laranja com bobina de teleporte |
| `dummy.png` | Dummy | Autômato cinza pesado com alvo de latão |
| `alvo.png` | Alvo | Autômato cinza leve, juntas expostas |
| `lacraia.png` | Lacraia | Chefe vermelho, elmo com chifres e placas segmentadas |

## Verificações realizadas

As 15 folhas compartilham exatamente a mesma paleta de até 15 cores visíveis,
com entradas constantes entre frames e personagens. Os componentes RGB pertencem
à escala de oito níveis `[0,36,73,109,146,182,219,255]`, convertida para os níveis
VDP de três bits por componente. Não há alfa intermediário nem dithering de exportação.

Foram conferidos tamanho, profundidade de 4 bits, índice transparente, paleta,
duas células vazias, presença de 10 poses distintas e limites de cada célula.
A base dos pés no repouso fica em `y=46`; a referência horizontal fica em
`x=16`, com arredondamento de até meio pixel nas poses de repouso. A corrida
permite deslocamento da silhueta e elevação intencional nas poses de suspensão.

O **ResComp 4.02** compilou as 15 definições e reconheceu **4 + 6 frames em cada
inimigo**, totalizando **150 frames**, com **1 a 3 peças VDP por frame**.
Isso verifica os recursos individualmente; não é um teste da capacidade de uma
cena completa com inimigos, tiros, jogador e efeitos simultâneos.

## Limites da geração e revisão artística

A ferramenta não respeitou a resolução final nem a paleta solicitada nos
originais. Portanto, **estas artes não foram desenhadas originalmente em 32×48**.
As entregas técnicas foram extraídas das poses geradas, reduzidas por vizinho
mais próximo, alinhadas, convertidas para alfa binário e mapeadas para uma única
paleta. Os originais foram preservados para comparação.

A revisão visual das folhas e a comparação de cada transição, incluindo o retorno
do último frame ao primeiro, identificam esta entrega como **primeira versão de
arte**, não como animação artesanal finalizada. Em Aseprite ou outro editor de
pixel art, revisar especialmente:

1. Reforçar grupos de pixels no tamanho real, sobretudo armas, juntas e rostos.
2. Corrigir oscilações de volume e posição de capacetes, ombreiras e caldeiras
   entre as poses; no Dummy a variação vertical do repouso é mais evidente.
3. Travar o desenho dos pés no repouso, além da base geométrica já alinhada.
4. Ajustar alternância das pernas e braços e a passagem do frame 5 ao frame 0
   da corrida. Os GIFs permitem revisar ritmo; diferença de pixels não comprova
   anatomia nem continuidade física perfeita.

As folhas seguem a orientação lateral para a direita do pedido. O jogo atual usa
char-maps quadrados rotacionados em oito direções por `enemygfx.c`; a adoção destas
folhas 32×48 exige integração de renderer/animação, teste de paleta na cena e
revisão das caixas de colisão. **O renderer e o gameplay existentes não foram
alterados, e não houve teste em ROM/emulador desta nova arte.**

## Recursos SGDK

Exemplo que corresponde a um arquivo entregue:

```text
SPRITE enemy_torreao "gfx/torreao.png" 4 6 FAST 6 NONE BALANCED FAST
```

Todas as declarações reais estão em `enemies.res`, com caminhos relativos a ele.
Os nomes de símbolos usam prefixo `enemy_` para evitar colisão com os dados do jogo.
O modelo literal solicitado no prompt, para um arquivo chamado `heroi.png`, é:

```text
SPRITE heroi "gfx/heroi.png" 4 6 FAST 6 NONE BALANCED FAST
```

`heroi.png` é apenas o nome do modelo; os arquivos efetivos são os 15 inimigos
da tabela. O ResComp descarta as duas células transparentes finais da linha 0.

## Reproduzir a exportação e a verificação

Na raiz do repositório, com Python/Pillow e Java disponíveis:

```sh
python3 game/art/darkspace-v1/export_sheets.py
python3 game/art/darkspace-v1/validate_sheets.py
```

A verificação usa `java -Djava.awt.headless=true` e o ResComp local de `SGDK/bin/`.
O pacote ZIP de entrega contém os PNGs nativos, paleta, declarações, relatório,
prévia e documentação. Os originais e scripts de reprodução permanecem nesta
pasta do projeto.
