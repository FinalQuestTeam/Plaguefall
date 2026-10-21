# Plaguefall — arte do projeto

**Arte ativa:** [Damião](cangaco-protagonista-iso60-v2/README.md), [13 inimigos em resoluções nativas](cangaco-insects-sized-v3/README.md) e [Nossa Senhora Aparecida](santa-aparecida-v1/README.md), substituindo a antena. Câmera visual elevada a 60° acima do chão. O [inventário completo e pendências](INVENTARIO-SPRITES.md) separa arte integrada e legado. A [parceira feminina](cangaco-parceira-iso60-v1/README.md) tem sprites32×48, oito direções e as mesmas animações de Damião, integrados à galeria Assets. A ROM atual tem896 KiB; os relatórios distinguem orçamento de memória de desempenho de CPU.

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

A [abertura com trilha contínua](audio-abertura-v2/README.md) começa a música no logo Plaguefall e só permite pular com START. A [galeria Assets](gallery-v1/README.md) reúne Damião, Dinorah e quatro músicas. Os [itens atuais](cangaco-itens-v2/README.md) têm sprites16×16 e ícones8×8. A [ROM principal](../out/release/rom.bin) e o [relatório consolidado](../doc/build-validation.json) são as referências atuais; relatórios dentro dos estudos anteriores são históricos.
