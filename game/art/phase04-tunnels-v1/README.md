# Fase 04 — Túneis de manutenção

## Estado atual — campanha integrada

Pacote aprovado explicitamente e aplicado à fase 04. A campanha carrega o mapa próprio, os limites, a câmera, os obstáculos e os perigos desta planta; a música existente permanece **Breu**.

A validação integrada foi concluída em NTSC e PAL. A bateria dos sete mapas reuniu 42 partidas novas e 12 partidas de regressão da fase 1; os 28 ensaios de carga mantiveram 60 FPS NTSC e 50 FPS PAL. Os resultados da campanha estão em [NTSC](../phases02-06-v1/validation/ntsc/report.json) e [PAL](../phases02-06-v1/validation/pal/report.json). Os ensaios isolados abaixo são registros anteriores e não substituem esses resultados.


Damião avança pelos túneis de manutenção para abrir o caminho dos refugiados. Escotilhas abertas e marcas de ferramentas revelam os últimos reparos feitos antes do abandono.

Mapa integrado: 512 × 288 pixels, câmera ortográfica a 60° acima do chão. Área de circulação: [16, 80, 480, 192]; início [48, 176]; saída [464, 176]. Os elementos grandes ficam fora da área de combate. As zonas de risco são pequenas e periféricas, com passagem seca conectada.

Objetivo existente preservado: eliminar 16 inimigos. Música existente: **Breu**.

`source/layout.png` é o mapa raster de produção gerado com a ferramenta integrada ImageGen, orientado pelo pátio aprovado, pelo herói e pelo conceptart da fase. `prompts.json` registra prompt, referências e origem. `design.json` contém os parâmetros para exportação. Este pacote foi aprovado e seu mapa próprio está integrado ao jogo.

A montagem usa recortes sem escala: um módulo de chão 16 × 16 repetível, trechos de parede e tubulação, marcos narrativos únicos e cantos completos 16 × 32 por último. A lista `modules` registra cada recorte e destino em coordenadas nativas alinhadas a 8 pixels.

Exportação revisada: **537 tiles exatos de 8 × 8**, 17,184 bytes de padrões, 16 cores específicas da fase, sem substituição aproximada de tiles. O mapa, atlas e hardware estão em `map-native.png`, `tileset.png`, `modules.png`, `stage.tmx` e `hardware/`. A verificação geométrica encontrou 1281 posições secas conectadas para um personagem 16 × 16, incluindo início e saída (94.93% de área seca). O custo de renderização, câmera, HUD e atores foi medido em uma revisão isolada NTSC/PAL; a fase completa agora usa este cenário na campanha.

A paleta preserva azul da manutenção, cinzas de concreto e ferrugem; no abrigo, tecido e luz tornam o salão mais quente. Os túneis usam concreto mais frio e iluminação pontual. As caixas de narrativa em `story_elements` foram alinhadas aos recortes finais.

## Ensaio de carga isolado — histórico anterior à integração

[NTSC](validation/emulator-ntsc.json) · [PAL](validation/emulator-pal.json). Os testes reais no Genesis Plus GX mantiveram60/50 quadros por segundo nos três casos medidos por região: repouso, rolagem horizontal e rolagem vertical. A carga de movimento usa4 inimigos e6 tiros por grupo. O atlas exportado foi comparado à VRAM real; os limites da câmera foram percorridos.

Estes relatórios anteriores usaram ROMs temporárias da renderização existente, com o cenário substituído para medição. Estes ensaios não simulam os objetivos/perigos das novas fases nem representam partidas completas. Naquele ensaio, a ROM, as fontes e os recursos de produção foram preservados por hash; isso descreve a revisão isolada anterior à integração atual.
