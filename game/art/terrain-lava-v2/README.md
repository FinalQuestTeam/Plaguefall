# Lava — terreno ampliado, revisão2

Material compartilhado pelas fases3,6A e6B para campos de lava que ocupam espaço relevante da arena.

[source/liquid.png](source/liquid.png) é a textura opaca de líquido gerada com **image_gen.imagegen integrado**. O [prompt completo e proveniência](prompts.json) pedem um material repetível, vista ortográfica, veios laranja/amarelo e fissuras finas. Cada exportação reduz a fonte uma única vez a64×64 e aplica a paleta da fase. As bordas/crusta vêm da fonte aprovada da6A e são copiadas/espelhadas sem escala.

A lista de módulos em design.json de cada fase declara as duas caixas quentes, o miolo repetível e as oito peças de contorno. O desenho preenche as mesmas caixas usadas pelo teste com LAVA_update. Não há ampliação grosseira de pixels.

A revisão foi feita nos pacotes de arte e em ROMs temporárias de teste. Estes cenários ainda aguardam aprovação para integração à campanha principal.
