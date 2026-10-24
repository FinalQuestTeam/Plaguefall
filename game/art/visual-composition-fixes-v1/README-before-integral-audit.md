# Correções de composição visual

Na reavaliação solicitada pelo usuário, a fase 3 foi reprovada por cortes nas casas e sua aceitação anterior foi retirada. Permanecem 12 das 13 variações aceitáveis. [Evidências dos cortes](../phase03-clipping-review-v1/evidence.png) e [parecer atualizado](../phase03-clipping-review-v1/report.json). Os grupos trabalharam em paralelo, com críticas cruzadas e no máximo três ciclos por fase. A avaliação usa imagens completas, mapas nativos reconstruídos e enquadramentos reais do emulador; testes técnicos não substituem o julgamento visual.

[Comparação, fontes e playtests](review.html) · [Pareceres por fase](report.json) · [Visão geral das capturas finais](final-contact.png) · [Auditoria anterior](../visual-composition-audit-v1/review.html)

| Variações | Ciclos | Resultado principal |
|---|---:|---|
| 3 | 3 | **Reprovada na reavaliação:** fragmentos de casas e emendas entre telhado/fachada; aprovação retirada |
| 4 | 2 | Materiais consistentes, recortes sem halos, racks e fechamento sul visíveis durante movimento |
| 6A / 6B / 12 | até 3 | Piso calmo, marcos de progressão, portões com folha e válvulas conectadas; chegada sindical distinta |
| 7 / 8 | 1 | Depósito coberto, cargas claras e emissores roxos com sinal ciano ativo |
| 9 / 10 / 11 | 2 | Três setores industriais, quatro barreiras reais, ovos claros e tubulação ligada às válvulas |
| 13B | 2 | Memorial com retrato, faixa de luto e velas; entrada diante do guichê |
| 14 / 15 | 2 | Gabinetes legíveis, circuito contínuo, estação de rádio e apresentação dos motores |

As composições de 1, 2A, 2B e 5 foram preservadas pelos hashes dos recursos. Os pixels RGB de 13A e 16 permanecem idênticos ao ponto de partida. A ignição de 15 usa um cenário próprio, preservando a arena já aceita do chefe. A história e as três consequências persistentes continuam produzindo os oito percursos; Dinorah viva mantém suas conversas finais.

## Verificação final

ROM de produção: `ea9caca81c9baa64cd07d011f7b8ae234cb883b50a81c791fdcea179f23a558f`, 2.490.368 bytes. Dez baterias completas passaram na mesma ROM: cinco grupos, cada um em NTSC e PAL. Incluem colisões, tetos de inimigos/tiros, rolagem, bytes da arte na VRAM, poses, estados e conclusão dos objetivos. Os relatórios estão em [campaign-integrated-v1](../campaign-integrated-v1/review.html).

Os recursos gerados e testes nativos de `game/tools/check.py` passaram. Depois do último ajuste no perímetro da fase 4, sua geometria foi revalidada e as dez baterias de emulador foram repetidas. A apresentação de ignição pausa IA, dano, projéteis e contador, devolvendo a câmera antes da defesa continuar.

Na carga máxima configurada, as fases corrigidas registraram **53,9–60 FPS em NTSC** e **47,33–50 FPS em PAL**. Os tetos variam de três a seis inimigos ativos, com quatro ou seis tiros por pool; o detalhamento está no painel técnico. A fase 5 preservada registra 51,2/46,92 FPS no mesmo ensaio. Nenhum teste foi realizado em console físico.

As travessias completas das escoltas foram verificadas com combate isolado. Amostras de combate incluem derrotas, especialmente na 12; não representam vitória humana em dificuldade normal. A revisão visual está aceitável, mas uma campanha humana completa ainda é necessária para calibrar dificuldade. Peças arquitetônicas se repetem nos panoramas para respeitar o orçamento de 640 tiles; a maior combinação atual ocupa 639.

## Jogar e reproduzir

- [ROM de playtest](../../out/playtest/Plaguefall.bin): C escolhe a fase na preparação; A começa. A+B+C avança durante a partida.
- [ROM da campanha](../../out/release/Plaguefall.bin): fluxo narrativo normal. Direcional move, A atira, C escolhe item e B usa item. Aproximar e soltar A opera equipamentos.
- `python3 game/tools/test_campaign_emulator_suite.py --movie` repete as dez baterias contra `game/out/release`.
- `python3 game/art/visual-composition-fixes-v1/build_review.py` publica o painel a partir dos pareceres salvos; não gera aprovação automática.

## Produção das imagens

As novas imagens foram feitas com o **ImageGen integrado**. Primeiro foi criada ou editada a cena inteira, depois foram extraídas peças arquitetônicas, materiais e elementos para compor os mapas. A redução inicial da fonte pode usar LANCZOS; a escolha de cores RGB333 e o reaproveitamento de tiles são exatos, sem troca por padrões parecidos. O índice zero da paleta de cenário permanece preto.

[Prompts do galpão e memorial](authored-scenes-prompts.json) · [Prompts dos objetivos](objectives/prompts.json) · [Atlas final dos objetivos](objectives/final-atlas.png). Os grupos mantêm suas fontes e prompts nos subdiretórios de ciclos e nos diretórios canônicos em `campaign-whole-scenes-v1`.

As práticas compartilhadas foram: piso discreto; arquitetura visível nos extremos da câmera; grandes massas de cor nos objetivos; recortes sem chão residual; tubulações ligadas aos mecanismos; estados de funcionamento semanticamente corretos; e verificação no jogo antes de aceitar uma composição.
