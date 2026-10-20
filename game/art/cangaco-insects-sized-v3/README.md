# Inimigos cangaço — tamanhos nativos e colisão

Os treze inimigos foram redesenhados com **image_gen integrado**, a partir das identidades anteriores, para as classes nativas do projeto. Rex mantém a arte 32×48 da versão 2. Os PNGs antigos não foram substituídos.

O código original usa classes 16/24/32 pixels e 48 para o chefe; não havia uma classe 36×36 nas definições consultadas. Antes desta etapa todos os novos insetos eram desenhados em 32×48, apesar dessas hitboxes diferentes.

## Arquivos por nome do projeto

| ID | Nome | Dimensão | Tiles/frame | Bytes/frame | Peças do hardware |
|---|---|---:|---:|---:|---:|
| `sq_red` | [Torreão](enemies/sq_red/sq_red.png) | 16×16 | 4 | 128 | 1 |
| `sq_yellow` | [Batedor](enemies/sq_yellow/sq_yellow.png) | 16×16 | 4 | 128 | 1 |
| `sq_purple` | [Baluarte](enemies/sq_purple/sq_purple.png) | 32×32 | 16 | 512 | 1 |
| `sq_orange` | [Aríete](enemies/sq_orange/sq_orange.png) | 16×16 | 4 | 128 | 1 |
| `tri_red` | [Fuzileiro](enemies/tri_red/tri_red.png) | 16×16 | 4 | 128 | 1 |
| `tri_yellow` | [Caçador](enemies/tri_yellow/tri_yellow.png) | 16×16 | 4 | 128 | 1 |
| `tri_purple` | [Escudeiro](enemies/tri_purple/tri_purple.png) | 16×16 | 4 | 128 | 1 |
| `tri_orange` | [Adaga](enemies/tri_orange/tri_orange.png) | 16×16 | 4 | 128 | 1 |
| `pen_red` | [Artilheiro](enemies/pen_red/pen_red.png) | 24×24 | 9 | 288 | 1 |
| `pen_yellow` | [Alcateia](enemies/pen_yellow/pen_yellow.png) | 24×24 | 9 | 288 | 1 |
| `pen_purple` | [Fortaleza](enemies/pen_purple/pen_purple.png) | 32×32 | 16 | 512 | 1 |
| `pen_orange` | [Meteoro](enemies/pen_orange/pen_orange.png) | 24×24 | 9 | 288 | 1 |
| `boss` | [Lacraia](enemies/boss/boss.png) | 48×48 | 36 | 1152 | 4 |

Cada PNG tem seis colunas (dois quadros de repouso, quatro de movimento) e oito linhas, na ordem N, NE, L, SE, S, SO, O, NO. Cinco vistas são desenhadas; as três ocidentais usam HFLIP. As folhas medem 96×128,144×192,192×256 ou 288×384, conforme a classe. A dimensão da célula e a escala são constantes dentro de cada personagem. Os arquivos `ID-4x.png` são prévias separadas por vizinho mais próximo.

Paleta PAL1 compartilhada, até 15 cores visíveis, índice 0 transparente, RGB nos níveis do Mega Drive e alfa binário. Os 30 quadros canônicos de cada inseto totalizam 390 quadros em ROM; as 624 referências visuais incluem espelhos. Não há VFLIP para simular frente/costas. O chefe é dividido em 32×32,32×16,16×32 e16×16; o HFLIP também reposiciona as colunas de 32 e 16 pixels.

## Correção de alinhamento e hitbox

As caixas de movimento/contato de `EnemyDef.size` foram preservadas. A arte agora tem o mesmo tamanho da caixa; corpo, tiros dos dois lados e arcos usam a projeção comum `VIDEO_PROJECT_Y(y)=y−16`. Assim um tiro desenhado sobre a área do inseto também cruza a sua AABB lógica. A saída da arma deixou de aplicar a regra antiga de espelhamento vertical do mech: Rex usa apenas HFLIP, com N/S próprios.

É uma colisão AABB, não uma máscara de pixels: a margem transparente da célula também pertence ao retângulo. Os escudos dos blindados continuam consumindo tiros sem perder HP por regra do jogo.

