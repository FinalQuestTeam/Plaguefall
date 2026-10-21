# Plaguefall — arte do projeto

**Cenários aprovados e integrados:** [pátio da igreja](phase01-courtyard-v2/README.md), com [revisão visual e vídeo](phase01-courtyard-v2/revisao.html), e [sete telas dos capítulos 2 a 6](phases02-06-v1/revisao.html), incluindo 2A/2B e 6A/6B. A primeira fase foi aprovada em 21/10/2026; os novos conjuntos também receberam aprovação explícita e agora usam mapas próprios na campanha. Os pacotes preservam fontes, módulos, atlas e arquivos Tiled. A lava das fases 3 e 6 recebe brilho por variações dos tiles, mantendo a paleta compartilhada estável. As músicas existentes continuam associadas às fases.

**Validação da integração concluída:** 42 partidas novas, 12 partidas de regressão da fase 1 e 28 ensaios de carga a 60 FPS NTSC / 50 FPS PAL. Relatórios da campanha: [NTSC](phases02-06-v1/validation/ntsc/report.json) e [PAL](phases02-06-v1/validation/pal/report.json). Os relatórios de ROMs temporárias nas pastas individuais registram ensaios anteriores à integração e permanecem como histórico.

**Concept art dos cenários:** [21 pranchas de fases e epílogo](concepts/fases-v1/README.md), com [galeria visual](concepts/fases-v1/galeria.html), estudos de elementos e [guia de narrativa ambiental](concepts/fases-v1/guia-cenarios.md). Referências de pré-produção para as futuras telas, ainda sem integração à ROM.

**Arte ativa:** [Damião](cangaco-protagonista-iso60-v2/README.md), [13 inimigos em resoluções nativas](cangaco-insects-sized-v3/README.md) e [Nossa Senhora Aparecida](santa-aparecida-v1/README.md), substituindo a antena. Câmera visual elevada a 60° acima do chão. O [inventário completo e pendências](INVENTARIO-SPRITES.md) separa arte integrada e legado. A [parceira feminina](cangaco-parceira-iso60-v1/README.md) tem sprites32×48, oito direções e as mesmas animações de Damião, integrados à galeria Assets. Na fase 5, a Santa do mapa usa área lógica de 40×40 e invulnerabilidade de 2,5 s; um sinal de 8×8 substitui a duplicação do sprite sobre o cenário. Os demais NPCs conservam a representação legada. Os relatórios distinguem orçamento de memória, ensaios isolados e desempenho da campanha integrada.

## Direção atual: cangaço cyberpunk brasileiro

A direção visual parte do concept do
[protagonista humano](concepts/protagonista/README.md): implantes cibernéticos,
proteções feitas de pedaços de armadura sobre tecido, tecnologia incorporada,
chapéu metálico com sensores/comunicação e arma de fogo. O rosto fica exposto,
sem óculos ou visor. O [protagonista Damião já possui sprites](cangaco-protagonista-iso60-v2/README.md) e substitui o mech na partida e na abertura da galeria de personagens.

Os [concepts atuais dos inimigos gigantes](concepts/inimigos/README.md) apresentam
serra-pau (sq), mutuca (tri), saúva-soldado (pen) e escorpião (boss), com doze
variantes comuns e um chefe. As pranchas mantêm os IDs e nomes existentes para
rastreabilidade. Os [sprites atuais derivados desses concepts](cangaco-insects-sized-v3/README.md)
já foram integrados à ROM, com oito direções, animações e auditoria de memória.

## Estudos anteriores


O pacote existente de inimigos da direção anterior, com robôs e armaduras, está em
[darkspace-8dir-v3/enemies](darkspace-8dir-v3/README.md), organizado pelos
identificadores de `game/src/enemies/defs/`: `sq_*`, `tri_*`, `pen_*`, `dummy`,
`target` e `boss`.

Cada pasta reúne o inimigo nas oito direções do jogo. Consulte o
[catálogo de nomes e índices](darkspace-8dir-v3/catalog.json) ou as
[declarações SGDK](darkspace-8dir-v3/enemies.res).

`darkspace-v1` e `darkspace-iso60-v2` são versões anteriores da arte.

## Áudio e apresentação

A [abertura com trilha contínua](audio-abertura-v3/README.md) começa a música no logo Plaguefall e só permite pular com START. A [galeria Assets](gallery-v1/README.md) reúne Damião, Dinorah e quatro músicas. Os [itens atuais](cangaco-itens-v2/README.md) têm sprites16×16 e ícones8×8. A [ROM principal](../out/release/Plaguefall.bin) e o [relatório consolidado](../doc/build-validation.json) são as referências atuais; relatórios dentro dos estudos anteriores são históricos.
