# Fase 06A — Resgate confirmado

## Estado atual — campanha integrada

Pacote aprovado explicitamente e aplicado à fase 06A. A campanha carrega o mapa próprio, os limites, a câmera, os obstáculos e os perigos desta planta; a música existente permanece **Entardecer**.

A validação integrada foi concluída em NTSC e PAL. A bateria dos sete mapas reuniu 42 partidas novas e 12 partidas de regressão da fase 1; os 28 ensaios de carga mantiveram 60 FPS NTSC e 50 FPS PAL. Os resultados da campanha estão em [NTSC](../phases02-06-v1/validation/ntsc/report.json) e [PAL](../phases02-06-v1/validation/pal/report.json). Os ensaios isolados abaixo são registros anteriores e não substituem esses resultados.


Cenário aprovado explicitamente e integrado à campanha. Fonte de produção criada com a ferramenta nativa image_gen; prompt completo e referências em [prompts.json](prompts.json). Seus mapas, tiles e paleta alimentam os recursos ativos desta fase.

## Planta

Arena retangular de 512×320 pixels, câmera ortográfica a 60° acima do chão e norte para cima. Área navegável: x16–495, y96–303. Faixa de arquitetura no topo com 96 pixels; centro aberto para combate, muros laterais e inferior de 16 pixels com cantos contínuos. O início é [48,208] e a referência de saída [464,176]. A passagem segue para o capítulo 7 após 20 abates, mantendo a condição existente.

Dois campos extensos de lava nos cantos: [16,96,184,96] e [296,208,200,96]. O centro continua seco e amplo. A montagem de tiles deve mover os módulos térmicos da fonte para essas caixas; não considerar a fonte inteira uma colisão. Nenhum obstáculo sólido adicional foi proposto.

## História pelo ambiente

O sinalizador foi protegido e os refugiados embarcaram com vida. Damião e Dinorah ficam para investigar os ninhos próximos à base de lançamento.

- **Rampa de embarque vazia:** A retirada terminou: a rampa recolhe sem passageiros deixados para trás.
- **Sinal azul confirmado:** O dispositivo da santa conseguiu estabelecer o contato de resgate.
- **Marcas ordenadas de embarque:** Pegadas e trilhas de rodas ligam a comunidade ao embarque bem-sucedido.
- **Suprimentos e área desocupada:** O que ficou são equipamentos do posto, sem sugerir vítimas ou abandono de pessoas.

A música existente é **Entardecer**. A melancolia da despedida acompanha o alívio, antes da investigação da base.

## Arquivos e montagem

- [source/layout.png](source/layout.png): raster de produção em alta resolução, 1586×992; composição para mundo de 512×320.
- [design.json](design.json): planta, áreas de dano, narrativa e coordenadas para montagem.
- [prompts.json](prompts.json): prompt integral, ferramenta e origem das referências.

As caixas de story_elements e source_regions usam coordenadas do mundo normalizado a 512×320, alinhadas à grade de 8 pixels. A fonte contém detalhes de superfície que não implicam colisão. O exportador compartilhado deve repetir módulos calmos de chão e muros, preservando os marcos narrativos. Os limites finais, contagem de tiles e imagem nativa são definidos pelo exportador; a validação dos objetivos, perigos e partidas da integração foi concluída nos relatórios compartilhados NTSC/PAL. A carga gráfica já foi medida em uma compilação isolada.


## Exportação para revisão

- [Mapa nativo](map-native.png): 512×320, paleta de 16 cores do Mega Drive.
- [Atlas](tileset.png) e [módulos de construção](modules.png).
- [Mapa editável no Tiled](stage.tmx), [catálogo de módulos](modules.json) e [relatório](export.json).
- `hardware/tiles.bin`: 508 tiles exatos de 8×8, 16256 bytes. Limite: 640 tiles.
- Mapa compacto: 5120 bytes; mapa acolchoado para janela VDP: 6144 bytes.

O teste geométrico encontra 899 posições secas conectadas para um personagem de 16×16 pixels, incluindo uma rota entre entrada e saída. A área seca ocupa 63,08% do piso navegável. Os muros inferiores terminam em módulos de canto completos, aplicados por último.

A exportação conserva a resolução nativa após uma única redução da fonte, sem redimensionar módulos nem substituir tiles por aproximações. O teste `--check` confirmou reconstrução e binários determinísticos. A renderização, câmera, HUD e atores passaram no benchmark isolado em NTSC e PAL. A campanha agora usa o mapa próprio desta fase; os ensaios integrados finais foram concluídos em NTSC/PAL.

Na campanha integrada, a lava conserva as caixas de dano da planta e recebe brilho lento por variações dos próprios tiles. As transferências são parceladas; a paleta compartilhada do cenário não é animada, evitando fazer o chão, os muros, os personagens ou o HUD piscarem junto.

## Ensaio de carga isolado — histórico anterior à integração

[NTSC](validation/emulator-ntsc.json) · [PAL](validation/emulator-pal.json). Os testes reais no Genesis Plus GX mantiveram60/50 quadros por segundo nos três casos medidos por região: repouso, rolagem horizontal e rolagem vertical. A carga de movimento usa4 inimigos e6 tiros por grupo. O atlas exportado foi comparado à VRAM real; os limites da câmera foram percorridos.

Estes relatórios anteriores usaram ROMs temporárias da renderização existente, com o cenário substituído para medição. Nesta revisão, os ensaios habilitam a lógica original de dano de lava e verificam a travessia seca. Os novos objetivos de campanha não são simulados, e os ensaios não representam partidas completas. Naquele ensaio, a ROM, as fontes e os recursos de produção foram preservados por hash; isso descreve a revisão isolada anterior à integração atual.

## Lava ampliada — revisão2

A lava passou de12.69% para **36.92% do piso navegável**. A arte é montada com bordas e miolo separados em escala nativa; as caixas de dano têm exatamente a área desenhada. Há duas zonas em cantos opostos, que reduzem o espaço para recuar durante o combate. O miolo usa [textura nova](../terrain-lava-v2/README.md), gerada com ImageGen integrado.

As passagens entre os campos têm96 pixels no eixo horizontal e16 no vertical. A base física do jogador é16×16; a referência visual é32×48. O caminho seco da entrada à saída continua conectado, com899 posições válidas. A galeria mostra o personagem nesse tamanho.

[Antes](validation/before-lava-v2.png) · [Mapa revisado](map-native.png). Os relatórios PAL/NTSC foram refeitos: usam LAVA_update original, comprovam dano ao pisar no campo, fim do dano ao sair e uma travessia seca apenas pelo joypad. Naquela etapa de revisão isolada, a integração da campanha ainda não havia sido autorizada.
