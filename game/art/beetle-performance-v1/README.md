# Investigação: lentidão com oito besouros blindados

## Protótipo de 60 FPS pronto para avaliação

O conjunto experimental passou nos 24 casos: **60 FPS NTSC e 50 FPS PAL**, com oito blindados e cargas de 0/6/16 tiros por conjunto. Também passou em dois ensaios NTSC de cinco minutos com carga máxima, sem quadros perdidos. A ROM é separada; as mudanças de desempenho não foram aplicadas ao jogo principal.

Para chegar ao resultado, o protótipo combina otimizações de colisão, montagem de sprites e caches com mudanças a avaliar: lógica dos amarelos/roxos a 15 Hz NTSC, preparação gráfica dos inimigos em quatro grupos, afastamento distribuído e escudo incorporado aos frames roxos. Jogador e tiros atualizam em todos os quadros. Há mudanças na suavidade e no tempo de reação dos inimigos.

[ROM experimental, resultados, compromissos e reprodução](performance-60fps/README.md). O registro detalha também uma alteração independente na ROM principal durante o trabalho; a comparação usa capturas isoladas.

## Experimento anterior: afastamento mais barato

**Houve melhora parcial; a mudança continua somente no experimento.** O código de inimigos e a ROM principal mantiveram os hashes anteriores ao ensaio. Foram feitas 72 execuções: 12 configurações em NTSC/PAL para cada uma de três compilações isoladas da mesma captura das fontes. Apenas a função de separação entre inimigos difere. Cada configuração tem uma execução determinística, com 180 VBlanks de aquecimento e 1.800 medidos, usando o mesmo protocolo de oito blindados com cargas de 0, 6 e 16 tiros por lado.

Foram comparadas duas implementações:

- **Compacta:** pré-calcula centros e tamanhos, trabalha só com os inimigos ativos e usa acumuladores de 16 bits com limites demonstrados. Mantém os mesmos empurrões inteiros dos inimigos de 16/24/32 pixels.
- **Oito direções:** faz as mesmas simplificações e troca a normalização dos vetores por comparações e deslocamentos de bits. O afastamento fica quantizado em oito direções e pode mudar ligeiramente a formação do grupo.

As duas mantêm a atualização a cada dois quadros, o limite de vinte unidades de ponto fixo por eixo e a chamada de colisão `ARENA_move`. Não removem a separação nem mudam o teto de inimigos ou de tiros.

| Oito Baluartes | Região | Original | Compacta | Oito direções |
|---|---|---:|---:|---:|
| Sem tiros | NTSC | 33,80 | 33,80 | 33,77 |
| 6 tiros por lado | NTSC | 30,00 | 30,00 | 30,00 |
| 16 tiros por lado | NTSC | 23,80 | 25,97 | 26,70 |
| Sem tiros | PAL | 33,44 | 36,83 | 38,00 |
| 6 tiros por lado | PAL | 25,06 | 25,06 | 25,00 |
| 16 tiros por lado | PAL | 24,75 | 24,75 | 24,81 |

Na carga alta NTSC, a compacta ganhou **9,1%** e a de oito direções **12,2%** no caso de Baluartes. No grupo misto com quatro Baluartes e quatro Fortalezas e 16 tiros por lado, o resultado passou de **24,00 para 25,43/26,57 FPS**, respectivamente. Com seis tiros por lado, o ganho de CPU não bastou para superar o patamar de 30 FPS NTSC ou aproximadamente 25 FPS PAL. **A meta de 60/50 FPS continua não atingida.** Pequenas diferenças de centésimos de FPS não são ganhos relevantes.

Os testes nativos com ASan/UBSan compararam a compacta com a rotina original em 4.096 cenas de inimigos de 16/24/32 pixels e obtiveram resultados idênticos. Também verificaram cadência, atores inativos, limites de deslocamento, obstáculos e bordas em uma arena de teste. A média das distâncias entre pares, após 600 aplicações sobre oito inimigos inicialmente coincidentes, foi 37,203 px na original e compacta, e 37,607 px na de oito direções. Isso verifica que o afastamento continua funcionando nesse ensaio; não substitui uma avaliação de todas as formações da campanha. O teste em ROM usa o `ARENA_move` real, sem alteração do cenário ou da renderização.

Durante a preparação, o vínculo do script com `invTimer` foi tornado independente dos sufixos privados do LTO, que podem trocar entre jogador e NPC conforme a compilação. A fase 1 não possui NPC ativo; o ensaio inicializa os temporizadores correspondentes e verifica que o jogador mantém 100 HP. Os resultados acima são os ensaios completos após essa correção do instrumento de teste.

