# Favela e sala do sindicato: imagem completa primeiro

Fontes completas, geradas com ImageGen antes de qualquer recorte:

- `source/07-08-favela.png`: casas, telhados, fios, escadarias, duas barricadas e pátio contínuo.
- `source/13-union.png`: janelas para o estaleiro, bandeira sindical, armários, guichê protegido e três bancos.

A conversão mantém uma grade lógica de 2×pixels. A paleta global de 16 cores reais do Mega Drive é aplicada a toda a fonte antes de recortar fachadas completas, baias, escadarias e pavimentação. A composição usa esses módulos inteiros. A deduplicação posterior só aceita pixels idênticos, incluindo espelhamentos H/V; não existe substituição por tiles aproximados. A reconstrução é comparada pixel a pixel com a composição anterior ao corte.

A favela usa 497 tiles: somando 76 da carga ou 96 dos transmissores, cabe em 640. As duas versões do sindicato compartilham 568 tiles. Dinorah viva aparece dentro do guichê protegido; na versão de sua morte há o memorial no mesmo espaço. A geometria do combate permanece idêntica.

Os limites excluem as casas e paredes da circulação. Há colisão nas duas barricadas da favela e nos três bancos da sala. Todas as cinco frentes de carga, seus pontos de coleta, o depósito e os três transmissores passam na busca de circulação com pés16×16.

A lógica da missão usa as posições atualizadas de `geometry.json`. O harness de emulador inicia cada cenário a partir da preparação da campanha sem deixar buffers temporários do mapa, impede escritas de RAM durante testes de controle e compara bytes reais de VRAM e atributos H/V das cenas. Resultados antigos não validam estes novos mapas; o build conjunto deve ser testado novamente.

Reprodução: `python3 game/tools/build_campaign_resistance.py` (Pillow). Fontes originais intactas; dados nativos e prévias estão em `native/` e `previews/`.
