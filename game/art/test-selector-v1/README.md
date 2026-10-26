# Seleção de testes — campanha completa

No título, abra **FASE TESTE**. Esquerda/direita alternam entre as **18 salas técnicas** e as **19 versões da campanha**. Cima/baixo escolhem; **C** avança nove posições (volta ao início na última página); **A** entra; **B/START** voltam.

A campanha inclui 1, 2A, 2B, 3, 4, 5, 6A, 6B, 7, 8, 9, 10, 11, 12, 13A, 13B, 14, 15 e 16. Usa os cenários, objetivos, inimigos, guia e contagem normais. A entrada direta pula a conversa de chegada e começa com vida cheia/equipamento básico. As variantes 2B, 6B e 13B recebem respectivamente igreja destruída, resgate parcial e morte de Dinorah. Demais entradas diretas usam o estado inicial da campanha.

A pausa das fases abertas por esse seletor oferece **REINICIAR FASE** e **TROCAR FASE**. Trocar inicia um teste novo; cancelar preserva a fase ativa. A progressão após concluir uma fase continua seguindo as regras normais da campanha.

Validação em 24/10/2026, Genesis Plus GX, somente entradas de controle e leitura de memória: todas as 19 entradas, variantes, paginação, cancelamento, reinício, troca de abas, sala técnica 6 e novo jogo normal passaram em [NTSC](validation/ntsc/report.json) e [PAL](validation/pal/report.json). A suíte usa `game/tools/test_training_emulator.py --only-selector` (adicione `--pal` para PAL). Não foi repetido o ensaio completo de carga ou a campanha inteira nesta alteração de menu.

ROM SHA256: `721552d7817e38796d5ab0adb541e83e5266576d329efced40ee8ac402c31eb3`. ROM: 2.359.296 bytes. RAM estática: 19.946 bytes (+4 bytes). Nenhum recurso gráfico novo.

## Verificação na ROM atual

Em 26/10/2026, as 19 entradas, variantes, paginação, reinício, troca e cancelamento passaram novamente na ROM de 2.621.440 bytes, SHA256 `c12217f9f5e8611c625e0a45d7356470f35a936111415ac5a6ce70d1d903f8cf`. Relatórios atuais: [NTSC](../phase45-vertical-v1/validation/selector-ntsc/report.json) e [PAL](../phase45-vertical-v1/validation/selector-pal/report.json). As medições de 24/10 acima são históricas.