- [Comparação completa e hashes](validation/separation/comparison.json).
- [Resultado dos testes nativos](validation/separation/native-test.txt).
- [Rotina experimental](separation-experiment/separate.inc), [patch compacto](separation-experiment/compact.patch) e [patch de oito direções](separation-experiment/compass.patch).
- [Controle NTSC](validation/separation/baseline-ntsc/report.json), [compacta NTSC](validation/separation/compact-ntsc/report.json), [oito direções NTSC](validation/separation/compass-ntsc/report.json).
- [Controle PAL](validation/separation/baseline-pal/report.json), [compacta PAL](validation/separation/compact-pal/report.json), [oito direções PAL](validation/separation/compass-pal/report.json).

Reprodução dos testes nativos e preparação das compilações isoladas:

```sh
python3 game/art/beetle-performance-v1/separation-experiment/test_separation.py
python3 game/art/beetle-performance-v1/separation-experiment/prepare.py /private/tmp/separacao-novo-teste
```

Compile as pastas `baseline`, `compact` e `compass` geradas, fornecendo `GDK` e `OUT_DIR_LIB` do SDK do projeto ao Make. Execute `game/tools/benchmark_enemy_shields.py --combat --repeats 1 --build-dir PASTA/out/release --output DESTINO`, repetindo com `--pal` para cada variante. A captura de fontes desse ensaio é nova; use o controle correspondente acima para avaliar os ganhos, não os números de revisões anteriores.

## Experimento adicional: compartilhar frames entre inimigos iguais

**Testado e não adotado como otimização de desempenho.** O cache compartilhado economizou cópias de imagens na VRAM, mas não melhorou de forma consistente os casos críticos. A versão que preserva as fases individuais das animações piorou os casos com besouros grandes e tiros. Sincronizar o passo dos inimigos por espécie aumentou a reutilização das imagens, mas também não resolveu a lentidão.

Foram compiladas três versões isoladas a partir da mesma captura das fontes: original, cache compartilhado e cache compartilhado com animação sincronizada por tipo. Apenas `src/system/video/enemygfx.c` difere entre elas. Cada versão passou pelas mesmas 12 configurações em NTSC e PAL, com 1.800 VBlanks medidos por configuração: **72 execuções** no total. Há uma execução determinística de cada configuração por versão/região. A comparação usa uma nova versão de controle; os números não devem ser comparados diretamente aos ensaios anteriores feitos com outras revisões do jogo.

| Oito blindados / tiros por lado | Região | Original | Compartilhado | Compartilhado + sincronizado |
|---|---|---:|---:|---:|
| Baluarte / 6 | NTSC | 29,20 | 26,60 | 28,50 |
| Baluarte / 16 | NTSC | 22,50 | 20,93 | 22,47 |
| Baluarte / 6 | PAL | 25,00 | 25,00 | 25,00 |
| Baluarte / 16 | PAL | 22,33 | 20,47 | 22,06 |
| Quatro Baluartes + quatro Fortalezas / 6 | NTSC | 28,90 | 25,90 | 26,60 |
| Quatro Baluartes + quatro Fortalezas / 16 | NTSC | 22,33 | 20,97 | 21,57 |

No caso de oito Baluartes com seis tiros por lado no NTSC, o grupo passou de oito cópias distintas para cerca de **7,33** no compartilhamento simples e **4,43** no sincronizado. Este último representa aproximadamente 45% menos cópias referenciadas pelo grupo, mas não equivale a 45% menos CPU nem mede todos os frames antigos mantidos no cache. As amostras de RAM podem observar o carregador durante uma atualização que atravessa o VBlank; contagens instantâneas de prontidão não bastam para concluir que um sprite deixou de aparecer.

O protótipo usa uma chave de espécie, direção canônica e pose, com espelhamento horizontal independente por inimigo. Reutiliza hits mesmo após esgotar o limite de quatro uploads, mantém referências para proteger imagens compartilhadas e impede sobrescrever destinos de DMA já selecionados no quadro. As animações individuais são preservadas na primeira variante; a segunda alinha as poses por espécie. Em teste uniforme, oito atores reutilizam um único upload de 512 bytes; com as quatro poses de caminhada residentes, a troca de fase não exige upload novo. Na formação de combate, a combinação de poses e direções reduz a frequência desses casos favoráveis; o custo extra de gerenciamento do cache não compensou a economia de uploads.

Foram verificados 1.248 casos de arte no emulador, cobrindo 13 tipos, oito direções e seis poses em NTSC/PAL, com comparação de VRAM e SAT na variante sincronizada. As duas variantes passaram pelos testes nativos com ASan/UBSan, incluindo compartilhamento, espelhamento, troca de tipo, desaparecimento do ator original, limite de DMA e 2.400 quadros de pressão/falhas de cache por variante. O carregador de produção foi restabelecido ao conteúdo exato anterior ao experimento; os protótipos e testes estendidos ficam preservados abaixo. A ROM principal não recebeu essa otimização.

