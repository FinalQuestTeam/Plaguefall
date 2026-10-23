# Resultados: proposta aprovada e integração

`proposta-aprovada.html` e `conteudo-aprovado.json` preservam a revisão aprovada: texto centralizado e caixas de 256 px, com alturas de 184/152/128/176 px para derrota, confirmação, objetivo e final. `revisao.html` compara esses desenhos com capturas da ROM atual em NTSC e PAL.

O módulo `src/system/video/screens/result.c` compõe a moldura existente e a fonte SGDK em tamanho original. Antes de mostrar a caixa, esconde sprites/HUD, compacta os padrões referenciados do cenário e mantém suas paletas; PAL2 fica disponível para a caixa. Os buffers de captura são liberados antes de alocar o cartão. Ao sair, os tiles dos objetos/pisos são regenerados e o cache de atores é invalidado. Não se retoma simulação a partir de uma tela de resultado. Decais transitórios de sangue são ocultos junto com os atores nas arenas com câmera.

A morte tem prioridade sobre cumprir a meta no mesmo quadro. A vitória final segue o diálogo existente e reconstrói somente o covil vazio, sem respawn. Repetir mantém a fase; uma campanha nova limpa equipamentos, rotas, cenas e estatísticas. START repete na derrota e cancela dentro da confirmação; A confirma a seleção. O tiro mantido não descarta o cartão; exige uma nova pressão após 350 ms. Conclusões avançam em 2 s e a perda do sinal em 3 s; a vitória final aguarda a escolha.

A ROM foi validada em Genesis Plus GX, sem ensaio em hardware físico/CRT. Os testes usam RAM para preparar cenários e antecipar contadores, morte e chefe; não são batalhas vencidas naturalmente. A navegação e as transições são do código de produção. Relatórios em `integracao/validation/` pertencem ao hash registrado em cada JSON.

```sh
python3 game/art/resultados-ux-v1/exportar.py --check
arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py
arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py --pal
python3 game/art/resultados-ux-v1/publicar_revisao.py
```

`capturar.py` documenta a captura histórica anterior à implementação. `propor.py` recompõe o desenho aprovado, sem exportar recursos do jogo. A publicação das capturas ocorre separadamente em `publicar_revisao.py`.
