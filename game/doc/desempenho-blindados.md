# Desempenho dos blindados na ROM principal

A correção foi integrada em 23/10/2026 ao código atual do jogo, sobre a revisão `8cedcde`, preservando o rádio, as cores e as demais interfaces recentes. O build normal gera [Plaguefall.bin](../out/release/Plaguefall.bin). O experimento antigo permanece como registro da investigação.

O conjunto distribui a lógica dos amarelos e roxos e a preparação gráfica dos inimigos em quatro grupos. O afastamento entre corpos também é distribuído; o distintivo de escudo dos roxos fica incorporado aos seus frames. Foram integrados os atalhos de colisão, os caches de atributos dos tiros, de efeitos de morte e de andamento musical, além da montagem da lista de sprites com limites conservadores por faixa de oito pixels.

Jogador e projéteis continuam atualizando a cada quadro. Amarelos e roxos atualizam sua lógica a cada quatro quadros, com deslocamentos e temporizadores compensados; isso modifica a suavidade do movimento e permite até três quadros adicionais de reação. Vermelhos, laranjas e chefe mantêm a frequência original de lógica. Direção e pose dos gráficos dos inimigos também podem demorar até três quadros para mudar. A seleção conservadora da lista de sprites pode omitir tiros ou efeitos antes do limite por linha exata, sem reduzir a capacidade simulada.

## Sala 6

Abra **Fase Teste → 6. Carga e performance**. O padrão é oito Baluartes agrupados, escudo ligado, mortes automáticas desligadas e reposição de até 16 projéteis por conjunto. START → CONFIGURAR TESTE permite trocar por Fortalezas, Escudeiros ou grupo misto, alterar quantidade, carga, status e mortes. As opções das outras salas permanecem disponíveis.

O HUD mostra FPS, CPU, pico, inimigos e tiros. A reposição de projéteis é exclusiva da sala de carga; a campanha conserva seus disparos normais.

## Validação desta integração

Os [resultados e hashes da ROM recompilada](../art/beetle-performance-v1/validation/integrated-current/report.json) distinguem os testes atuais dos experimentos históricos.

- **Combate:** 12 configurações em NTSC e 12 em PAL, com oito blindados de quatro formações e cargas de 0/6/16 tiros por conjunto; 1.800 VBlanks medidos por configuração. Todos mantiveram 60/50 FPS.
- **Duração:** dois casos NTSC de cinco minutos, com oito Baluartes ou grupo misto e carga máxima. Cada caso completou 18.000 atualizações em 18.000 VBlanks.
- **Sala 6, por controles:** seis configurações por região. O padrão Baluarte manteve 60/50 FPS. No NTSC, o misto perdeu três quadros em 1.800 (59,90 FPS) e Fortaleza perdeu um (59,9667 FPS); os demais mantiveram 60. Todos os casos PAL mantiveram 50. Configurações, quantidades, cancelamento e mortes automáticas passaram.
- **Gráficos:** SAT real com oito corpos nos ensaios de carga, limites de sprites respeitados e 1.248 frames de arte conferidos em NTSC/PAL.
- **Testes nativos:** recursos gerados, mira, regras de morte, direções, alternância do banco de escudos e áudio passaram com ASan/UBSan. A equivalência de colisões, movimentos válidos e atributos dos tiros também foi conferida. As quatro trilhas conservaram as sequências de áudio do código anterior.

Os resultados usam Genesis Plus GX. São cenários determinísticos de carga; não constituem validação de toda a campanha nem de hardware físico. O relatório registra separadamente a aprovação funcional da sala e sua meta estrita de desempenho.

## Repetir

Na raiz do repositório:

```sh
make -C game -j4 GDK="$PWD/SGDK" OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/benchmark_enemy_shields.py --combat --audit-sprites --repeats 1 --frames 1800 --build-dir game/out/release --output /private/tmp/plaguefall-combate-atual
arch -x86_64 /usr/bin/python3 game/tools/test_load_room_emulator.py --build-dir game/out/release --output /private/tmp/plaguefall-sala6-atual
```

Adicione `--pal` e use outro destino para a região PAL. Para os dois casos longos, acrescente ao benchmark `--formations Baluarte,mixed --loads 16 --frames 18000`. O teste da sala usa somente controles; o benchmark de combate prepara em RAM os inimigos e a carga e mede o laço real da fase 1.

Ao reexportar as animações, `game/tools/pack_actor_animation.py` também regenera o banco de escudos a partir da arte atual; `--check` verifica sua sincronização.