- [Comparação completa, hashes e critérios](validation/shared-frames/comparison.json).
- [Protótipo compartilhado](shared-frame-experiment/shared/src/system/video/enemygfx.c), [sincronizado](shared-frame-experiment/synchronized/src/system/video/enemygfx.c) e [original usado no controle](shared-frame-experiment/baseline/src/system/video/enemygfx.c).
- [Validação de arte NTSC](validation/shared-frames/directions-ntsc/report.json) e [PAL](validation/shared-frames/directions-pal/report.json).

Para repetir os testes nativos dos protótipos preservados:

```sh
python3 game/art/beetle-performance-v1/shared-frame-experiment/test_shared_frames.py --variant shared
python3 game/art/beetle-performance-v1/shared-frame-experiment/test_shared_frames.py --variant synchronized
```

## Teste adicional: oito blindados agrupados e tiros ativos

O teste solicitado foi concluído em NTSC e PAL, em uma compilação isolada sem instrumentação. **A meta de 60/50 FPS não foi atingida.** Foram 24 configurações, cada uma repetida três vezes a partir do mesmo estado salvo, totalizando 72 execuções. As repetições são replays determinísticos, não partidas aleatórias independentes.

| Grupo de oito blindados | Tiros por lado | NTSC (meta 60) | PAL (meta 50) |
|---|---:|---:|---:|
| Baluarte | 6 | 30,00 | 25,03 |
| Baluarte | 16 | 23,83 | 24,75 |
| Fortaleza | 6 | 30,00 | 25,00 |
| Fortaleza | 16 | 23,97 | 25,00 |
| Escudeiro | 6 | 30,00 | 25,44 |
| Escudeiro | 16 | 27,50 | 25,00 |
| Quatro Baluartes + quatro Fortalezas | 6 | 30,00 | 25,03 |
| Quatro Baluartes + quatro Fortalezas | 16 | 24,00 | 24,92 |

Cada execução mede 1.800 VBlanks após 180 de aquecimento: 30 segundos medidos no NTSC e 36 no PAL. Os oito inimigos começam sobrepostos e continuam se movimentando e se separando normalmente. As verificações confirmaram oito inimigos blindados e visíveis em todas as amostras, em um grupo de no máximo 128×128 pixels. Os dois conjuntos de projéteis permaneceram não vazios em todas as 48 execuções com tiros, e o autofire normal foi observado. Há também 24 execuções de controle sem tiros.

As cargas de 6/16 são os limites de reposição por conjunto, não uma promessa de que todos os projéteis sobrevivem ao quadro: colisões continuam consumindo tiros. O relatório registra mínimo, média e máximo após cada passo. Os slots inativos recebem projéteis em movimento com tempos de vida escalonados; tiros inimigos são uma carga injetada, pois besouros roxos não passam a atirar. A carga de 16 usa a capacidade global e excede o limite normal da fase 1, que serve como arena controlada. A fica pressionado nos casos com tiros; invocação e novos spawns ficam desativados para preservar os oito inimigos.

ROM isolada testada: `ea8db11bd481c8751ad240da5e280a18694f19361a7f7f4300d7a79e38ca2f0e`. A ROM principal manteve seu hash durante o ensaio. Houve alterações paralelas nas fontes do workspace após a captura; os resultados correspondem à compilação isolada do início do teste, e não às edições posteriores. O teste não aplica otimizações de desempenho.

- [Resumo e identificação da compilação](validation/combat-summary.json).
- [Resultados NTSC](validation/combat-ntsc/report.json) e [PAL](validation/combat-pal/report.json).
- [Captura do grupo misto com carga de 16 tiros por lado](validation/combat-ntsc/combat-type-2-load-16-mixed.png).

Reprodução com a compilação a verificar:

```sh
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --combat --build-dir /caminho/do/build --output /private/tmp/besouros-combate-ntsc
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --combat --pal --build-dir /caminho/do/build --output /private/tmp/besouros-combate-pal
```

## Investigação inicial, sem tiros

Investigação de 22/10/2026. Problema reproduzido no Genesis Plus GX, usando o laço real da campanha. A ROM final está sem instrumentação e os três arquivos de produção usados nos experimentos foram restabelecidos exatamente ao conteúdo anterior à investigação. Esta entrega contém diagnóstico e ferramenta de reprodução; não aplica uma correção de desempenho.

## Medições finais

Cada caso parte do mesmo estado da fase 1 e executa 120 VBlanks de aquecimento e 600 de medição. O cenário injeta inimigos para comparar cargas, inclusive acima do limite normal dessa fase. Os inimigos se movimentam normalmente e se agrupam perto do jogador; não há disparos. A invulnerabilidade do jogador evita encerrar o ensaio. Os temporizadores de escudo e invocação ficam suspensos para manter população e estado comparáveis.

