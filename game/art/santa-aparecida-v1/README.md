# Nossa Senhora Aparecida — objetivo PROTEGER

Substitui a antena, usando o mesmo NPC estático existente. Tamanho24×24, apoio e posição no retângulo original; HP, perseguição dos inimigos, dano12 por contato, invulnerabilidade5s, recuo/onda de choque, piscar e condição de falha são preservados. Não foi criado um segundo aliado.

## Arte e câmera

[PNG nativo indexado](santa-aparecida.png), [prévia10× por vizinho mais próximo](santa-aparecida-10x.png), [paleta compartilhada](paleta.json). Nossa Senhora Aparecida com manto azul, coroa dourada e pedestal compacto de metal reaproveitado. A primeira fonte ficou frontal demais e foi corrigida com vista de cima da coroa, ombros e parte traseira da base. A meta visual é60° acima do chão; não há medição exata de câmera3D em um raster estilizado.

Gerado com **image_gen integrado**; fonte ampliada em `originals/santa-aparecida.png`. O exportador recorta a área opaca, registra por vizinho mais próximo em24×24 e indexa na PAL1 já existente. Portanto, a ferramenta não forneceu diretamente um PNG nativo indexado: esses ajustes técnicos foram feitos e conferidos pelo exportador. O código não inventa poses ou desenha a figura.

Prompts finais: [pedido inicial](prompt-v1.txt), [correção da câmera](prompt-camera-correction.txt). A segunda imagem é a fonte escolhida.

## Integração e orçamento

- Corpo:9 tiles288 bytes no mesmo endereço72; uma peça de hardware24×24.
- HUD:1 tile32 bytes, endereço81, derivado da mesma arte.
- Brilho da coroa:1 tile32 bytes, endereço82, nos mesmos x+8/y da antiga luz; alterna nos mesmos30/60 quadros.
- Total11 tiles352 bytes; **variação de VRAM0 bytes**, paletas adicionais0, RAM permanente adicional0. `NUM_TILES` permanece83.
- `saint_data.h` é gerado e copiado para o buffer de tiles já existente no boot; não precisa de recurso SPRITE nem cache/DMA de animação próprio.

## Verificações

[Validação técnica](validation.json):24×24, uma pose,11 cores visíveis na PAL1 de até15, índice0 transparente, alfa binário, borda transparente, mesmos índices e empacotamento em ordem de coluna. O ícone e o brilho também são PNGs indexados8×8.

[Teste da ROM](emulator.json): entrada no estágio6 pelas portas normais,70 verificações do retângulo SAT24×24, ambas as fases do brilho, HP60→48 após contato, segundo contato sem dano durante invulnerabilidade e dano novamente após o período. [Captura real](emulator-screens/santa-proteger.png). A figura é estática; não tem ciclo de movimento ou oito orientações, assim como a antena substituída.

```sh
/opt/homebrew/bin/python3 game/art/santa-aparecida-v1/export_sprite.py
/opt/homebrew/bin/python3 game/art/santa-aparecida-v1/export_sprite.py --check
arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-iso60-v2/tests/smoke_emulator.py --saint --output game/art/santa-aparecida-v1/emulator.json
```

A parceira feminina está [somente em concept](../concepts/parceira/README.md), e sua conversão depende da aprovação do usuário.
