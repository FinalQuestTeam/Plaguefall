# Inventário de sprites — direção cangaço cyberpunk

Organizado pelos identificadores usados no código. A parceira ainda depende de aprovação do concept.

## Arte atual da partida

| ID / recurso | Nome | Célula | Estado |
|---|---|---|---|
| `heroi` | Rex | 32×48 | Integrado, oito direções, 2 repouso + 4 movimento |
| `sq_red`, `sq_yellow`, `sq_orange` | Torreão, Batedor, Aríete | 16×16 | Integrados |
| `sq_purple` | Baluarte | 32×32 | Integrado |
| `tri_red`, `tri_yellow`, `tri_purple`, `tri_orange` | Fuzileiro, Caçador, Escudeiro, Adaga | 16×16 | Integrados |
| `pen_red`, `pen_yellow`, `pen_orange` | Artilheiro, Alcateia, Meteoro | 24×24 | Integrados |
| `pen_purple` | Fortaleza | 32×32 | Integrado |
| `boss` | Lacraia (escorpião) | 48×48 | Integrado |
| `TILE_SAINT` / `NPC` | Nossa Senhora Aparecida | 24×24 | Substitui a antena no objetivo PROTEGER; estática |

Os 13 inimigos também têm oito direções, 2 quadros de repouso e 4 de movimento. As cinco vistas canônicas usam HFLIP para as três direções ocidentais.

## Ainda faltam personagens / objetos centrais

| ID / recurso | Nome | Tamanho atual | Pendência |
|---|---|---|---|
| futura parceira (ainda sem ID de runtime) | Parceira feminina | Não definido | [Concept v1](concepts/parceira/README.md) aguardando aprovação; criar sprite e definir comportamento depois |
| `ENEMY_DUMMY` / `dummy` | Boneco de treino | 24×24 | Char-map antigo `INS_BEETLE24` |
| `ENEMY_TARGET` / `target` | Alvo | 24×24 | Mesmo char-map antigo do dummy |

**Atenção ao papel da antena:** existe somente um NPC de proteção no código. Ele era desenhado como antena e agora como santa. Não existe outro parceiro móvel ou feminino para apenas trocar a textura. A santa preserva posição, tamanho, HP, dano por contato, invulnerabilidade, piscar, onda de choque e condição de vitória/derrota.

## Arte auxiliar que ainda usa o visual anterior

- Itens `ITEM_HEART`, `ITEM_BOMB`, `ITEM_SHOTS`, `ITEM_SPEED`, `ITEM_SHIELD`, `ITEM_CHAIN`, `ITEM_ICE`, `ITEM_FIRE`: oito sprites 16×16 de char-maps em `sprites/items_data.h`.
- Projéteis `TILE_PSHOT`, `TILE_ESHOT`: 8×8; nó do raio `TILE_SPARK`: 8×8; sombra `TILE_SHADOW`: 16×16; sangue `TILE_BLOOD`: tile 8×8 espelhado em 16×16; overlays de gelo/fogo `TILE_STATUS`: bloco de até 32×32.
- Galeria antiga `CHARS_COUNT=9`: AZUL PEQ, AZUL MED, AZUL ELITE, VERM PEQ, VERM MED, VERM ELITE, VERDE PEQ, VERDE MED, VERDE ELITE; mechs de 32×32, mantidos só como acervo da galeria. Rex é o personagem da partida.
- Retratos de história `PORTRAIT_ART`: REX, COMANDO, LACRAIA, três imagens 48×48. Ainda não correspondem aos novos concepts. Não há retrato da parceira implementado.
- Ícones de HUD/inventário são tiles 8×8; o indicador da antiga antena é substituído pelo da santa nesta etapa. Demais ícones mantêm a arte antiga.

Piso, parede, lava, lama, portas, título e logo também mantêm a apresentação anterior, mas são tiles de cenário/interface, não personagens faltantes.

## Fontes principais

- [Inimigos atuais por nome e resolução](cangaco-insects-sized-v3/README.md)
- [Rex](cangaco-protagonista-iso60-v2/README.md)
- [Santa](santa-aparecida-v1/README.md)
- [Parceira — somente concept](concepts/parceira/README.md)
