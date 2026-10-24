# Plaguefall — arte do projeto

## Campanha ativa · correção dos corredores v3

A campanha reúne 19 variações em 16 etapas. O padrão separa áreas superior/inferior, limites laterais e elementos do campo; quantidade e posições variam conforme a história e o objetivo. As fontes do guidebook e os módulos existentes definem a direção artística.

A [revisão integrada](campaign-corridors-v3/corrections/delivery-candidate/review.html) mostra os cenários completos, câmeras e ressalvas. O [manifesto ativo](campaign-corridors-v3/active.json) identifica as fontes usadas nos corredores 3, 6A, 6B, 9 e 12. As outras 14 composições permanecem no conjunto `campaign-pattern-v2`.

A ROM `748849ea836635630f8a595634a34c21323fe1bc24df115ff6629f1babac6c77` passou nas dez suítes funcionais NTSC/PAL. Os ensaios dos cinco corredores somaram 18.000 VBlanks sem perdas, com 60 FPS NTSC / 50 FPS PAL nas condições descritas no [aceite técnico](campaign-corridors-v3/corrections/delivery-candidate/acceptance.json). Não houve teste em console físico nem aprovação humana declarada. Os relatórios das versões anteriores são históricos.

**Bornal de recuperação:** [bolsa de couro de cangaceiro aprovada](bolsa-recuperacao-v1/README.md), adaptada a 16×16 na paleta existente e integrada a todas as derrotas, com conteúdo definido pelo equipamento pré-morte e pela etapa da campanha. As oito páginas de ajuda incluem o sprite e as regras por trecho da campanha; capturas reais NTSC/PAL acompanham a validação.

**Diálogos em holodeck:** a [opção C aprovada](dialogue-holodeck-v1/README.md) está integrada: monitor preto, títulos dourados, falas em cinza claro e dois retratos inferiores. Quem escuta fica escurecido, e quem fala conserva a paleta original. [Cores atuais e capturas NTSC/PAL](radio-text-colors-v1/validation/report.json); o pacote original conserva a validação das 51 falas.

**Preparação no rádio:** objetivo, guia e contagem usam o monitor único da opção 1. Dez inimigos menores usam retratos de 32×32 extraídos das mesmas fontes corrigidas de combate, na pose SE de repouso, sem geração de nova arte. O recorte, a redução por vizinho mais próximo e a indexação preservam o desenho original em outra resolução; não se trata de igualdade de pixels com os sprites de 16/24 pixels. O [manifesto de origem](mission-portraits-v3/sources.json) registra fontes, correções, pose, hashes e correspondência com o banco de combate. A paleta, os inimigos maiores e os alvos de treino permanecem; `game/tools/build_mission_portraits.py` empacota os mesmos 7.680 bytes. A única contagem 3/2/1 cobre o carregamento e libera o combate ao terminar. Conversa, objetivo e contagem trocam de conteúdo mantendo a moldura visível, e as páginas do guia reutilizam o fundo. [Comparação da fonte com o retrato](mission-portraits-v3/validation/comparacao-fontes.png), [missão na ROM](mission-portraits-v3/validation/interface-ntsc/prep-1.png) e [validação atual NTSC/PAL](mission-portraits-v3/validation/report.json). A pasta `mission-portraits-v2` conserva a releitura anterior e sua auditoria como histórico.

**Morte dos protagonistas:** [Damião e Dinorah](actor-deaths-v1/README.md) têm quatro poses próprias de queda, integradas à campanha e ao treino. A sequência termina antes de mostrar o resultado.

**Percursos contínuos:** a travessia da fase 4 e a escolta de Dinorah na 6B usam
[composições próprias de 2048 pixels](routes-2048-v2/README.md), com entrada,
equipamentos e saída distintos ao longo do caminho. A arquitetura deixa de
repetir salas completas de 512 pixels; os buracos conservam a faixa de segurança.

**Cenários aprovados e integrados:** [pátio da igreja](phase01-courtyard-v2/README.md), com [revisão visual e vídeo](phase01-courtyard-v2/revisao.html), e [sete telas dos capítulos 2 a 6](phases02-06-v1/revisao.html), incluindo 2A/2B e 6A/6B. A primeira fase foi aprovada em 21/10/2026; os novos conjuntos também receberam aprovação explícita e agora usam mapas próprios na campanha. Os pacotes preservam fontes, módulos, atlas e arquivos Tiled. A lava das fases 3 e 6 recebe brilho por variações dos tiles, mantendo a paleta compartilhada estável. As músicas existentes continuam associadas às fases.

**Validação da integração concluída:** 42 partidas novas, 12 partidas de regressão da fase 1 e 28 ensaios de carga a 60 FPS NTSC / 50 FPS PAL. Relatórios da campanha: [NTSC](phases02-06-v1/validation/ntsc/report.json) e [PAL](phases02-06-v1/validation/pal/report.json). Os relatórios de ROMs temporárias nas pastas individuais registram ensaios anteriores à integração e permanecem como histórico.

**Concept art dos cenários:** [21 pranchas de fases e epílogo](concepts/fases-v1/README.md), com [galeria visual](concepts/fases-v1/galeria.html), estudos de elementos e [guia de narrativa ambiental](concepts/fases-v1/guia-cenarios.md). Referências de pré-produção para as futuras telas, ainda sem integração à ROM.

**Arte ativa:** [Damião](cangaco-protagonista-iso60-v2/README.md), [13 inimigos em resoluções nativas](cangaco-insects-sized-v3/README.md) e [Nossa Senhora Aparecida iso60](santa-iso60-v2/README.md), substituindo a antena. Câmera visual elevada a 60° acima do chão. O [inventário completo e pendências](INVENTARIO-SPRITES.md) separa arte integrada e legado. A [parceira feminina](cangaco-parceira-iso60-v1/README.md) tem sprites32×48, oito direções e as mesmas animações de Damião, integrados à galeria Assets. Na fase 5 e no treino, a Santa do mapa usa colisão e contato de 40×48, invulnerabilidade de 2,5 s, piscar do conjunto inteiro, barra de vida e brilho na coroa. Os demais NPCs conservam a representação legada. Os relatórios distinguem orçamento de memória, ensaios isolados e desempenho da campanha integrada.

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

[Mais um Amanhecer](audio-vitoria-v1/README.md) é o tema aprovado para objetivos
cumpridos e vitória final. [Cinza e Silêncio](audio-game-over-v1/README.md) é
o tema aprovado para a tela de derrota. Ambos tocam uma vez e deixam silêncio
até a confirmação do jogador.

A [abertura com trilha contínua](audio-abertura-v3/README.md) começa a música no logo Plaguefall e só permite pular com START. A [galeria Assets](gallery-v1/README.md) reúne Damião, Dinorah e quatro músicas. Os [itens atuais](cangaco-itens-v2/README.md) têm sprites16×16 e ícones8×8. A [ROM principal](../out/release/Plaguefall.bin) e o [relatório consolidado](../doc/build-validation.json) são as referências atuais; relatórios dentro dos estudos anteriores são históricos.

## Objetivos das missões experimentais

[objective-sprites-v1](objective-sprites-v1/README.md) reúne dez folhas próprias e 60 quadros, fontes ImageGen, prompts, exportação para a paleta existente, prévia animada e testes NTSC/PAL. A integração fica nas salas 11–18: energia pulsante, sacolas coletáveis, Dinorah no corredor e câmara de contenção.
