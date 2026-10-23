# Avaliação de código estrutura e documentação de Plaguefall

A arquitetura permite evolução incremental. A divisão entre atores, inimigos, fases, objetivos, áudio e vídeo é adequada ao projeto. O maior custo atual vem de integração incompleta e evidências distribuídas. Não há motivo demonstrado para reescrever o jogo.

Esta análise foi de leitura do checkout em edição. O QA observou uma falha inicial de compilação e depois confirmou que uma atualização concomitante dos fontes compila e liga em cópia isolada. A primeira falha está preservada como histórico de integração, não como pendência atual.

## Forças

O `main.c` delega o fluxo, as definições de fases concentram conteúdo e o grafo concentra condições de rota. Pools fixos, orçamentos de DMA e verificações de sprites/VRAM respeitam o hardware. Painéis preservam o estado visual, e testes nativos usam código de produção com sanitizadores. As pastas de arte preservam fontes, exports e histórico de aprovação.

## Achados

1. **P1 — Falta fechar a validação da integração do sandbox.** O primeiro snapshot ainda chamava `TEST_draw()` e `TEST_update()`, ausentes da API nova, e falhou na compilação. Uma atualização concomitante passou a usar as APIs novas e a segunda compilação isolada gerou `rom.out` com sucesso. Porém, a suite nova de treinamento não passou em nenhuma das regiões. Diagnosticar suas asserções, validar pausa/configuração/objetivos e ligar os resultados à nova ROM. Evidências: [build inicial](evidencias/build.log), [build posterior](evidencias/build-final.log) e [QA](04-qa.md).

2. **P1 — O consolidado identifica outra ROM.** `build-validation.json` registra 1.310.720 bytes e hash `3bfa4cbd…`; a ROM disponível tem 1.441.792 bytes e hash `1928321f…`, coerente com seu JSON de empacotamento. Gerar um consolidado ligado ao artefato realmente testado, incluindo revisão dos fontes e resultados das suites. Preservar o anterior como histórico. Evidência: [manifesto anterior](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/doc/build-validation.json:7).

3. **P2 — A conferência central pode passar com o build quebrado.** `check.py` cobre exports, mira e áudio, mas não compila o jogo nem reúne empacotamento, cenários e teste de contato. Isso ocorreu nesta avaliação. Manter checks rápidos, mas oferecer um comando documentado de revisão completa que compile, valide recursos e identifique o pacote. Evidência: [check.py](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/tools/check.py:15).

4. **P2 — Há infraestrutura repetida e caminhos locais rígidos nos testes.** Callbacks libretro, controles, símbolos, PNG e leitura de RAM/VRAM se repetem. Núcleo e `m68k-elf-nm` usam caminhos do ambiente macOS atual. Extrair o adaptador comum e parametrizar dependências melhoraria reprodução sem misturar os cenários das suites. Evidências: [núcleo](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/tools/test_campaign_stages_emulator.py:10), [infraestrutura de interface](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/tools/test_interface_emulator.py:12).

5. **P2 — Os tiros inimigos deslocam valores negativos à esquerda.** `dx` e `dy` podem ser negativos em expressões com `<< 6`. Esse caso é comportamento indefinido em C. Substituir por multiplicação em tipo adequado e exercitar os quatro quadrantes com UBSan é uma correção localizada. É um risco de linguagem confirmado por leitura, sem falha visual demonstrada na ROM. Evidências: [tiro direcionado](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/actors/shots_enemy.c:37), [leque](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/actors/shots_enemy.c:49).

6. **P3 — A documentação de build diverge.** `BUILD-WORKTREE.md` ainda chama `rom.bin` de principal e omite `OUT_DIR_LIB`, enquanto README e desenvolvimento adotam o pacote `Plaguefall.bin`. O guia descreve um SDK já preparado, sem cobrir integralmente essa preparação em clone limpo. Centralizar a instrução canônica e deixar no guia de worktrees apenas suas diferenças. Evidências: [worktrees](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/BUILD-WORKTREE.md:11), [desenvolvimento](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/doc/desenvolvimento.md:13).

## Organização recomendada

Manter `src/`, `res/`, `art/`, `doc/`, `tools/` e `tests/`. Criar um índice curto para recursos ativos, ligando fonte, exportador, `.res`, consumidor no runtime e teste. Marcar estudos como ativos, históricos ou propostas. A documentação narrativa também precisa acompanhar o roteiro executável: a fase 7 atual usa padre e Damião, enquanto o texto histórico ainda descreve participação incondicional de Dinorah. Ver [roteiro](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/levels/story.c:89) e [documentação](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/doc/historia/README.md:22).

## Escolha recomendada

Fechar a validação da integração, tratar o cálculo dos projéteis e publicar evidências coerentes com a ROM. Depois validar a reprodução em clone limpo e compartilhar apenas a infraestrutura realmente comum das suites. A expansão de conteúdo pode aproveitar as estruturas atuais.
