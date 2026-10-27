# Fase 14 — estaleiro modular

[Revisão visual](review.html) · [Cenário completo](complete-with-generators.png) · [Geometria e memória](manifest.json).

Mapa512×576: faixa superior de motores independente, faixa inferior com porta, laterais repetíveis e console central como prop transparente128×112 em192,224. A bateria inferior também é um conjunto separado. O campo útil vertical passa de192para384px. Cinco geradores novos48×48mantêm a operação por aproximação; colisões acompanham suas bases, os props e a antena.

Ativação:10segundos diante do painel, sem atirar. Cada estação tem sua própria barra32×8acima do gerador e relógio de afastamento. Fora do alcance, a cada1segundo completo se perde1segundo de trabalho (10%), até zero. Reaproximar retoma o valor restante; atirar perto suspende o avanço sem perda; a pausa congela trabalho e decaimento. Estações ligadas permanecem ligadas. Barras parciais continuam visíveis durante o afastamento e desaparecem ao zerar ou concluir.

Seis ramais ligam três estações ao console, duas à bateria e a bateria ao console. Os conduítes são módulos nativos8×8com retas, curvas, junções e abraçadeiras;12terminais entram nas silhuetas dos equipamentos. O exportador verifica cada pixel central dos trajetos, as sete peças conectadas e a sobreposição dos terminais a pixels opacos. As conexões ficam no chão e permitem travessia.

A arquitetura foi extraída da fonte original1448×1086, com amostragem direta em grade nativa1px e paleta16cores. O console foi isolado com ImageGen integrado; [prompt exato](prompts/control-station.txt) e [RGBA original](source/control-station.png) preservados. A conversão elimina apenas o halo semitransparente externo. Não há etapa intermediária de blocos2×2ou4×4.

O gerador foi criado com ImageGen integrado para o padrão azul/cinza/dourado do console e bateria: [prompt](prompts/generator-native.txt), [fonte RGBA](source/generator-native-grid.png), [sprite final48×48](objects/generator-0.png) e [seis estados](generator-states.png). A exportação faz amostragem direta por vizinho mais próximo e quantiza para a mesma paletaPAL3do cenário, sem filtro de suavização. Carcaça e pés permanecem iguais; visor e indicadores mudam em pixels nativos. Os quadros e a máscara48×48são específicos da14.

O piso usa [placas de ferro64×64](modules/iron-floor-plate.png), com quatro rebites nos cantos e juntas contínuas nos quatro lados. Material criado com ImageGen integrado: [fonte](source/iron-floor-plate.png) e [prompt](prompts/iron-floor.txt). Amostragem direta em detalhe nativo1px; o mesmo módulo se repete sob equipamentos e conduítes. As bordas opostas são verificadas pixel a pixel.

Os limitadores laterais têm módulos32×64com extremidades iguais; a faixa inferior usa módulo112×64com bordas iguais e cantos próprios. O exportador verifica a igualdade dos pixels das emendas. As peças estão em `modules/`; `upper.png`, `lower.png` e `objects/control-station.png` são recursos independentes.

1.190tiles de cenário exatos na ROM; cache480 + gerador53 + cinco barras20 =553/640tiles residentes. Pico conservador472tiles visíveis. Os seis quadros do gerador ocupam1.696bytes após deduplicação exata. Cada barra reserva4tiles próprios para preservar preenchimentos simultâneos diferentes. O cache carrega apenas padrões visíveis, sem substituição aproximada. As fases [15](../phase15-shipyard-v2/review.html) e [16](../phase16-shipyard-v2/review.html) compartilham cenário e geradores, com núcleo de rádio compacto no lugar deste console.

```sh
python3 game/tools/build_phase14_shipyard.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase14_shipyard_emulator.py --output game/art/phase14-shipyard-v2/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase14_shipyard_emulator.py --pal --output game/art/phase14-shipyard-v2/validation/pal
```

Os relatórios NTSC/PAL em `validation/` registram28câmeras por região, seis estados48×48idênticos emVRAM, coresPAL3, cache, colisões, pausa e o limite exato da ativação600/500atualizações. Decaimento60/50atualizações, limite zero, retomada, estações concluídas e barras/relógios independentes também foram verificados. Os cinco geradores foram ativados por controle. Resultados, continuidade15e carga com quatro inimigos e4+4tiros passaram:57,3FPSNTSC/49,5PAL. RAM prepara cenários isolados; o objetivo usa apenas o controle. Hardware físico e dificuldade humana não certificados.
