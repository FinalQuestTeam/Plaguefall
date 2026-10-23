# Travessia com áreas maiores de lama

A fase 4 tem quinze retângulos conectados em poças, cobrindo 97.664 pixels,
ou 25,23% da área caminhável. Três passagens de lama ocupam toda a altura
caminhável, de y80 a y271: x448–511, x960–1039 e x1536–1623. Suas larguras
são 64, 80 e 88 pixels; o jogador precisa atravessá-las para alcançar a saída.

A lama usa os módulos de terreno existentes, a mesma paleta e a lentidão
progressiva atual. Não é uma parede sólida e não causa dano. As margens das
poças se conectam a bancos laterais; os buracos e o trajeto físico continuam
iguais. O início e a área de chegada permanecem em piso seco.

[Mapa completo de 2048×288](mapa-04.png) · [Dados atuais](../routes-2048-v2/export.json).

O gerador `tools/build_route_stages.py` mantém as quinze áreas no mundo
completo de 2048 pixels. A definição da fase deriva a quantidade de áreas do
array gerado, evitando ignorar as últimas poças por uma contagem fixa antiga.
O atlas de cenário permanece em 603 de 640 tiles; a ampliação usa o plano
modular de lama já existente, sem adicionar sprites ou paletas.

As salas de teste que reutilizam a fase 4 também recebem a nova distribuição.

[Lama no emulador](lama-no-emulador.png) · [Validação](validation.json) ·
[NTSC](validation/ntsc.json) · [PAL](validation/pal.json).
Os 28 checks passaram em cada região, incluindo lentidão no topo, meio e base
das três passagens, progressão até o teto existente de 85%, velocidade menor
enquanto se anda na lama, recuperação imediata no piso seco, ausência de dano
e conclusão da travessia somente pelo controle. A escolta, a pausa, os buracos
e os resultados também passaram pela regressão.
