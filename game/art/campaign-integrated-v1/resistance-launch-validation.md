# Resistência e estaleiro — validação integrada

ROM final: `bb9955bf90a25dab36aa280281909f5d08d98a0d9b313d8508849d68aa382a16`. Quatro execuções completas, todas com código de saída 0 e `passed:true`. Nenhuma alteração no código da ROM durante os testes.

| Fase | Cap de inimigos | Tiros por lado | Carga NTSC | Carga PAL |
|---|---:|---:|---:|---:|
|7|4|6/6|60.0|50.0|
|8|6|6/6|60.0|50.0|
|13A|5|6/6|60.0|50.0|
|13B|5|6/6|60.0|50.0|
|14|4|4/4|60.0|50.0|
|15|3|4/4|59.0|49.2|
|16|4|4/4|60.0|50.0|

FPS representa atualizações lógicas por VBlank. O rádio manteve59/49,2 FPS na carga artificial; não foi classificado como60/50 estritos. A prova reinsere os inimigos no cap configurado e ocupa ambos os pools de tiros. CPU pico máximo:61,57% NTSC e36,38% PAL.

Passaram a abertura, coleta e entrega das cinco cargas por controles; três prioridades; limites 30/45 da sala; cinco geradores; duração real do rádio, falha com reinício e vitória; ignição com atlas inteiro correto; nascimento e dano real do chefe. Os testes de combate do chefe elevam apenas a saúde inicial do herói para isolar o dano; não alteram a vida do chefe.

As quatro bordas de cada arena e todas as suas barricadas/bancos/plataformas foram pressionadas por controles a partir de posições preparadas. O atlas, os atributos H/V e os pixels dos objetos foram comparados com a VRAM. Após caminhadas reais até câmera [448,160] na favela e [192,160] no estaleiro, os dados permaneceram exatos, sem lixo de BG_A fora dos objetos e com paleta estável.

A mudança completa para os motores em chamas passou pela mesma comparação. Rádio: 120,13 s NTSC e 119,98 s PAL a partir da amostra inicial. Escorpião derrotado com tiros reais em 23,73/23,42 s no teste isolado.

Amostras de dificuldade usam 20 s (resistência) ou 25 s (estaleiro) de movimentos/disparos automáticos, sem alteração de RAM durante a tentativa e com 100 HP iniciais. Elas registram dano e pressão; não constituem vitória humana nas fases completas. As derrotas e a vida restante estão preservadas nos relatórios JSON.

Vídeos e capturas foram inspecionados em movimento: fachadas da favela, sala do sindicato, guichê com Dinorah e motores/radio permanecem coerentes nos quadros examinados. A prova de pixels cobre também áreas da câmera atravessadas nos testes isolados.

[Resistência: vídeos e relatórios](resistance/review.html) · [Estaleiro: vídeos e relatórios](launch/review.html)
