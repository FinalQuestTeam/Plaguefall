# Fase 1 — Pátio da igreja (histórico da revisão 1)

**Substituída pela [revisão2 corrigida](../phase01-courtyard-v2/README.md).** Os arquivos e medições abaixo descrevem a versão anterior.

[Abrir revisão visual](revisao.html) · [Vídeo real da ROM](validation/ntsc/fase01.mp4) · [ROM jogável](../../out/release/Plaguefall.bin) · [Distribuição musical e próximas plantas](../../doc/fases-cenarios.md).

Primeira adaptação jogável dos [concept arts](../concepts/fases-v1/README.md). Apenas esta fase recebeu os cenários novos. Os conjuntos das próximas fases serão apresentados antes de sua integração, após a aprovação deste pacote.

## Cena e história ambiental

Mapa 512×256, visto através de uma tela 320×224 com câmera limitada ao mundo. Igreja de cal, portas azuis, telhado cerâmico, muros baixos, banco/barricada, água, bagagens, portões e vegetação periférica. O centro livre mantém inimigos e tiros legíveis. Os objetos sugerem que o lugar acaba de ser abandonado durante a fuga pelo pátio.

A bomba troca apenas o trecho superior esquerdo por igreja parcialmente destruída. O restante do mundo usa os mesmos tiles. A aparência danificada persiste ao pausar e retomar. As pegadas físicas dos volumes impedem passagem de jogador, inimigos e tiros; os detalhes pintados do piso não viram obstáculos.

A meta original de 10 inimigos foi preservada. A evacuação é representada pelo diálogo e pelo cenário, sem NPCs de fuga animados. Sem bomba, a saída segue para 2A com a igreja preservada; com bomba, segue para 2B. As falas de chegada agora mencionam explicitamente o resultado na igreja. A trilha é **Ladainha de Ferro**, com ameaça ajustada ao limite de quatro inimigos desta abertura.

## Arquivos de produção

- `source/intact.png`, `source/damaged.png`: fontes geradas com image_gen a partir do concept do pátio; instruções preservadas em `source/prompts.json`.
- `intact-native.png`, `damaged-native.png`: reprodução da paleta e dos tiles exportados, 512×256.
- `tileset.png`: atlas de 560 tiles 8×8, colunas de 16 tiles.
- `phase01.tmx`, `courtyard.tsx`: cópia para Tiled, com camadas preservada/danificada e objetos de colisão. As camadas são alternativas: mostrar uma por vez.
- `../../res/courtyard/`: dados big endian consumidos pela ROM. O mapa de cada estado ocupa 4096 bytes.
- `../../src/levels/arena.c`: limites, câmera, colisões e posição inicial; a tabela de obstáculos é a fonte das colisões exportadas no TMX.
- `../../tools/pack_courtyard.py`: conversão técnica determinística; quantiza a paleta do hardware, deduplica e seleciona tiles reais da fonte dentro do orçamento. As fontes em alta resolução não entram na ROM.

O TMX é uma cópia para inspeção/edição futura: salvar nele ainda não reimporta mudanças para o jogo. A exportação atual parte das fontes PNG e da tabela de obstáculos em C.

## Orçamento e desempenho

560 tiles compartilhados entre os estados, 17.920 bytes de padrões, uma paleta de 16 cores, dois mapas e uma fonte opaca para o HUD. O cenário fica residente em BG_B; os decalques usam BG_A e rolam junto. O HUD usa WINDOW. A câmera atualiza quatro registradores, sem transferir o mapa a cada quadro. A troca da igreja modifica 26×15 entradas de mapa uma vez por fase, sem carregar outro atlas.

Limites da fase 1: **4 inimigos, 6 projéteis do jogador e 6 inimigos**. Mantêm o leque de até cinco balas e evitam a carga excessiva encontrada na primeira medição. As outras fases conservam seus limites anteriores.

Validação em Genesis Plus GX, executando a ROM real: **60 FPS NTSC / 50 FPS PAL** no combate natural e no teste sustentado com os limites acima preenchidos. O benchmark mede quadros de jogo contra VBlanks, sem confundir velocidade do computador com desempenho do console. Também registra carga além do orçamento: oito inimigos com 32 tiros ainda provocam queda e não são a configuração autorizada desta fase. Os resultados não substituem teste em console físico.

Os testes usam controle real para entrada, movimento, disparo, pausa e bomba. Formações extremas, vida e contador de conclusão são controlados na RAM volátil do emulador, sem alterar a ROM. Conferem câmera 0–192, HUD fixo, obstáculos, projéteis, dano distante, pausa, estado danificado, as duas saídas e retorno às arenas clássicas.

[Relatório NTSC](validation/ntsc/report.json) · [Relatório PAL](validation/pal/report.json) · [Hashes da exportação](export.json).

## Reprodução

Na raiz do repositório:

```sh
python3 game/tools/pack_courtyard.py --check
python3 game/tools/check.py
make -C game -j4
arch -x86_64 /usr/bin/python3 game/tools/test_courtyard_emulator.py --movie
arch -x86_64 /usr/bin/python3 game/tools/test_courtyard_emulator.py --pal
```

O script do emulador usa o core Intel já instalado neste Mac. A imagem original da igreja, sua variante e os recursos das outras fases foram preservados.
