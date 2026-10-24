# Fase 3 — ensaio privado de estilo

Este pacote usa as imagens já compostas pelo gerador `build.py` do coordenador. `package_native.py` somente empacota esses arquivos; não executa nem altera o gerador, a fase ativa, o código C ou a ROM.

- Cena inteira: `complete-native.png`, 2560 × 320, **554/640 tiles**.
- Igreja destruída: `complete-damaged-native.png`, **570/640 tiles**.
- Bancos: `native/{tiles,map,palette}.bin` e `damaged-native/{tiles,map,palette}.bin`.
- Contrato de integração: `manifest.json`; fontes relativas a esta pasta e `game_path` rastreável.
- Prancha: `reviews/five-cameras-1x.png`; cada quadro tem 320 × 224 pixels, com Damião em tamanho nativo e identificação “prévia, não ROM”.
- Parecer e validações: `reviews/review.json`.

Os dois bancos conservam a mesma paleta RGB333 de 16 cores da igreja. A deduplicação usa apenas tiles exatamente iguais e inversões H/V; a remontagem foi comparada pixel a pixel. Bounds, sólidos, início, caminho, saída e metadados de câmera mantêm os valores ativos. O bridge foi validado contra esta pasta, sem ativá-la.

A cobertura dominante, a fachada curta e os materiais de 1 pixel aproximam a proposta da igreja original. A repetição regular das telhas e do reboco ainda aparece; o piso ocre mantém continuidade com o pátio, mas distingue pouco rua e terra seca. As aberturas das garagens também parecem mais limpas que a igreja. Isso autoriza comparação em ensaio privado, não aprovação visual final nem publicação. FPS, contato, movimento da câmera e paleta em execução exigem uma ROM de teste posterior.