| Tipo / quantidade | NTSC sem escudo | NTSC com escudo | PAL sem escudo | PAL com escudo |
|---|---:|---:|---:|---:|
| Baluarte × 4 | 60,0 | 60,0 | 50,0 | 50,0 |
| Baluarte × 8 | 40,1 | 33,6 | 34,83 | 33,5 |
| Fortaleza × 4 | 60,0 | 60,0 | 50,0 | 50,0 |
| Fortaleza × 8 | 40,0 | 32,5 | 36,17 | 33,75 |
| Escudeiro × 8 | 44,3 | 39,8 | 50,0 | 40,75 |

Os valores são quadros de jogo por segundo, calculados por `phaseStats.frames / vtimer`, com a frequência da região. Não são a velocidade de execução do computador. A carga SGDK é uma média de oito quadros e pode esconder picos alternados: mesmo com média abaixo de 100%, um quadro pode perder seu prazo. Não se devem comparar percentuais SGDK entre regiões como se fossem tempos absolutos.

ROM final SHA-256: `d0eb603294a2f6ae67766b1ff6ee8c29215f9147168b43dca524822633b089a2`.

## Causas encontradas

1. **Separação entre inimigos agrupados.** `ENEMIES_separate` examina todos os pares a cada dois quadros: quatro inimigos geram seis pares; oito geram 28. Além da comparação, pares próximos calculam empurrões e fazem movimentos com consulta de colisão. A concentração de trabalho em quadros alternados provoca picos. Em uma compilação experimental, retirar somente a chamada da separação levou oito Baluartes sem escudo de 40 para 60 FPS. Com os escudos, a lentidão persistiu. Esse experimento altera a formação do grupo e serve para identificar o gargalo, não como correção pronta.
2. **Ícones de status e admissão de sprites.** O escudo acrescenta um marcador por inimigo em todos os quadros. A montagem dos marcadores e a verificação dos limites por linha aumentam o custo da renderização; os grupos sobrepostos podem exigir o caminho detalhado de admissão. Na compilação instrumentada, oito Baluartes passaram de aproximadamente 0,06 para 1,64 ms na emissão dos marcadores e de 0,50 para 1,37 ms no fechamento da lista. São estimativas pelo contador de vídeo do SGDK, com resolução e limitações durante VBlank, não medidas exatas por instrução.
3. **Sprites grandes e atualização gráfica.** Baluarte e Fortaleza usam 32×32, ou 16 tiles; Escudeiro usa 16×16, ou quatro tiles. A preparação de frames, os uploads e a montagem da lista somam carga ao movimento e à separação. O problema também ocorre com invocação desativada e sem tiros: não depende de um aumento oculto da população nem do combate com projéteis.

O booleano de invulnerabilidade não é, sozinho, a explicação. O controle amarelo, que não possui ciclo de escudo, também perde desempenho com oito inimigos agrupados. Forçar os ícones de escudo nesse controle agrava a queda.

## Onde pode aparecer

Pelos rosters atuais, os blindados aparecem nas fases **3, 4, 7, 11, 12, 13A, 13B, 14 e 15**. As fases 3 e 4 têm teto explícito de quatro inimigos; as demais usam o teto padrão de 15. O teste foi uma comparação controlada na fase 1, não uma execução de cada uma dessas fases. Cenário, tiros, mortes e outros efeitos podem mudar o resultado.

A prioridade de correção é reduzir os picos da separação preservando o afastamento dos inimigos, depois reduzir o custo dos marcadores e da admissão de sprites. Remover a separação permite empilhamento e não foi mantido como solução.

## Reprodução e evidências

Na raiz do repositório, com a ROM e os símbolos compilados:

```sh
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --output /private/tmp/besouros-ntsc
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --pal --output /private/tmp/besouros-pal
```

- [Medição final NTSC](validation/ntsc/report.json) e [PAL](validation/pal/report.json): 32 cenários concluídos, com verificações de população e permanência no jogo.
- [Oito Baluartes blindados no emulador](validation/ntsc/type-2-shield-1.png).
- [Perfil temporário da campanha](validation/campaign-profile/report.json) e [experimento sem separação](validation/no-separation-profile/report.json). Essas ROMs experimentais não foram mantidas como ROM principal.

Nos relatórios instrumentados, `render_subticks` segue: início/HUD, herói, gráficos dos inimigos, corpos/projéteis, marcadores, efeitos/sombras, admissão final, envio SAT. `logic_subticks[2]` mede a atualização dos inimigos. Um subtick corresponde nominalmente a 1/76800 s; o contador tem precisão limitada durante VBlank. Os tempos incluem o custo da instrumentação e não substituem os números finais sem instrumentação.
