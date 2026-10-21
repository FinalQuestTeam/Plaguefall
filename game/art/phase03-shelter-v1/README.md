# Fase 03 — Abrigo de manutenção

## Estado atual — campanha integrada

Pacote aprovado explicitamente e aplicado à fase 03. A campanha carrega o mapa próprio, os limites, a câmera, os obstáculos e os perigos desta planta; a música existente permanece **Entardecer**.

A validação integrada foi concluída em NTSC e PAL. A bateria dos sete mapas reuniu 42 partidas novas e 12 partidas de regressão da fase 1; os 28 ensaios de carga mantiveram 60 FPS NTSC e 50 FPS PAL. Os resultados da campanha estão em [NTSC](../phases02-06-v1/validation/ntsc/report.json) e [PAL](../phases02-06-v1/validation/pal/report.json). Os ensaios isolados abaixo são registros anteriores e não substituem esses resultados.


O padre pede que Damião proteja o novo abrigo enquanto os refugiados decidem uma rota segura. Redes e cobertores ocupam uma antiga oficina; a vida civil resiste entre tubulações avariadas.

Mapa integrado: 384 × 384 pixels, câmera ortográfica a 60° acima do chão. Área de circulação: [16, 96, 352, 272]; início [64, 256]; saída [336, 144]. Os elementos grandes ficam fora da área de combate. Os campos de lava ocupam33,02% da área navegável, em cantos opostos, com passagem seca conectada.

Objetivo existente preservado: eliminar 14 inimigos. Música existente: **Entardecer**.

`source/layout.png` é o mapa raster de produção gerado com a ferramenta integrada ImageGen, orientado pelo pátio aprovado, pelo herói e pelo conceptart da fase. `prompts.json` registra prompt, referências e origem. `design.json` contém os parâmetros para exportação. Este pacote foi aprovado e seu mapa próprio está integrado ao jogo.

A montagem usa recortes sem escala: um módulo de chão 32 × 32 repetível, trechos de parede e tubulação, marcos narrativos únicos e cantos completos 16 × 32 por último. A lista `modules` registra cada recorte e destino em coordenadas nativas alinhadas a 8 pixels.

Exportação revisada: **538 tiles exatos de 8 × 8**, 17,216 bytes de padrões, 16 cores específicas da fase, sem substituição aproximada de tiles. O mapa, atlas e hardware estão em `map-native.png`, `tileset.png`, `modules.png`, `stage.tmx` e `hardware/`. A verificação geométrica encontrou 925 posições secas conectadas para um personagem 16 × 16, incluindo início e saída (66.98% de área seca). O custo de renderização, câmera, HUD e atores foi medido em uma revisão isolada NTSC/PAL; a fase completa agora usa este cenário na campanha.

A paleta preserva azul da manutenção, cinzas de concreto e ferrugem; no abrigo, tecido e luz tornam o salão mais quente. Os túneis usam concreto mais frio e iluminação pontual. As caixas de narrativa em `story_elements` foram alinhadas aos recortes finais.

Na campanha integrada, a lava conserva as caixas de dano da planta e recebe brilho lento por variações dos próprios tiles. As transferências são parceladas; a paleta compartilhada do cenário não é animada, evitando fazer o chão, os muros, os personagens ou o HUD piscarem junto.

## Ensaio de carga isolado — histórico anterior à integração

[NTSC](validation/emulator-ntsc.json) · [PAL](validation/emulator-pal.json). Os testes reais no Genesis Plus GX mantiveram60/50 quadros por segundo nos três casos medidos por região: repouso, rolagem horizontal e rolagem vertical. A carga de movimento usa4 inimigos e6 tiros por grupo. O atlas exportado foi comparado à VRAM real; os limites da câmera foram percorridos.

Estes relatórios anteriores usaram ROMs temporárias da renderização existente, com o cenário substituído para medição. Nesta revisão, os ensaios habilitam a lógica original de dano de lava e verificam a travessia seca. Os novos objetivos de campanha não são simulados, e os ensaios não representam partidas completas. Naquele ensaio, a ROM, as fontes e os recursos de produção foram preservados por hash; isso descreve a revisão isolada anterior à integração atual.

## Lava ampliada — revisão2

A lava passou de1.40% para **33.02% do piso navegável**. A arte é montada com bordas e miolo separados em escala nativa; as caixas de dano têm exatamente a área desenhada. Há duas zonas em cantos opostos, que reduzem o espaço para recuar durante o combate. O miolo usa [textura nova](../terrain-lava-v2/README.md), gerada com ImageGen integrado.

As passagens entre os campos têm48 pixels no eixo horizontal e64 no vertical. A base física do jogador é16×16; a referência visual é32×48. O caminho seco da entrada à saída continua conectado, com925 posições válidas. A galeria mostra o personagem nesse tamanho.

[Antes](validation/before-lava-v2.png) · [Mapa revisado](map-native.png). Os relatórios PAL/NTSC foram refeitos: usam LAVA_update original, comprovam dano ao pisar no campo, fim do dano ao sair e uma travessia seca apenas pelo joypad. Naquela etapa de revisão isolada, a integração da campanha ainda não havia sido autorizada.
