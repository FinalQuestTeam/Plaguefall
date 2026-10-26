# Fase 7 — Feira urbana do Último Chão

[Composição, capturas e ROM](review.html). Esta é a versão ativa da fase 7, substituindo o pátio de terra de `../phase07-spacious-v1`.

A saída dos esgotos agora é marcada por um bueiro aberto, com tampa afastada e escada. O campo tem asfalto, calçadas e muros urbanos, fachadas de comércio e quatro barracas de lona branca. Mantém 768×544 px e 304 px de altura útil. O depósito permanece na barraca esquerda. A quarta fonte foi deslocada para não ficar sob uma das novas barracas; as cinco cargas e o depósito continuam acessíveis.

O bueiro é um marco visual atravessável, sem dano ou nova animação de transição. As regras de abertura, coleta, uma carga por viagem, lentidão de transporte e entrega permanecem as mesmas.

A imagem-base foi criada com ImageGen integrado. [Prompt utilizado](prompts/whole-scene.txt), [imagem-base](source/07-urban-whole.png), [composição nativa com objetivos](complete-with-objectives.png), [fundo nativo](complete-background.png). A composição foi criada inteira primeiro, depois convertida em módulos completos. A montagem efetiva repete fachadas urbanas encostadas e o mesmo sprite de barraca, preservando seus apoios e sombras. A faixa de alvenaria cinza e os vãos que não existiam na imagem-base foram removidos. As fachadas cobrem x0–768 sem lacunas; o recorte preserva as silhuetas completas. A última revisão move apenas a tenda superior 56 px para baixo; fora da união de sua posição antiga e nova, todos os pixels permanecem idênticos. A paleta RGB333 de 16 cores foi adaptada para asfalto cinza e lona branca, mantendo tijolo quente e portas azuis no estilo existente.

Memória: 978 padrões na ROM, no máximo 552 por janela conservadora; cache de 560 e 74 tiles de cargas = **634/640 tiles**, ou 20.288 bytes residentes. Gráficos: 31.296 bytes na ROM; mapa: 13.056 bytes; controle do cache: 6.436 bytes de heap, liberados na pausa. Não há substituição aproximada de padrões no empacotamento.

[layout.json](layout.json) define cidade, colisões, fontes, depósito, barracas e bueiro. [export.py](export.py) gera os padrões, mapa, include de cenário e âncoras da missão. A fase 8 e as salas 13A/13B mantêm seus bancos anteriores e passaram nas regressões compartilhadas.

Testes NTSC/PAL: pixels visíveis de cenário/cargas, rolagem nos dois sentidos e vertical, saída do bueiro por controle, colisões, limites, pausa e cinco entregas reais em combate isolado. Todas as 2.561 posições livres da malha estão conectadas. Carga de quatro inimigos e 6+6 tiros por 20 s em três trechos: 55,1–59,85 FPS NTSC; 49,95–50 PAL. Há quedas sob carga. Defesa natural, limites e evidências estão em [delivery.json](delivery.json).

ROM verificada: `5f443b87a621026298538b705b59051d6cfce2bc71c9904db61c5ac45b5280be`. Hardware físico e dificuldade humana não certificados.

```sh
python3 game/art/phase07-urban-v2/export.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase07_spacious_emulator.py --output /private/tmp/phase07-urban-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase07_spacious_emulator.py --pal --output /private/tmp/phase07-urban-pal
```

O recorte anterior protegia um retângulo de asfalto ao redor da tenda. [stall-silhouette.json](stall-silhouette.json) limita essa proteção à silhueta real, mantendo todos os valores RGB originais. Os pixels transparentes revelam a fachada original. A composição acontece antes da exportação dos tiles; não exige mistura alfa ou sprites extras no jogo. A tenda do topo foi posteriormente deslocada de [600,80] para [600,136], descendo 56 px. Sua colisão agora é [608,176,104,64], recortada pelo limite superior do campo. As outras três tendas, cargas e depósito mantêm suas posições. [Comparação](stall-alpha-review.png).
