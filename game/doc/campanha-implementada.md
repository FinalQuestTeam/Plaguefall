# Campanha implementada e playtests

ROM de produção: `ea9caca81c9baa64cd07d011f7b8ae234cb883b50a81c791fdcea179f23a558f`. 2,490,368bytes; RAM estática19,830bytes.

As 19 versões de fase estão integradas em 16 etapas por partida. A animação existente de 101 s abre o jogo. Igreja, resgate e Dinorah produzem oito encerramentos; Dinorah viva participa das conversas 14–16.

## Como jogar os trechos

- `game/out/release/Plaguefall.bin`: campanha normal.
- `game/out/playtest/Plaguefall.bin`: mesma campanha com atalhos de inspeção. C no controle troca a fase durante a preparação; A começa. A+B+C juntos avançam pela saída padrão durante a partida.
- Durante a partida: direcional move; A atira; C seleciona item; B usa item. Válvulas, geradores e cargas usam aproximação e pausa no disparo.
- A seleção direta de um trecho no playtest não simula escolhas narrativas anteriores. A campanha normal grava as três consequências.

## Resultados por fase

Limite de inimigos é o teto de atores ativos. Inclui o chefe/lacaios e os transmissores da fase 8; o enquadramento pode mostrar menos. Os pools de tiros do herói e dos inimigos têm limites próprios. Dinorah dispõe ainda de dois projéteis aliados. FPS abaixo são quadros de simulação por VBlank sob carga preparada na RAM, com os tetos de cada fase.

| Fase | Objetivo | Inimigos | Tiros por lado | FPS NTSC | FPS PAL |
|---|---|---:|---:|---:|---:|
| 1 | Sobreviver 90 s | 4 | 6 | 57.7 | 48.0 |
| 2A | Eliminar 15 insetos | 4 | 6 | 57.8 | 48.0 |
| 2B | Eliminar 15 insetos; entulho sólido | 4 | 6 | 57.9 | 48.0 |
| 3 | Percorrer 2560 px com desvios e cobertura | 4 | 6 | 53.9 | 47.83 |
| 4 | Eliminar 20 insetos | 4 | 6 | 57.7 | 48.0 |
| 5 | Proteger 120 s | 3 | 6 | 51.2 | 46.92 |
| 6A | Escolta 3072 px | 3 | 4 | 57.33 | 47.33 |
| 6B | Escolta 3072 px;2 válvulas e 2 portões | 3 | 4 | 55.67 | 47.33 |
| 7 | Transportar 5 cargas | 4 | 6 | 60.0 | 50.0 |
| 8 | Eliminar 3 prioritários | 6 | 6 | 60.0 | 50.0 |
| 9 | Percorrer 2560 px | 3 | 4 | 60.0 | 50.0 |
| 10 | Destruir 10 ninhos | 4 | 6 | 60.0 | 50.0 |
| 11 | Liberar 3 válvulas | 3 | 6 | 60.0 | 50.0 |
| 12 | Escolta 3072 px; morte permanente deDinorah | 3 | 4 | 57.33 | 47.33 |
| 13A | Eliminar 30;Dinorah protegida | 5 | 6 | 60.0 | 50.0 |
| 13B | Eliminar 45;Dinorah morta | 5 | 6 | 60.0 | 50.0 |
| 14 | Ligar 5 geradores | 4 | 4 | 60.0 | 50.0 |
| 15 | Proteger 120 s | 3 | 4 | 59.0 | 50.0 |
| 16 | Derrotar o chefe | 4 | 4 | 60.0 | 50.0 |

## Verificações

- Dez baterias de emulador aprovadas: cinco grupos em NTSC/PAL na mesma ROM identificada acima.
- Colisões com corpo16×16, limites e sólidos; câmera e atlas; circulação além de2048px; transporte, interação, projéteis, contagens e timers.
- Fase 5: perda do sinal roteia 6B; morte de Dinorah em 6A/6B exige nova tentativa. Fase 12: morte dela roteia 13B; derrota simultânea de Damião tem prioridade.
- Rádio da 15 destruído exige nova tentativa. Ignição dos motores e morte do chefe encerram o fluxo conforme a história.
- Oito percursos, três decisões persistentes e variantes de Dinorah exercitados no códigoC real com ASan/UBSan; 115 falas cabem no painel 26×4.
- `python3 game/tools/check.py` passou, incluindo recursos gerados, áudio, jogador, tiros, regras de morte e regras novas da campanha.

## Dificuldade e desempenho

O galpão, as escoltas e a energia do estaleiro exigem uma rodada humana de ajuste fino. As amostras automáticas incluem derrotas no galpão, nas escoltas paradas e na rua industrial em PAL; esses resultados estão registrados, sem serem tratados como vitórias humanas. Os replays e os JSON registram vida, duração, inimigos e método de preparação de cada tentativa.

As rotas completas das escoltas foram testadas por controle com combate isolado e a6B teve válvulas/portões verificados separadamente. O chefe caiu com disparos reais mantendo sua vida original, mas com saúde inicial ampliada em Damião para isolar o combate. Essas provas validam funcionamento; não afirmam vitória humana em dificuldade normal.

Carga forçada ficou entre 51,2–60 FPS em NTSC e46,92–50FPS em PAL nos tetos configurados. Ensaios acima dos tetos, com 8/16 inimigos nas escoltas, caem mais; não são a população permitida nessas fases. Nenhum teste foi feito em hardware físico.

## Arquivos

- [Painel com capturas, vídeos e resultados](../art/campaign-integrated-v1/review.html)
- [Resumo estruturado](../art/campaign-integrated-v1/summary.json)
- Relatórios por grupo em`art/campaign-integrated-v1/{early,escorts,resistance,factory,launch}/{ntsc,pal}/report.json`.
- [História e impactos](historia/tratamento-proposto.md)

Os relatórios antigos dos grupos permanecem como histórico dos builds isolados. O painel integrado usa somente as medições da ROM final.