- [1380 casos no código real de tiros/dano](validation/combat.json), incluindo 15 tipos (os 13 novos e os 2 alvos legados), 8 direções, bordas, erros, tiros com velocidade máxima, escudo, gelo, fogo e morte.
- [600 casos na ROM executada](validation/emulator-combat.json), verificando HP, consumo do tiro, status e 120 checagens dos retângulos efetivos do SAT. Os alvos são imobilizados na RAM volátil para tornar a amostra controlada.
- [Validação nativa e de renderização](validation/report.json): 128 quadros aleatórios, 600 de estresse, 1024 de mudanças de tipos/alocação, falha de DMA e HFLIP sem transferência adicional.

## Memória e desempenho

| Medida | Antes desta etapa | Atual |
|---|---:|---:|
| Animação dos inimigos |299520 B|118080 B|
| Pool de inimigos em VRAM |12 KiB|10 KiB|
| ROM alinhada |640 KiB|512 KiB|
| RAM estática |6008 B|6165 B|
| Heap livre observado |47490 B|47332 B|

A animação dos inimigos usa **60,6% menos ROM**. O pool está limitado a 320 tiles, alocados em blocos de 4; desalocações, reutilização e eventuais expulsões invalidam a imagem antes do reaproveitamento. Gráficos com DMA já agendado no quadro ficam protegidos. Isso reduz VRAM e transferências dos inimigos comuns, com um pequeno aumento de RAM para a administração do cache.

Por transferência: 128/288/512 bytes para os comuns e 1152 para o chefe. Até quatro atualizações de inimigos e uma de Rex são permitidas por quadro; o pior caso teórico é 5376 bytes, com reserva de banda/fila para SAT/HUD. Sob excesso de demanda pode haver adiamento/expulsão; não há garantia de manter 16 chefes em cache ao mesmo tempo. As situações normais com quinze comuns e um único chefe cabem no pool.

O HUD da arena TESTE passou a reescrever textos inalterados a 10 Hz, atualizando atributos imediatamente quando mudam. Isso também foi verificado por diferença dos pixels reais do vídeo.

No cenário controlado com lógica ativa, oito Batedores mantêm 60 FPS; quinze ficaram em 31,75 FPS. Quinze ainda não atingem 60 FPS. Os números anteriores de ROM/SAT não demonstravam desempenho de CPU; os [resultados por etapa e método](validation/performance/README.md) mantêm essas verificações separadas.

[Auditoria completa de ROM/RAM/VRAM](validation/memory.json) · [Build e hashes dos recursos](validation/worktree-build.json) · [Captura da ROM com as classes em escala](validation/emulator/all-enemies-direction-2.png).

## Origem e reprodução

As fontes novas do **image_gen integrado** estão em `originals/`; os [prompts por ID e registro das fontes](prompts/sources.json) estão em `prompts/`. Foi solicitada composição específica para cada resolução, com formas simplificadas, câmera elevada a 60° e tecnologia improvisada sobre insetos orgânicos. A ferramenta gerou fontes ampliadas; o exportador isola poses, registra o apoio, converte por vizinho mais próximo para a resolução final e indexa a paleta. Não desenha membros ou inventa poses por código. Os sprites finais e seus limites são verificados; um ângulo 3D exato não é mensurável a partir de uma imagem 2D estilizada.

A primeira fonte do chefe repetia a orientação de S nas vistas N/NE; essas vistas foram redesenhadas. As três vistas diagonais/lateral da fonte de Fortaleza estavam voltadas para oeste e são normalizadas com HFLIP, registrado em `validation/export.json`. Meteoro veio com uma pose adicional; são usadas as primeiras seis poses de cada linha.

```sh
/opt/homebrew/bin/python3 game/tools/pack_actor_animation.py
/opt/homebrew/bin/python3 game/art/cangaco-insects-sized-v3/validate_sprites.py
make -C game clean
make -C game -j4
```

Para conferir recursos e cabeçalho sem escrever, usar `pack_actor_animation.py --check`. O empacotador lê a seleção de animações e a versão ativa em `game/res/actor_animation.json`, mantém Rex com os mesmos quadros e gera os binários do SGDK em `game/res/insects/`. O exportador direto também aceita `--check`.

Os testes de emulador usam o Genesis Plus GX libretro Intel já instalado via Rosetta. Relatórios e capturas descrevem emulação controlada; não são testes em console físico nem garantem todos os ataques e sobreposições possíveis. A projeção do cenário permanece a anterior; esta etapa trata da arte e colisão dos personagens/projéteis.

ROM: `game/out/rom.bin`. SHA-256: `b3281bf4fa08aa695882547305607524e148a9988b5c4c224bebc7a69014d241`.
