# Fase 15 — antena e estaleiro modular

[Revisão visual](review.html) · [Cenário completo](normal-complete.png) · [Ignição](fire-complete.png) · [Geometria e memória](manifest.json) · [Validação e ROM](delivery.json).

A sala compartilha os módulos aprovados da 14: mundo 512×576, piso de placas de ferro com quatro rebites, limites repetíveis, cinco estações de energia de 48×48, bateria e conexões. Os cinco geradores já entram ligados; o objetivo continua sendo proteger o rádio por 120 segundos.

A antena grande foi substituída pelo [núcleo compacto aprovado](../phase15-radio-core-proposal-v1/radio-core-native-48x64.png), criado com ImageGen integrado: aço azul/cinza, prata, dourado e visor de rádio. [Prompt exato](../phase15-radio-core-proposal-v1/prompt.txt) e [prop integrado 48×64](objects/radio-antenna.png). O rádio inteiro usa uma sobreposição transparente de 48×64 com seis estados. A paleta PAL1 existente mantém o visor ciano; os geradores continuam na PAL3. Não há reamostragem da arte nativa aprovada.

O prop fica em 232,256. Somente a base do núcleo em 240,304, com 32×16 pixels, bloqueia passagem e recebe contato de dano. O mastro e os espaços antes ocupados pelo console estão livres e não recebem dano. O alvo dos inimigos é 256,312, centro da mesma base; o contato usa sua borda externa com margem de um pixel. As conexões foram reposicionadas e entram em pixels opacos do núcleo. A fase 16 compartilha essa mesma geometria.

A antena usa primeiro plano transparente: atores atrás ficam encobertos, e atores à frente usam prioridade de sprite. Uma barra de integridade de 32×8 fica junto ao núcleo; ao receber dano, somente a região da base pisca por meio segundo. O preparo instrui proteger o núcleo do rádio. Dano de 12 pontos, intervalo de cinco segundos e defesa de 120 segundos foram preservados.

Ignição altera somente os interiores dos dois motores superiores; piso, limite, antena, bateria e estações persistem. A breve apresentação pausa combate e contagem. Reiniciar restaura o cenário normal, a antena íntegra e os 120 segundos.

Memória: cache de 480 tiles + geradores 53 + rádio 45 = 578/640 tiles residentes. As duas fontes de cenário têm 1.047 padrões exatos cada; pico conservador de 470 visíveis. Heap do cache: 5.934 bytes por estado. Nenhuma substituição aproximada de tiles. As peças herdadas da sala 14 conservam seus pixels.

```sh
python3 game/tools/build_phase14_shipyard.py --check
python3 game/tools/build_phase15_shipyard.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase15_shipyard_emulator.py --output game/art/phase15-shipyard-v2/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase15_shipyard_emulator.py --pal --output game/art/phase15-shipyard-v2/validation/pal
```

As suítes verificam 28 câmeras e seis estados do rádio por região, pixels em VRAM, travessia por controle, faces sólidas, dano nos quatro lados da base, passagem livre pelo mastro, ausência de dano no mastro/console removido, prioridade dos atores e reação local ao dano. Também verificam pausa, ignição com combate congelado, reinício, defesa completa, resultado e continuação para a 16. A carga artificial usa três inimigos e 4+4 tiros em três setores; FPS e limites estão em `delivery.json`. A RAM prepara cenários isolados; navegação e defesa usam o código normal. Dificuldade humana e hardware físico não certificados.
