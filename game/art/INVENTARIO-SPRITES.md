# Inventário de sprites — direção cangaço cyberpunk

Organizado pelos identificadores usados no código. Damião e os insetos atuais estão na partida; Dinorah participa da galeria e dos diálogos. Os recursos substituídos foram retirados do runtime.

## Arte atual da partida

| ID / recurso | Nome | Célula | Estado |
|---|---|---|---|
| `heroi` | Damião | 32×48 | Integrado, oito direções, 2 repouso + 4 movimento |
| `sq_red`, `sq_yellow`, `sq_orange` | Torreão, Batedor, Aríete | 16×16 | Integrados |
| `sq_purple` | Baluarte | 32×32 | Integrado |
| `tri_red`, `tri_yellow`, `tri_purple`, `tri_orange` | Fuzileiro, Caçador, Escudeiro, Adaga | 16×16 | Integrados |
| `pen_red`, `pen_yellow`, `pen_orange` | Artilheiro, Alcateia, Meteoro | 24×24 | Integrados |
| `pen_purple` | Fortaleza | 32×32 | Integrado |
| `boss` | Escorpião (escorpião) | 48×48 | Integrado |
| `TILE_SAINT` / `NPC` | Nossa Senhora Aparecida | 24×24 | Substitui a antena no objetivo PROTEGER; estática |

Os 13 inimigos também têm oito direções, 2 quadros de repouso e 4 de movimento. As cinco vistas canônicas usam HFLIP para as três direções ocidentais.

## Pendências de integração e de arte

| ID / recurso | Nome | Tamanho atual | Pendência |
|---|---|---|---|
| `parceira` (asset; ainda sem ator de runtime) | Dinorah |32×48 | [Sprites criados](cangaco-parceira-iso60-v1/README.md), oito direções,2/4 quadros como Damião; integrada à galeria ASSETS, ator na arena pendente |
| `ENEMY_DUMMY` / `dummy` | Boneco de treino | 24×24 | Mapa24×24 em `training_target_data.h`, ainda usado no sandbox |
| `ENEMY_TARGET` / `target` | Alvo | 24×24 | Mesmo char-map antigo do dummy |

**Atenção ao papel da antena:** existe somente um NPC de proteção no código. Ele era desenhado como antena e agora como santa. Não existe outro parceiro móvel ou feminino para apenas trocar a textura. A santa preserva posição, tamanho, HP, dano por contato, invulnerabilidade, piscar, onda de choque e condição de vitória/derrota.

## Arte auxiliar que ainda usa o visual anterior

- Itens `ITEM_HEART`, `ITEM_BOMB`, `ITEM_SHOTS`, `ITEM_SPEED`, `ITEM_SHIELD`, `ITEM_CHAIN`, `ITEM_ICE`, `ITEM_FIRE`: oito sprites 16×16 de char-maps em `sprites/items_data.h`.
- Projéteis `TILE_PSHOT`, `TILE_ESHOT`: 8×8; nó do raio `TILE_SPARK`: 8×8; sombra `TILE_SHADOW`: 16×16; sangue `TILE_BLOOD`: tile 8×8 espelhado em 16×16; overlays de gelo/fogo `TILE_STATUS`: bloco de até 32×32.
- [Galeria ASSETS](gallery-v1/README.md): somente DAMIAO e DINORAH, com células32×48, oito direções e dois quadros de repouso. O código e os nove mechs antigos foram removidos do runtime; os estudos históricos permanecem no acervo de arte. Damião é o personagem da partida.
- Retratos de história `PORTRAIT_ART`: DAMIAO, COMANDO, ESCORPIAO e DINORAH, quatro imagens 48×48. [Damião, Comando (padre) e Dinorah já seguem os concepts](dialogue-portraits-v1/README.md), com paletas próprias e transparência; Dinorah participa por rádio antes da fase 7. O retrato do Escorpião continua ativo nas cenas finais.
- Ícones de HUD/inventário são tiles 8×8; o indicador da antiga antena é substituído pelo da santa nesta etapa. Demais ícones mantêm a arte antiga.

Piso, parede, lava, lama, portas, título e logo também mantêm a apresentação anterior, mas são tiles de cenário/interface, não personagens faltantes.

## Fontes principais

- [Inimigos atuais por nome e resolução](cangaco-insects-sized-v3/README.md)
- [Damião](cangaco-protagonista-iso60-v2/README.md)
- [Santa](santa-aparecida-v1/README.md)
- [Dinorah — sprites prontos para integração](cangaco-parceira-iso60-v1/README.md)

## Limpeza do runtime

Removidos o gerador dos nove mechs, as demais matrizes antigas de insetos, os seis ícones substituídos, a trilha XGM sem uso e referências de imagem antigas sem consumidores. O dummy/alvo do sandbox conserva seu único mapa24×24. Fonte, paletas e brilho idênticos compartilham recursos na ROM. Os pisos das fases7–16 continuam ativos. [Registro da limpeza](runtime-cleanup-v1/README.md).
