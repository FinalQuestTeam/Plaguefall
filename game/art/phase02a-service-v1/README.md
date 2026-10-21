# Fase 2A — Rua de serviço

## Estado atual — campanha integrada

Pacote aprovado explicitamente e aplicado à fase 02A. A campanha carrega o mapa próprio, os limites, a câmera, os obstáculos e os perigos desta planta; a música existente permanece **Ladainha de Ferro**.

A validação integrada foi concluída em NTSC e PAL. A bateria dos sete mapas reuniu 42 partidas novas e 12 partidas de regressão da fase 1; os 28 ensaios de carga mantiveram 60 FPS NTSC e 50 FPS PAL. Os resultados da campanha estão em [NTSC](../phases02-06-v1/validation/ntsc/report.json) e [PAL](../phases02-06-v1/validation/pal/report.json). Os ensaios isolados abaixo são registros anteriores e não substituem esses resultados.


Cenário aprovado explicitamente e integrado à campanha. Capítulo 2, nó 2, após a igreja ser preservada no prólogo. A etapa seguinte é a fase 3, o novo abrigo.

`source/layout.png` é a fonte raster produzida pela ferramenta integrada ImageGen. `prompts.json` guarda o texto integral e as referências. `design.json` registra a composição lógica de 512×320, o piso de 480×208, os elementos narrativos, a saída e a trilha.

A câmera acompanha a inclinação de 60° dos personagens. A capela ocupa a borda superior; porta azul, telhado íntegro e nicho vazio ligam a cena à fuga anterior. O rack vazio e as jarras agrupadas contam uma retirada organizada. O portão e o pano vermelho assinalam a continuação do caminho. O centro permanece livre de objetos altos e de colisões decorativas.

Trilha ativa: **Ladainha de Ferro**, mantendo a ligação com a igreja. Objetivo existente: eliminar 12 inimigos. Entrada em (48,208); referência de saída em (464,160).

Para exportação, a fonte é normalizada uma única vez para o tamanho lógico. A montagem deve repetir módulos de piso e muros, mantendo as duas junções inferiores contínuas; os elementos da faixa superior ficam acima de y=96. Não há lama nem obstáculos sólidos no interior da área caminhável. A fonte não deve ser usada como uma textura integral sem deduplicação dos tiles. As medidas finais do atlas e a validação de orçamento ficam no relatório do exportador.

Exportação validada: **443 tiles / 14176 bytes**, 16 cores, sem substituições aproximadas. O piso seco permanece conectado e a entrada alcança a saída com ator de 16×16. A geometria foi verificada pelo exportador. Os relatórios `validation/emulator-ntsc.json` e `validation/emulator-pal.json` medem renderização, câmera, HUD e atores em uma compilação temporária isolada; os objetivos e efeitos de lama não são simulados. Na etapa desse ensaio isolado, a ROM de produção foi preservada por hash.

## Ensaio de carga isolado — histórico anterior à integração

[NTSC](validation/emulator-ntsc.json) · [PAL](validation/emulator-pal.json). Os testes reais no Genesis Plus GX mantiveram60/50 quadros por segundo nos três casos medidos por região: repouso, rolagem horizontal e rolagem vertical. A carga de movimento usa4 inimigos e6 tiros por grupo. O atlas exportado foi comparado à VRAM real; os limites da câmera foram percorridos.

Estes relatórios anteriores usaram ROMs temporárias da renderização existente, com o cenário substituído para medição. Estes ensaios não simulam os objetivos/perigos das novas fases nem representam partidas completas. Naquele ensaio, a ROM, as fontes e os recursos de produção foram preservados por hash; isso descreve a revisão isolada anterior à integração atual.
