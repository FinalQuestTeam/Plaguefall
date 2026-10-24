# Protótipo de 60 FPS para avaliação

A [revisão com a sala 6 de carga pronta para uso pelo controle](load-room/README.md) está disponível em uma nova ROM. O padrão de oito Baluartes manteve 60/50 FPS; o grupo misto NTSC registrou duas perdas em 30 segundos dentro da sala. Os resultados abaixo se referem ao protótipo anterior.

**O conjunto experimental atingiu 60 FPS NTSC e 50 FPS PAL nos 24 casos da matriz.** Os dois ensaios adicionais de cinco minutos com carga máxima também completaram 18.000 atualizações em 18.000 VBlanks, sem quadros perdidos. Foram testados oito Baluartes e o grupo misto de quatro Baluartes e quatro Fortalezas. São resultados no Genesis Plus GX; a campanha inteira e um console físico ainda não foram validados.

A [ROM experimental](Plaguefall-60fps-experimental.bin) contém as mudanças no jogo completo. Este conjunto não foi aplicado às fontes, recursos ou saída principal do workspace. A ROM principal recebeu uma alteração independente durante a execução; os hashes inicial e final estão no [manifesto](manifest.json). As comparações abaixo usam a mesma captura isolada das fontes e dos recursos.

| Oito blindados, 16 tiros por conjunto | NTSC original | Protótipo NTSC | PAL original | Protótipo PAL |
|---|---:|---:|---:|---:|
| Baluarte | 23,80 | 60,00 | 24,75 | 50,00 |
| Fortaleza | 23,93 | 60,00 | 25,00 | 50,00 |
| Escudeiro | 27,40 | 60,00 | 25,00 | 50,00 |
| Quatro Baluartes + quatro Fortalezas | 24,00 | 60,00 | 24,92 | 50,00 |

Confira os valores sem arredondamento por contagem de quadros no [comparativo](comparison.json). Cada caso da matriz mede 1.800 VBlanks após 180 de aquecimento. Há cargas de 0, 6 e 16 tiros por conjunto. As execuções são determinísticas, com uma execução por caso; não são partidas aleatórias independentes.

## O que precisa ser decidido

O resultado exige o conjunto completo. Retirar uma parte requer medir novamente.

- **Lógica dos amarelos e roxos em quatro grupos:** cada inimigo atualiza a cada quatro quadros, a 15 Hz NTSC ou 12,5 Hz PAL. O deslocamento é multiplicado por quatro e os temporizadores usam decrementos saturados de quatro. Jogador e tiros continuam atualizando a cada quadro. A posição dos inimigos avança em passos maiores; contato, direção e limites de temporizadores podem reagir até três quadros depois. Vermelhos, laranjas e chefe mantêm sua frequência original de lógica.
- **Afastamento distribuído:** cada corpo recebe seu empurrão a cada quatro quadros, em oito direções, com deslocamento dobrado por aplicação. Continua havendo afastamento e colisão com a arena, mas a formação e a resposta do grupo mudam.
- **Gráficos dos inimigos em quatro grupos:** corpos entram na lista de sprites em todos os quadros; direção, pose e upload de cada slot são preparados a cada quatro. Uma troca pode demorar até três quadros. A tolerância de animação após parar também passa a contar amostras gráficas.
- **Escudo desenhado dentro do corpo roxo:** uma cópia dos frames nativos recebe o distintivo existente de 8×8 no canto superior direito. A arte normal fica em seu banco original. Isso elimina oito sprites extras de escudo nesse teste e acrescenta 118.080 bytes de recurso à ROM. Escudos do jogador e do chefe conservam os marcadores separados.
- **Admissão de sprites por faixas de oito pixels:** mantém limites conservadores de 80 sprites totais, 20 por linha e 320 pixels por linha, com admissão atômica dos atores e do chefe. Pode recusar sprites opcionais ou tiros antes da implementação por linha exata; simulação e capacidade dos projéteis continuam iguais.

Também foram aplicadas mudanças sem redução intencional de frequência: descarte de tiros fora dos limites agregados dos inimigos, atalhos de colisão em espaço comprovadamente livre, atributos gráficos dos tiros em cache, laços de tiros separados para reduzir pressão de registradores e caches para andamento musical e ausência de efeitos de morte. O campo novo do projétil ocupa o byte de preenchimento; a estrutura mantém 20 bytes.

## Verificações

A leitura da SAT real confirmou oito corpos em todas as amostras finais, projéteis renderizados dos dois lados e respeito aos limites de scanline. Os inimigos continuaram vivos, blindados, visíveis e agrupados; os dois conjuntos de tiros ficaram ativos em todos os quadros com carga. O teste usa movimento, colisões, autofire, áudio e HUD reais. Novos spawns e invocações ficam suspensos para preservar oito inimigos. A carga máxima injeta até 16 tiros por lado, acima do limite normal da fase 1 usada como arena.

Os [testes nativos](native-equivalence.log), com ASan/UBSan, verificaram 540.000 consultas de colisão, 86.498 movimentos a partir de posições válidas equivalentes ao original, 131.072 atributos de projéteis e 2.048 listas aleatórias de sprites. Os [testes de execução](native-runtime.log) cobrem direções, banco de escudo ligado/desligado, expiração e saturação de mortes, chefe, música, SFX e restauração após preview. O emulador conferiu 1.248 frames de arte e SAT em NTSC/PAL.

- [Matriz final NTSC](../validation/60fps/final2-ntsc/report.json) e [PAL](../validation/60fps/final2-pal/report.json).
- [Dois ensaios de cinco minutos](../validation/60fps/long2-ntsc/report.json).
- [Controle original NTSC](../validation/60fps/baseline-ntsc/report.json) e [PAL](../validation/60fps/baseline-pal/report.json).
- [Patch das fontes](changes.patch), [fontes alteradas](overlay/) e [histórico de medições](iterations.json).

A versão anterior passou na matriz curta, mas perdeu um quadro no ensaio longo do grupo misto. Esse resultado foi preservado em `../validation/60fps/long-ntsc/`; a ROM entregue usa a revisão seguinte, que passou nos dois ensaios longos.

## Reprodução isolada

Na raiz do repositório:

```sh
python3 game/art/beetle-performance-v1/performance-60fps/prepare.py --destination /private/tmp/plaguefall-60-review
make -C /private/tmp/plaguefall-60-review -j4 GDK="$PWD/SGDK" OUT_DIR_LIB="$PWD/SGDK/out/release"
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --combat --audit-sprites --repeats 1 --frames 1800 --build-dir /private/tmp/plaguefall-60-review/out/release --output /private/tmp/plaguefall-60-ntsc
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --combat --audit-sprites --pal --repeats 1 --frames 1800 --build-dir /private/tmp/plaguefall-60-review/out/release --output /private/tmp/plaguefall-60-pal
python3 game/art/beetle-performance-v1/performance-60fps/validate_runtime.py /private/tmp/plaguefall-60-review
```

O diretório de destino deve ser novo. `prepare.py --variant baseline` restaura o controle sem o overlay. Passe os dois diretórios a `validate.py` para repetir a comparação nativa. `build_shield_frames.py /caminho/do/build --check` verifica o banco gráfico derivado. Uma compilação completa a partir do pacote restaurado produziu exatamente o mesmo SHA-256 da ROM entregue: `1fc88e9312b3a14023f98a55d874faacd747059625e51607eb737c7a1e8d4572`.
