# Painel de campanha integrado

Arte aprovada em `source/painel-nativo.png`, exportada por `exportar.py`. `conteudo-aprovado.json` preserva os textos e coordenadas aprovados. O fundo usa 545 tiles únicos e 15 cores RGB333. Fonte transparente e ícones permanecem separados da arte.

## Comportamento

- Preparação: nome do lugar, etapa, objetivo real, perigo, dica nas quatro bifurcações e inimigos; chefe identificado explicitamente.
- Pause: progresso real de mortes/tempo/sinal/chefe, vida, bombas e item ou tiro ativo. A escolhe, B/START retomam. A ajuda volta ao pause. Sair exige confirmação, inicialmente em continuar jogando.
- Ajuda: seis páginas. A ou direita avança; esquerda volta; B/START retorna à origem.
- Diálogo: um retrato e caixa fixos, nome do padre, contador de falas, legenda para mostrar texto/avançar/ver missão e START para pular. Todas as 51 falas cabem em quatro linhas de 34 colunas.
- DEV_SHORTCUTS é necessário para C trocar preparação e A+B+C pular fase. Desativado na ROM normal. A contagem inicial de três segundos foi mantida.

## Preservação da partida

`panel.c` empresta os tiles 101–757, mapas A/B, fonte, paletas e deslocamentos. Guarda 32.288 bytes temporários, mantendo os tiles fixos e o plano WINDOW. Antes do empréstimo, aplica DMA já pendente. Ao sair, restaura os bytes e libera a memória sem reiniciar fase, ator ou cache. A ajuda dentro do pause reutiliza o mesmo empréstimo. Timers de objetivos, atores, itens e flash não avançam dentro do pause/guia.

## Validação

`validation/ntsc` e `validation/pal`: vinte localidades, seis páginas, entrada/retorno do guia, cancelamento e confirmação de saída, B e START para retomar, simulação congelada e comparação de VRAM na restauração. A seleção de fases/morte é acelerada por RAM de forma explícita; a navegação da interface roda somente com controles sob bloqueio de escrita. DMA de atores/cenário já solicitado é aplicado antes da fotografia estável da VRAM.

`validation/map-ntsc` e `validation/map-pal`: 23 ligações e duas campanhas completas por sistema. Testes nativos de áudio, mira e recursos passaram. Não houve teste em console físico ou CRT.

Reproduzir: `python3 game/art/interface-ux-v2/exportar.py --check`, `make -C game -j4 release`, `arch -x86_64 /usr/bin/python3 game/tools/test_interface_emulator.py [--pal]`. A galeria é gerada por `integracao/galeria.py`.
