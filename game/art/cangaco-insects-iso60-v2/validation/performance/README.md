> Histórico: a build atual usa [tamanhos nativos e hitboxes alinhadas](../../../cangaco-insects-sized-v3/README.md). Os hashes e números abaixo descrevem as etapas anteriores.

# Investigação de desempenho — 20/10/2026

> Atualização: a ROM em uso agora tem animação reduzida. A tabela principal abaixo descreve a etapa anterior; veja a seção final para os resultados e hash atuais.

O gargalo observado é CPU. O consumo de ROM/RAM/VRAM permanece dentro das reservas auditadas; a checagem prévia de memória e SAT não tinha medido o tempo do laço do jogo.

## Resultado com a lógica completa da arena

| Inimigos | ASCII original | Sprites novos antes | ROM corrigida | CPU antes → depois |
|---:|---:|---:|---:|---:|
| 1 | 60 FPS | 60 FPS | 60 FPS | 88.62% → 54.65% |
| 3 | 60 FPS | 30 FPS | 60 FPS | 119.56% → 64.41% |
| 8 | 60 FPS | 24.25 FPS | 40 FPS | 198.08% → 97.82% |
| 15 | 40 FPS | 16 FPS | 30 FPS | 312.96% → 131.5% |
| 16 | 40 FPS | 15.25 FPS | 30 FPS | 327.17% → 137.33% |

O problema com três inimigos foi reproduzido e corrigido neste teste. **Quinze ainda não recuperaram o desempenho da versão ASCII**: 30 contra 40 FPS com toda a lógica ativa. Não há garantia de quinze a 60 FPS. O custo restante inclui preparação/streaming da animação e montagem dos sprites maiores, somado à lógica existente da arena. Não foi isolado como sendo exclusivamente IA.

## Teste isolado de animação/desenho

A lógica da fase fica congelada, mas coordenadas, direção e animação continuam variando, mantendo o caminho de DMA exercitado.

| Inimigos | Antes | Depois |
|---:|---:|---:|
| 3 | 50 FPS | 60 FPS |
| 8 | 30 FPS | 60 FPS |
| 15 | 20 FPS | 60 FPS |
| 16 | 20 FPS | 60 FPS |

## Causas e mudanças

- A admissão anterior varria até 48 linhas para cada ator e repetia a contagem para suas duas peças. O custo aumentava mesmo em cenas sem excesso de sprites. Agora eventos de início/fim produzem uma única certificação do quadro; a admissão detalhada por prioridade ocorre apenas se o conjunto exceder algum limite. O caminho detalhado conta quatro linhas exatas em cada palavra de 32 bits.
- O módulo de inimigos calculava a fase com `%6` em cada entidade. O GCC gerava uma rotina de divisão de 32 bits por entidade. A fase comum agora é calculada uma vez e combinada com pequenos deslocamentos de fase.
- Movimento, lentidão da lama e animação do protagonista usam DIVS/DIVU onde as faixas numéricas garantem quociente de 16 bits. A normalização preserva o truncamento inteiro anterior.
- A arte, a paleta, as oito direções, os dez quadros canônicos de cada vista e o teto de quatro transferências de inimigos mais uma do protagonista foram preservados.

## Método e limites

Genesis Plus GX libretro instalado na máquina, executado via Rosetta. Medição de 120 VBlanks de aquecimento e 240 por caso. O contador de SPRITES_draw é comparado ao vtimer; o vídeo do emulador a 60 Hz sozinho não conta quadros perdidos pelo jogo. A carga de CPU é a média de oito quadros do SGDK; valores acima de 100% indicam trabalho ultrapassando o intervalo de um quadro.

Cenário controlado: mesma espécie `sq_yellow`, posições espaçadas em três fileiras, movimento contínuo, um retarget de perseguição distribuído por quadro, elementos/itens do primeiro estágio TESTE. HP e posições são restabelecidos na RAM volátil do emulador para manter a amostra comparável. A versão completa executa a lógica da arena; a isolada usa o temporizador de congelamento da fase. O teste não é uma gravação de uma partida natural, nem representa todos os ataques, espécies, sobreposições ou console físico. Mais projéteis, efeitos e sobreposição podem reduzir o desempenho.

A referência ASCII foi compilada do commit c133b29c74e0727878f91db1f7b46197543b73a9 com o mesmo SGDK. A comparação permite ver tanto o ganho da correção quanto a regressão ainda existente em quinze. Os arquivos de experimentos intermediários têm outros hashes e não descrevem a ROM final.

## Verificação técnica

Build limpo aprovado. Testes nativos: 8192 admissões aleatórias contra referência por linha, domínio completo da codificação compacta, 128 quadros aleatórios com certificação/recorte comparados a referência independente, e 600 quadros de estresse com DMA e falha de fila. Mantidos os tetos 80 sprites totais / 20 por linha / 320 pixels por linha; as duas peças de um ator são admitidas ou descartadas juntas. A ROM final passou por 1159 VBlanks com Damião nas oito direções e todos os treze inimigos; esse teste funcional é separado da medição de FPS.

