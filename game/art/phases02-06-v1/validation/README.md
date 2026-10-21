# Verificação da campanha integrada

Comando: `arch -x86_64 /usr/bin/python3 game/tools/test_campaign_stages_emulator.py --matches 3 --movie`, repetido com `--pal`.

O harness carrega `game/out/release/rom.bin` e os símbolos do mesmo build. Não cria nem compila ROM alternativa. O cabeçalho da cópia em memória pode selecionar PAL; a ROM em disco permanece intacta. O hash original e o hash efetivamente carregado constam do relatório.

A entrada inicial na fase 1 usa somente joypad. Para preparar cada nó, o teste acelera a contagem de eliminações da fase 1 e seleciona `pendingLevel` no fluxo de mapa/preparação. O motor real carrega o nível, seus recursos, inimigos, música, objetivo e contagem regressiva. Esse estado inicial é salvo. Todas as tentativas ordinárias restauram esse baseline e ativam uma trava que proíbe qualquer escrita de RAM pelo harness: somente o joypad é enviado. HP, IA, cadência, drops e inventário usam as regras da ROM. O bot não representa a habilidade ou experiência de uma pessoa; vitórias e derrotas são registradas sem mudar dificuldade para obter resultados favoráveis.

Os probes isolados são explicitamente separados das partidas: preparam posição/cooldown/formações para conferir paredes, tiros verticais, rotas secas, dano e reset da lava, lama, pausa, HUD/fonte e upload do atlas. O teste de sucesso do objetivo 5 suprime spawns; o de falha mantém um inimigo em contato com o NPC, sem escrever HP, invulnerabilidade, temporizador do objetivo ou estatísticas do grafo. O pedestal é verificado por movimento real. A saída 6B→7 (nó 8→9) acelera apenas o contador de mortes.

O stress mantém quatro inimigos e seis tiros em cada pool, vida e contagem controladas em RAM, e move a câmera gradualmente em cada eixo. Ele compara `phaseStats.frames` com `vtimer` durante 300 VBlanks após aquecimento de 90 quadros. A velocidade de execução no computador não é FPS do jogo. `cpuFrameLoad / 2048 * 100` é a métrica SGDK, resumida como média e percentil 95.

Os vídeos de brilho registram quatro segundos da ROM final com os inimigos isolados. Os probes conferem que somente o intervalo privado de tiles da lava muda, que apenas os pixels de destaque previstos mudam de índice e que as paletas permanecem estáveis. Isso não equivale a uma avaliação humana da qualidade sonora; áudio possui verificação separada.

Resultados e capturas ficam em `ntsc/` e `pal/`. `report.json` informa falhas concretas, resultados de cada tentativa, danos, curas, caps observados e métricas do stress. Capturas `FAIL-*` pertencem a verificações com falha e podem registrar problemas do próprio harness durante seu desenvolvimento; o relatório final é a referência de execução atual.
