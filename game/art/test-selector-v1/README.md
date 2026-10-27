# Seleção de testes — campanha completa

No título, abra **FASE TESTE**. Esquerda/direita alternam entre as **19 versões da campanha** e os **oito finais**. Cima/baixo escolhem; **C** avança nove posições nas fases (volta ao início na última página); **A** entra ou reproduz; **B/START** voltam. As salas técnicas permanecem fora do seletor.

Na aba **FINAIS DA CAMPANHA**, a tabela mostra igreja, população e Dinorah para cada combinação. A prévia usa os mesmos slides, música e partículas da campanha e retorna ao mesmo final selecionado, inclusive ao pular com START. Depois de assistir, B/START no seletor retornam ao título. [Vídeos e validação das oito prévias](../ending-slides-v1/README.md). A regressão das 19 fases, paginação, reinício e cancelamento passou em [NTSC](../ending-slides-v1/validation/phases-ntsc/report.json) e [PAL](../ending-slides-v1/validation/phases-pal/report.json).

A campanha inclui 1, 2A, 2B, 3, 4, 5, 6A, 6B, 7, 8, 9, 10, 11, 12, 13A, 13B, 14, 15 e 16. Usa os cenários, objetivos, inimigos, guia e contagem normais. A entrada direta pula a conversa de chegada e começa com vida cheia/equipamento básico. As variantes 2B, 6B e 13B recebem respectivamente igreja destruída, resgate parcial e morte de Dinorah. Demais entradas diretas usam o estado inicial da campanha.

A pausa das fases abertas por esse seletor oferece **REINICIAR FASE** e **TROCAR FASE**. Trocar inicia um teste novo; cancelar preserva a fase ativa. A progressão após concluir uma fase continua seguindo as regras normais da campanha.

Validação histórica em 24/10/2026, Genesis Plus GX, somente entradas de controle e leitura de memória: todas as 19 entradas, variantes, paginação, cancelamento, reinício, troca de abas, sala técnica 6 e novo jogo normal passaram em [NTSC](validation/ntsc/report.json) e [PAL](validation/pal/report.json). A suíte usa `game/tools/test_training_emulator.py --only-selector` (adicione `--pal` para PAL). Não foi repetido o ensaio completo de carga ou a campanha inteira nesta alteração de menu.

ROM SHA256: `721552d7817e38796d5ab0adb541e83e5266576d329efced40ee8ac402c31eb3`. ROM: 2.359.296 bytes. RAM estática: 19.946 bytes (+4 bytes). Nenhum recurso gráfico novo.

## Verificação anterior

Em 26/10/2026, as 19 entradas, variantes, paginação, reinício, troca e cancelamento passaram novamente na ROM de 2.621.440 bytes, SHA256 `c12217f9f5e8611c625e0a45d7356470f35a936111415ac5a6ce70d1d903f8cf`. Relatórios atuais: [NTSC](../phase45-vertical-v1/validation/selector-ntsc/report.json) e [PAL](../phase45-vertical-v1/validation/selector-pal/report.json). As medições de 24/10 acima são históricas.

## Seletor somente da campanha — 27/10/2026

As 18 salas técnicas foram retiradas. O seletor abre diretamente nas 19 versões da campanha; esquerda/direita não abrem outras abas. Entrada nas 19 fases, variantes, paginação, cancelamento com B/START, reinício e troca pela pausa passaram em NTSC e PAL, somente com entradas de controle e leitura de memória.

ROM SHA256: `2a27766c1e7704511b2178acdebc3ea8f2e75d1df9ca3f122fe2fafbab80ae5a`. ROM: 2752512 bytes. Verificação: `arch -x86_64 /usr/bin/python3 game/tools/test_training_emulator.py --only-selector` (adicione `--pal` para PAL).