RAM estática: 6008 bytes; heap livre observado: 47490 bytes, maior bloco de 46976 bytes. VRAM e recursos gráficos têm os mesmos tamanhos. ROM: 917504 bytes.

## Reprodução

Na raiz da worktree, após `make -C game -j4`:

```sh
arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-iso60-v2/tests/smoke_emulator.py --benchmark --output game/art/cangaco-insects-iso60-v2/validation/performance/after.json
arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-iso60-v2/tests/smoke_emulator.py --benchmark --gameplay --counts 1,3,8,15,16 --output game/art/cangaco-insects-iso60-v2/validation/performance/gameplay-after.json
```

O script usa o core instalado e os símbolos da própria ROM; `--core`, `--rom` e `--symbols` permitem indicar outros caminhos.

Dados: [antes completo](gameplay-before.json), [depois completo](gameplay-after.json), [ASCII completo](ascii-gameplay.json), [antes isolado](before.json), [depois isolado](after.json), [ASCII isolado](ascii.json).

SHA-256 da etapa anterior, com quatro quadros de repouso e seis de corrida: `fc1f56842be1cb019cfffd25b1a2befe2a6e312b91c0f1e8e1c40fb78861df8a`.

## Atualização: dois quadros de repouso e quatro de corrida

Por solicitação do usuário, foram mantidos quinze inimigos e todas as oito direções, com menos quadros e menos trocas de imagem por segundo. O mesmo tratamento foi aplicado a Damião e aos treze tipos. Seleção das poses existentes: repouso 0/2; corrida 4/6/7/9 (contatos e poses intermediárias dos dois lados). Os PNGs completos e as prévias de seis quadros ficam como matrizes, não representam a cadência reduzida da build atual.

O espelhamento horizontal já reutilizava três vistas: L→O, NE→NO e SE→SO. Um teste de regressão comprova que a troca L/O da mesma pose conserva os tiles e não agenda DMA adicional, tanto no inimigo quanto em Damião. Inverter verticalmente não substitui N/S mantendo a câmera elevada e personagens de pé.

| Medida | Antes da redução | Atual |
|---|---:|---:|
| Quadros canônicos por personagem | 50 | 30 |
| Dados animados de todos os personagens | 537600 B | 322560 B |
| ROM alinhada | 896 KiB | 640 KiB |
| Repouso/corrida por direção | 4 / 6 | 2 / 4 |
| Peças do hardware por ator | 2 | 2 |
| VRAM por ator | 768 B | 768 B |

A economia dos dados animados é de 40% (215040 bytes). Os limites máximos de DMA continuam iguais; a frequência programada de atualização foi reduzida. Em NTSC a 60 quadros de jogo/s, o repouso usa uma troca a cada 24 quadros (2,5 poses/s) e a corrida a cada nove (6,67 poses/s), preservando o período dos ciclos. Com o jogo a 30 FPS, a cadência efetiva cai junto com o laço. Em PAL, os intervalos são 20 e sete quadros. A animação fica menos suave.

Resultados com lógica ativa, mesma metodologia:

| Inimigos | Antes da redução | Atual | Carga de CPU antes → atual |
|---:|---:|---:|---:|
| 3 | 60 FPS | 60 FPS | 64.41% → 63.94% |
| 8 | 40 FPS | 40.5 FPS | 97.82% → 97.22% |
| 15 | 30 FPS | 30 FPS | 131.5% → 129.42% |
| 16 | 30 FPS | 30 FPS | 137.33% → 136.19% |

A redução tem efeito pequeno na CPU e **não corrigiu o caso de quinze inimigos**. A diferença de 40 para 40,5 FPS com oito é pequena e não deve ser tratada como ganho garantido de jogabilidade. O teste isolado de animação/desenho continua em 60 FPS até dezesseis. Para maior recuperação será necessário reduzir o custo de preparação/montagem dos atores maiores e investigar a lógica ativa além da quantidade de poses.

Build limpo, validação dos pixels selecionados e dos ciclos, testes de espelhamento sem DMA, 128 quadros aleatórios, 600 de estresse e 1159 VBlanks no emulador aprovados. Os tamanhos de RAM/VRAM não mudaram. Dados: [jogo completo atual](reduced-gameplay.json), [renderização isolada atual](reduced-render.json), [seleção e hashes dos recursos](../reduced-animation.json).

Configuração: `game/res/actor_animation.json`. Regerar recursos e cabeçalho com `/opt/homebrew/bin/python3 game/tools/pack_actor_animation.py`; adicionar `--check` para verificar sem escrever. Os validadores conferem a correspondência com os pixels de origem. Os recursos `SPRITE` das folhas completas são opcionais e não estão vinculados ao renderizador manual; a partida usa os binários compactados.

SHA-256 da ROM atual: `a9fd09684371ed1df0bc5813a04ac6f10b99f08e9f43aca1040a9c256ef36b40`.
