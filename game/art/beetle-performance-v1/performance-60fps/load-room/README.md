# Sala de carga do experimento

A [nova ROM experimental](Plaguefall-60fps-carga.bin) traz a sala **6. CARGA E PERFORMANCE** preparada para reproduzir a investigação pelo controle, sem injetar dados na RAM. No título, escolha **FASE TESTE** e depois a sala 6.

A sala abre no pátio usado na medição, com oito Baluartes inicialmente agrupados, escudos permanentes, até 16 projéteis por conjunto, mortes automáticas desligadas e jogador protegido. Os tiros se repõem automaticamente; não é preciso segurar A. A imunidade usa o piscar normal do personagem. Os oito inimigos continuam andando, se afastando e colidindo normalmente, com a lógica da build experimental.

Use **START → CONFIGURAR TESTE** para escolher Baluarte, Fortaleza, Escudeiro ou grupo misto Baluarte/Fortaleza. Também é possível ajustar quantidade (1/4/8/16), tiros por grupo (0/6/16), status, mortes em loop e proteção do jogador. **A** aplica e reinicia; **B** cancela e preserva a configuração. Os campos na tela mostram FPS atual/alvo, CPU, pico, inimigos e tiros ativos.

## Verificação dentro da sala

Entrada, seleção, configuração e medições foram feitas somente pelo controle no Genesis Plus GX. Cada medição cobre 1.800 VBlanks, após 180 de aquecimento. A leitura da SAT confirmou os oito corpos em todas as amostras dos seis casos por região; os dois conjuntos de tiros se mantiveram ativos nos casos com carga. Os tipos dos inimigos e os escudos foram conferidos. Também passaram cancelamento de configuração, quantidades 1/4/8/16 e mortes em loop.

| Oito blindados, até 16 tiros por conjunto | NTSC | PAL |
|---|---:|---:|
| Baluarte, padrão da sala | 60,0000 | 50,0000 |
| Fortaleza | 60,0000 | 50,0000 |
| Escudeiro | 60,0000 | 50,0000 |
| Quatro Baluartes + quatro Fortalezas | 59,9333 | 50,0000 |

O grupo misto NTSC perdeu **dois quadros em 30 segundos**: 1.798 atualizações em 1.800 VBlanks. Portanto, esta versão interativa não teve estabilidade absoluta nesse caso. Ela acrescenta reposição de projéteis e painel dentro da própria ROM; os resultados do ensaio anterior, com preparação externa, continuam vinculados à ROM anterior. O painel calcula FPS por janelas de um segundo, enquanto os relatórios registram a contagem completa de cada caso.

Os controles com Escudeiros e 6/0 tiros também mantiveram 60/50 FPS. Esses resultados não prometem a mesma frequência com 16 inimigos, mortes/efeitos extras ou qualquer movimentação do jogador. A sala permite justamente observar essas situações.

- [Resultados NTSC](../../validation/60fps/load-room-ntsc/report.json) e [PAL](../../validation/60fps/load-room-pal/report.json).
- [Captura do padrão](../../validation/60fps/load-room-ntsc/baluarte-16.png) e [configuração](../../validation/60fps/load-room-ntsc/configuration.png).
- [Patch desta revisão](changes.patch), [fontes](overlay/) e [manifesto](manifest.json).

## Alterações e reprodução

Além da configuração da sala, o painel transfere apenas os números alterados e distribui sua atualização entre quadros. A reposição usa registros de projéteis pré-calculados; a manutenção dos escudos evita reescrever todos os temporizadores em todos os quadros. A consulta da rota foi retirada de dentro do laço de inimigos. Três divisões positivas do envelope musical passaram a usar a instrução de divisão do 68000: a comparação de 80.000 quadros de áudio em quatro faixas e duas regiões produziu hashes de vozes/envelopes idênticos, além dos testes nativos anteriores.

Esta revisão é aplicada sobre o [protótipo anterior](../README.md); conserva os compromissos de frequência de lógica e preparação gráfica descritos nele. Os arquivos do jogo principal não receberam este conjunto. Houve outra alteração independente na ROM principal durante a execução; os hashes ficam registrados no manifesto.

Na raiz do repositório, usando um destino novo:

```sh
python3 game/art/beetle-performance-v1/performance-60fps/prepare.py --variant carga --destination /private/tmp/plaguefall-carga
make -C /private/tmp/plaguefall-carga -j4 GDK="$PWD/SGDK" OUT_DIR_LIB="$PWD/SGDK/out/release"
arch -x86_64 /usr/bin/python3 game/art/beetle-performance-v1/performance-60fps/load-room/verify_room.py --build-dir /private/tmp/plaguefall-carga/out/release --output /private/tmp/plaguefall-carga-ntsc
```

Acrescente `--pal` para a outra região. `compare_audio.py` recebe os diretórios do protótipo anterior e desta revisão. Uma compilação completa do pacote restaurado produziu a mesma ROM entregue, SHA-256 `261c05c73b4256219a2828c8da47c9facb6a9793a6784a0acc15f8e4816429d2`.
