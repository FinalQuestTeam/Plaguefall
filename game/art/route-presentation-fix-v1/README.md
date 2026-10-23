# Cortes de cenário e andamento da música — travessia e escolta

Investigação e correção da ROM em 22/10/2026. Build validada: `41e76ea6acbd47bbb99ba083890f42d46c88f334d117ade2429a609e29644a72`.

Havia dois tipos de corte. A câmera escrevia a posição de rolagem imediatamente,
mas enviava as novas linhas/colunas do mapa por DMA no próximo VBlank. Movimentos
para a esquerda/cima expunham células antigas ou vazias do anel de 64×32, sobretudo
quando a CPU perdia um quadro. Agora mapa e rolagem entram juntos no VBlank, com
os dados transferidos primeiro. Posições que não mudaram não geram novas escritas.

Além disso, o compositor copiava oito pedaços retangulares de uma pintura já
achatada: os recortes atravessavam pilares, tubulações e abrigos. Esses fragmentos
foram removidos. Os quatro marcos completos e quatro detalhes de chão por fase
continuam na composição. Os atlas passaram de 603/518 para **448/357 tiles**,
sem alterar a geometria, os buracos ou as três travessias de lama de altura inteira.

A música contava uma atualização do jogo como um quadro de tempo. Na medição da
ROM anterior, a escolta avançou 82 passos quando deveria avançar 90 em 12 segundos.
O sequenciador e os envelopes agora usam o número real de VBlanks transcorridos,
preservando a prioridade dos efeitos e a restauração das prévias e da abertura.
O teste carregado avançou os **90 passos esperados em NTSC e PAL**.

| Verificação | NTSC | PAL |
|---|---:|---:|
| Verificações de rotas aprovadas | 31 | 31 |
| Quadros conferidos por fase, nos dois eixos/sentidos | 1.500 | 1.500 |
| Células antigas / partes do terreno faltando | 0 / 0 | 0 / 0 |
| Verificações de menus aprovadas | 11 | 11 |
| Passos musicais em 12 segundos de carga, esperado 90 | 90 | 90 |

O teste consulta a posição efetivamente aplicada no VDP e compara todas as células
visíveis de cenário e de lama/lava com os dados de origem, quadro a quadro. Uma
execução da ROM anterior apresentou células erradas em 551/1.500 quadros da travessia
e 477/1.500 da escolta. Os testes também percorrem as rotas completas, conferem
colisão, atlas em VRAM, pausa/retomada, entrada, derrota, retry e conclusão.

**Limite observado:** o combate intenso ainda pode reduzir a simulação: o ensaio
piloto registrou 50 FPS NTSC e 42,83 FPS PAL. A correção mantém o andamento musical,
mas a saída PSG ainda é atualizada pelo loop principal, podendo ter pequenas variações
na articulação de notas durante uma queda de FPS. Não é uma garantia de
60/50 FPS constantes nem um driver de áudio independente no Z80.

[Validação consolidada](validation.json) · [NTSC](validation/ntsc.json) ·
[PAL](validation/pal.json) · [Mapa da travessia](mapa-04.png) ·
[Mapa da escolta](mapa-06b.png).

Reproduzir na raiz do repositório (macOS com o core Genesis Plus GX do RetroArch):

```sh
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_route_objectives_emulator.py --nodes 5,8 --matches 1 --seconds 100
arch -x86_64 /usr/bin/python3 game/tools/test_route_objectives_emulator.py --pal --nodes 5,8 --matches 1 --seconds 100
arch -x86_64 /usr/bin/python3 game/tools/test_menu_flicker_emulator.py
arch -x86_64 /usr/bin/python3 game/tools/test_menu_flicker_emulator.py --pal
```
