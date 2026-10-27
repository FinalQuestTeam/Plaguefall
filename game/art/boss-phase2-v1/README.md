# Escorpião — segunda fase integrada

[Revisão visual](review.html) · [ROM e validação](delivery.json) · [Código do chefe](../../src/enemies/enemy_boss.c).

Aos **12 de vida ou menos**, o chefe entra uma única vez na segunda fase. Ele para por **0,8 segundo**, brilha alternadamente usando somente a paleta do próprio sprite e emite um sinal sonoro. A mudança permanece registrada até morte/reinício. A primeira fase mantém sua alternância de quatro segundos e sua blindagem de três segundos a cada quinze.

Na segunda fase, o ciclo é: aproximação de **0,6 s** → aviso de **~0,35 s** → investida de **0,5 s** → novo aviso de **~0,35 s**, mirando novamente → segunda investida de **0,5 s** → recuperação parada de **1,2 s** → recuo e leques por **3 s**. A direção fica travada durante cada aviso e sua respectiva investida. Durante a recuperação não há movimento nem disparos; tiros reais causam dano normalmente. Contato com Damião e separação dos lacaios não cancelam a janela.

A blindagem periódica desaparece na segunda fase. Os disparos alternam um leque aberto e outro fechado, com cinco balas e dano 13. A cadência continua em cerca de 1,2 s após cada rajada. O chefe aguarda cinco vagas livres e só avança a alternância quando consegue disparar. Os limites permanecem em dez tiros inimigos e quatro do jogador.

As invocações, a cada dez segundos, preenchem vagas até **dois Caçadores vivos**; não acumulam um terceiro. A fase 16 admite o chefe e dois lacaios. São usados os sprites atuais de 48×48, suas oito direções e animações existentes. O recuo mantém o chefe encarando Damião; os avisos preservam a direção travada. Nenhuma reserva adicional de tiles ou campos novos na estrutura `Enemy`.

Pausa congela estado e temporizadores. Derrota/reinício restaura os 25 de vida e a primeira fase. O ensaio completo por controle atravessa a mudança de fase e derrota o chefe com seus 25 pontos de vida originais.

```sh
python3 game/tools/test_boss_phase2.py
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_boss_phase2_emulator.py --output game/art/boss-phase2-v1/validation/mechanics-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_boss_phase2_emulator.py --pal --output game/art/boss-phase2-v1/validation/mechanics-pal
arch -x86_64 /usr/bin/python3 game/tools/test_phase16_shipyard_emulator.py --output game/art/boss-phase2-v1/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase16_shipyard_emulator.py --pal --output game/art/boss-phase2-v1/validation/pal
python3 game/art/boss-phase2-v1/build_review.py
```

Os testes nativos executam a IA de produção com ASan/UBSan em 50/60 Hz. No Genesis Plus GX, os ensaios isolados usam RAM para preparar posições, tempo e ocupação dos pools; acertos, dano, movimento e ataques passam pelo código de produção. O ensaio de carga eleva uma vez a vida do jogador e, após registrar a segunda fase, a do chefe para 200, permitindo 30 s de observação por controle sem novas escritas de RAM. O ensaio de vitória mantém os 25 de vida originais do chefe e protege o jogador uma vez. FPS, sprites e cache estão no relatório; hardware físico e dificuldade humana não certificados.
