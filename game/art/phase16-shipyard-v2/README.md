# Fase 16 — mesmo estaleiro, novas janelas

[Revisão visual](review.html) · [Cenário nativo](complete.png) · [Janela nativa](objects/engine-interior-native.png) · [Geometria e memória](manifest.json) · [Validação e ROM](delivery.json).

A fase 16 usa a sala atual das fases 14/15: mundo de 512×576 pixels, piso de ferro rebitado, limites repetíveis, cinco geradores ligados de 48×48, rádio compacto de 48×64, bateria e conexões. A sala e os equipamentos são copiados da 15; a tabela de colisão é compartilhada literalmente. Somente a base de 32×16 do núcleo bloqueia passagem; o mastro é visual. A posição inicial e os limites de circulação também são os mesmos. O rádio permanece ligado. O Escorpião conserva sua vida, ataques e comportamento originais.

Somente os interiores das duas janelas superiores mudam, nos retângulos (56,16)–(200,96) e (320,16)–(464,96). O módulo completo foi recriado com ImageGen integrado usando a janela existente como referência; a exportação amostra para a grade nativa de 184×112 e utiliza somente o interior de 144×80. A moldura, soleira e todos os pixels externos vêm diretamente da sala 15. A conversão usa a paleta existente de 16 cores, tiles de 8×8 e nenhuma substituição aproximada de padrões. [Fonte gerada](source/engine-window.png) · [Prompt exato](prompts/engine-window.txt).

A exportação compara todos os pixels fora das janelas com a fonte da 15 e reconstrói integralmente a imagem a partir dos tiles para verificar igualdade. Cache de 480 tiles + 53 de geradores + 45 de rádio = 578/640 tiles residentes. Fonte de 1.047 padrões, máximo conservador de 470 visíveis, heap de 5.934 bytes. A imagem completa é uma composição da arte; as capturas em `validation/` são da ROM no Genesis Plus GX.

```sh
python3 game/tools/build_phase16_shipyard.py
python3 game/tools/build_campaign_launch.py
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase16_shipyard_emulator.py --output game/art/phase16-shipyard-v2/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase16_shipyard_emulator.py --pal --output game/art/phase16-shipyard-v2/validation/pal
```

O teste verifica 28 câmeras por região, cenário e equipamentos em VRAM, paleta, limites, faces sólidas, travessia por controle, pausa e restauração, derrota/reinício e vitória contra o chefe original. A RAM prepara os ensaios isolados e aumenta a vida/proteção do jogador uma vez no ensaio de combate; a luta usa somente comandos do controle e não altera a vida do chefe. Os FPS desse ensaio não representam uma certificação de toda a carga possível. As regressões completas das fases 14 e 15 também passaram em NTSC/PAL na mesma ROM. Hardware físico não testado.
