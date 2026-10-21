# Mapa regional — integração v1

Quatro paisagens de 320 × 160, redesenhadas a partir do conceito de São Jerônimo. A ROM apresenta comunidade, evacuação, base industrial e ninhos conforme o próximo destino. Conexões e visão geral vêm de `GRAPH`; os caminhos não estão pintados na imagem.

## No jogo

- Ponteiro preenchido persistente: Damião na origem da transição.
- Anéis concêntricos: próximo destino. Só o anel externo varia de brilho; o marcador não desaparece.
- Percorrido: ligação contínua clara. Histórico registra somente transições válidas realmente percorridas; reiniciar uma fase não acrescenta uma ligação.
- À frente: tracejado. Alternativas anteriores não usadas ficam mais discretas.
- Cabeçalho: região, etapa de 1 a 16 e esquema das 20 localidades possíveis.
- Rodapé: nome do destino e duas frases sobre a condição e a consequência da rota, centralizados. Comandos de seguir e pular viagem alinhados à direita. A revisão aprovada está em `../routemap-footer-ux-v1/revisao.html`.
- A ou START: inicia uma viagem de aproximadamente um segundo. Um segundo toque pula a viagem e segue para o diálogo/preparação.
- Ao mudar de região, a origem aparece junto à borda de entrada até Damião viajar.

As quatro bifurcações continuam determinadas por bomba na fase 1, proteção na 5, dano na 9 e tempo na 12. Não foi alterado o grafo nem o balanceamento dessas condições.

## Produção e limites

`source/atlas.png` foi criado com **image_gen integrado**, usando o concept como referência e pedindo marcos maiores e menos textura. O prompt integral está em `source/prompt.txt`. `export_map.py` recorta os quatro painéis, exporta RGB333, seleciona um dos dois bancos por tile e empacota 4bpp. Não substitui tiles por padrões aproximados. As prévias nativas são decodificadas dos próprios bytes empacotados.

Uma região ocupa 800 tiles / 25.600 B de padrões em VRAM. A interface reserva 192 tiles, dos quais no máximo 140 foram usados nos casos validados, e o ponteiro usa 4. A fonte opaca já existente na abertura é compartilhada; não foi duplicada em ROM. A composição usa um buffer estático de uma linha de tiles, 1.280 B, em vez de um framebuffer.

Com a configuração atual do SDK:

| Intervalo | Uso |
|---|---|
| 0–15 | Sistema |
| 16–100 | Elementos fixos do jogo, preservados |
| 101–900 | Arte regional |
| 901–1.092 | Reserva das rotas e indicadores |
| 1.093–1.096 | Ponteiro de 16 × 16 |
| 1.097–1.439 | Margem até a fonte |
| 1.440–1.535 | Fonte SGDK |

A carga ocorre com display apagado. Depois, só o sprite do ponteiro e uma entrada de cor do halo são atualizados. `ROUTEMAP_release()` limpa os planos, restaura paletas, fonte e chão e invalida o cache de inimigos. O estado `ST_MAP` não chama mais `SPRITES_hide()` depois de desenhar o ponteiro.

## Reproduzir e verificar

```sh
python3 game/art/routemap-regional-v1/export_map.py --check
python3 game/tools/check.py
make -C game -j4 release
arch -x86_64 /usr/bin/python3 game/tools/test_routemap_emulator.py
arch -x86_64 /usr/bin/python3 game/tools/test_routemap_emulator.py --pal
```

Os testes do mapa aceleram a entrada na fase de origem e sua conclusão com preparação explícita em RAM. As condições passam pelo `GRAPH_resolve` real. Assim que o mapa aparece, um bloqueio de escrita permite somente controle até a chegada na fase seguinte. Conferem todas as 23 ligações, as oito saídas das bifurcações, arte e fonte na VRAM, preservação dos 85 tiles fixos, ponteiro na SAT, viagem e pulo, além de dois históricos completos de 16 fases, em NTSC e PAL. Isso não equivale a jogar as fases inteiras sem preparação.

Também foi executada a regressão de entrada dos sete cenários integrados (2A–6B) nas duas regiões do console. Não houve teste em hardware físico.

Relatórios e capturas estão em `validation/`. `build-validation.json` registra a ROM correspondente. `mapas-no-jogo.png` reúne capturas reais do Genesis Plus GX. `revisao.html` apresenta as telas e liga a ROM publicada.
