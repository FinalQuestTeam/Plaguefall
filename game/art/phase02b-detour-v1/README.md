# Fase 2B — Desvio e igreja danificada

## Estado atual — campanha integrada

Pacote aprovado explicitamente e aplicado à fase 02B. A campanha carrega o mapa próprio, os limites, a câmera, os obstáculos e os perigos desta planta; a música existente permanece **Entardecer**.

A validação integrada foi concluída em NTSC e PAL. A bateria dos sete mapas reuniu 42 partidas novas e 12 partidas de regressão da fase 1; os 28 ensaios de carga mantiveram 60 FPS NTSC e 50 FPS PAL. Os resultados da campanha estão em [NTSC](../phases02-06-v1/validation/ntsc/report.json) e [PAL](../phases02-06-v1/validation/pal/report.json). Os ensaios isolados abaixo são registros anteriores e não substituem esses resultados.


Cenário aprovado explicitamente e integrado à campanha. Capítulo 2, nó 3, após o uso da bomba no prólogo. A etapa seguinte é a fase 3, o novo abrigo.

`source/layout.png` é a fonte raster produzida pela ferramenta integrada ImageGen. `prompts.json` guarda o texto integral e as referências. `design.json` registra a composição lógica de 512×320, o piso de 480×208, os elementos narrativos, as áreas de lama, a saída e a trilha.

A câmera conserva os 60° da fase aprovada. A fonte usa a mesma capela e o mesmo portão da rota 2A. Só um quarto do telhado cedeu: porta, sino, nicho e a maior parte da construção continuam reconhecíveis. Telhas sobre reservas e uma jarra caída contam o custo da explosão sem transformar o templo em ruína total. As duas poças periféricas e as passadas que as contornam mostram uma retirada mais difícil.

Trilha ativa: **Entardecer**, para o peso da decisão. Objetivo existente: eliminar 12 inimigos. Entrada em (48,208); referência de saída em (464,160). A lama é piso atravessável e aplica a lentidão existente ao jogador e aos inimigos; não bloqueia os tiros.

Para exportação, a fonte é normalizada uma única vez para o tamanho lógico. A montagem deve repetir piso seco e muros, manter cantos inferiores contínuos e recolocar apenas duas manchas de lama: (400,96,96,32) e (16,248,104,56). O desabamento e os objetos altos ficam acima de y=96. Não adicionar colisões de tiros às poças nem aos rastros. A fonte não deve ser usada como textura integral sem deduplicação dos tiles. As medidas finais do atlas e a validação de orçamento ficam no relatório do exportador.

Exportação validada: **603 tiles / 19296 bytes**, 16 cores, sem substituições aproximadas. O piso seco permanece conectado e a entrada alcança a saída com ator de 16×16. A geometria foi verificada pelo exportador. Os relatórios `validation/emulator-ntsc.json` e `validation/emulator-pal.json` medem renderização, câmera, HUD e atores em uma compilação temporária isolada; os objetivos e efeitos de lama não são simulados. Na etapa desse ensaio isolado, a ROM de produção foi preservada por hash.

## Ensaio de carga isolado — histórico anterior à integração

[NTSC](validation/emulator-ntsc.json) · [PAL](validation/emulator-pal.json). Os testes reais no Genesis Plus GX mantiveram60/50 quadros por segundo nos três casos medidos por região: repouso, rolagem horizontal e rolagem vertical. A carga de movimento usa4 inimigos e6 tiros por grupo. O atlas exportado foi comparado à VRAM real; os limites da câmera foram percorridos.

Estes relatórios anteriores usaram ROMs temporárias da renderização existente, com o cenário substituído para medição. Estes ensaios não simulam os objetivos/perigos das novas fases nem representam partidas completas. Naquele ensaio, a ROM, as fontes e os recursos de produção foram preservados por hash; isso descreve a revisão isolada anterior à integração atual.
