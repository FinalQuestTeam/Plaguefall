# Avaliação de Plaguefall para decidir os próximos passos

Avaliação de 22 de outubro de 2026 pelas perspectivas de game design, UX, desenvolvimento, QA e jogador casual. A identidade do jogo e a base técnica justificam continuar. O melhor próximo investimento é fechar a integração atual e melhorar a experiência de aprender, compreender o combate e tentar novamente.

As avaliações especializadas foram delegadas em paralelo; o QA executou verificações da ROM e uma compilação isolada dos fontes. A perspectiva casual é uma avaliação heurística, sem participação de jogadores humanos. Diversão, frustração e dificuldade percebida continuam sendo hipóteses de playtest.

## Relatórios

| Perspectiva | Conclusão principal | Relatório |
|---|---|---|
| Game design | Suavizar a transição 6–7 e rever a recuperação após derrota antes de expandir a campanha. | [Game design](01-game-design.md) |
| UX | Dar feedback correto de coleta e mostrar informações decisivas durante o combate. | [UX](02-ux.md) |
| Desenvolvimento | Fechar a validação do sandbox e ligar evidências à build efetivamente avaliada. | [Código, pastas e documentação](03-desenvolvimento.md) |
| QA | O novo snapshot compila; a nova suite de treinamento ainda não está aprovada. | [QA e evidências](04-qa.md) |
| Jogador casual | A primeira sessão precisa ensinar os controles e tornar progresso e recuperação mais compreensíveis. | [Jogador casual](05-jogador-casual.md) |

## Estado avaliado

O checkout tinha alterações locais de implementação em andamento sobre o commit `a05379fcc64754273e6a2b3bf03dda0a2b40bc2f`. Os achados descrevem esse recorte, não uma release fechada. Código, arte, ROM e documentação preexistentes foram preservados; a entrega desta avaliação acrescenta apenas esta pasta.

A ROM da primeira bateria executada foi `game/out/release/Plaguefall.bin`, de 1.441.792 bytes, SHA-256 `1928321fe1aaa430079a296ac0ca6ef837a99b840b87359789fe5d91de947ba1`. Os testes usam o `rom.bin` interno, cujo conteúdo é idêntico ao pacote nomeado conforme a verificação de empacotamento. O manifesto `game/doc/build-validation.json` ainda descrevia outra revisão. Não usar esse manifesto anterior como validação das mudanças atuais.

As suites de resultados, rádio/contagem, arte de combate e sandbox passaram em NTSC e PAL nessa primeira ROM. Também passaram os checks nativos de áudio/mira/exports, empacotamento, cenários e contato da Santa.

Durante a avaliação, alterações concomitantes concluíram a ligação das APIs do sandbox e substituíram a ROM. O primeiro erro de compilação foi superado: a segunda cópia isolada compilou e ligou `rom.out`, e os checks nativos passaram novamente. A nova ROM testada no treinamento tem SHA-256 `1b29878ddda2d8c0b5e0aebcbd81df06f534ad5707e7220309df1cfc2649899c`. A suite nova registrou falhas em galeria e falha da Santa nas duas regiões, além de controles sob carga em NTSC. Essas asserções exigem diagnóstico antes de serem classificadas como defeitos do jogo. Os oito resultados verdes anteriores não foram transferidos para o hash novo.

Prioridades: **P0** bloqueia uma nova build; **P1** afeta entendimento ou progressão e merece a próxima rodada; **P2** é evolução posterior; **P3** é acabamento. Esforços abaixo são relativos, sem estimativa de prazo.

## Caminhos para escolher

| Caminho | Escopo concreto | Esforço relativo | Como saber se terminou |
|---|---|---|---|
| A — Fechar a integração | Diagnosticar asserções do treino, validar a nova ROM e gerar manifesto correspondente. | Pequeno a médio | Build completa e suites pertinentes passam no mesmo hash. |
| B — Melhorar combate e retomada | Inventário cheio, HUD de chefe/rotas, leitura dos resultados, regra de retry e transição 6–7. | Médio | Feedback coerente, repetição viável e comparação controlada entre regras de recuperação. |
| C — Melhorar a primeira sessão | Lembretes contextuais, aprendizado de C/B, apresentação das rotas e teste com 3–5 pessoas. | Médio | Jogadores descobrem controles e explicam objetivo e consequência de rota sem ajuda externa. |
| D — Expandir conteúdo | Duas metas diferentes de eliminação usando o motor existente; depois protótipo de resgate ou demolição. | Médio a grande | Nova missão gera decisões diferentes e mantém campanha concluível nas duas rotas. |

**Sequência recomendada: A → B → C → D.** A corresponde ao fechamento do trabalho em edição. B trata os riscos que atravessam design, UX e perspectiva casual. C deve fornecer evidências humanas para decidir quanto tutorial e ajuste de dificuldade são necessários. D aproveita sistemas existentes depois que a experiência atual estiver consistente.

## Critérios para o próximo playtest

Observar primeiro acerto, descoberta de autofire e C/B, primeira morte, uso de item, compreensão da bifurcação, tempo por fase e equipamento ao repetir. Incluir fases 1, 5, 6B e 7, além de uma fase tardia iniciada com equipamento básico. Comparar legibilidade em tamanho nativo e em movimento. Não tratar as opiniões heurísticas destes relatórios como resultados de pesquisa com jogadores.
