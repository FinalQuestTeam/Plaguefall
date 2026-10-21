# Fases e saídas — levantamento de 21/10/2026

Levantamento do código salvo no workspace, incluindo alterações locais. A fonte das rotas é `src/levels/graph.c`; os objetivos vêm de `src/levels/defs/`, com execução em `src/core/flow.c` e `src/core/objective.c`.

## Quantidade e progressão

- **20 nós de campanha**, distribuídos em **16 etapas por partida**: as etapas 2, 6, 10 e 13 têm duas versões.
- **23 ligações**, quatro bifurcações e um único nó final, a fase 16.
- **16 percursos estruturais** possíveis no grafo, todos com 16 fases e terminando no Escorpião.
- **6 estágios de teste**, fora da campanha. Não entram na contagem acima.
- **22 cenas de diálogo e 47 falas**: chegada aos 20 nós, saída da 15 e final da 16. Cada percurso normal apresenta 18 cenas, além dos 12 planos da abertura de boot.

```text
1 → (2A | 2B) → 3 → 4 → 5 → (6A | 6B) → 7 → 8 → 9
  → (10A | 10B) → 11 → 12 → (13A | 13B) → 14 → 15 → 16
```

## Objetivo, terreno e saída de cada fase

“Eliminar” significa atingir a contagem de mortes, sem exigir limpar todos os inimigos restantes. O ritmo abaixo é a quantidade tentada por aparição e o intervalo configurado; o primeiro spawn tem atraso próprio de aproximadamente 1 segundo de jogo ativo.

| Fase | Objetivo | Terreno de perigo | Aparição regular | Saída |
|---|---|---|---|---|
| 1 | Eliminar 10 | Nenhum | 1 / 5 s | Sem bomba → 2A; usou bomba → 2B |
| 2A | Eliminar 12 | Nenhum | 1 / 5 s | 3 |
| 2B | Eliminar 12 | Lama | 1 / 5 s | 3 |
| 3 | Eliminar 14 | Lava | 1 / 4 s | 4 |
| 4 | Eliminar 16 | Lama | 1 / 4 s | 5 |
| 5 | Proteger a santa por 30 s | Nenhum | 1 / 4 s | Protegeu → 6A; santa caiu → 6B **(bloqueada atualmente)** |
| 6A | Eliminar 20 | Lava | 1 / 3 s | 7 |
| 6B | Eliminar 20 | Lava | 1 / 2 s | 7 |
| 7 | Eliminar 22 | Lama | 2 / 3 s | 8 |
| 8 | Eliminar 24 | Lava | 2 / 3 s | 9 |
| 9 | Eliminar 24 | Nenhum | 1 / 4 s | Sem perder HP → 10A; perdeu HP → 10B |
| 10A | Eliminar 26 | Lama | 2 / 3 s | 11 |
| 10B | Eliminar 26 | Lava e lama | 2 / 3 s | 11 |
| 11 | Eliminar 28 | Lava e lama | 2 / 3 s | 12 |
| 12 | Eliminar 30 | Lava e lama | 2 / 3 s | Menos de 60 s → 13A; 60 s ou mais → 13B |
| 13A | Eliminar 34 | Lava | 2 / 2 s | 14 |
| 13B | Eliminar 34 | Lama | 2 / 2 s | 14 |
| 14 | Eliminar 37 | Lava e lama | 3 / 2 s | 15 |
| 15 | Eliminar 40 | Lava e lama | 3 / 2 s | 16 |
| 16 | Derrotar o Escorpião | Piso de caverna, sem lava/lama | Sem spawn regular; chefe invoca lacaios | Diálogo final → tela de fim → START volta ao título |

Há 18 nós de eliminação, um de proteção e um de chefe. Sobrevivência e coleta existem no motor e nos testes, mas não são objetivos da campanha atual. O plano antigo de rotas menciona coleta como recompensa; isso não corresponde às definições atuais.

## Como as condições funcionam

1. **Bomba na fase 1:** conta a detonação que efetivamente consumiu carga. Coletar uma bomba ou tentar ativá-la sem carga não muda a rota. Uma detonação sem matar inimigos também conta.
2. **Proteção na fase 5:** o objeto precisa continuar vivo por 30 segundos ativos. Não precisa ficar intacto. Falhar o objetivo, se Damião estiver vivo, deveria encerrar a fase e levar à retirada. A morte de Damião continua sendo game over.
3. **Dano na fase 9:** conta HP efetivamente perdido naquela tentativa, mesmo que depois seja curado. Começar ferido por uma fase anterior não impede 10A. Um impacto absorvido pelo escudo não conta.
4. **Tempo na fase 12:** usa quadros ativos divididos por 50/60 Hz. Menos de 60 segundos vai para 13A; exatamente 60 já vai para 13B. Preparação, pausa, diálogos, mapa, contagem inicial de 3 segundos e mensagem de conclusão ficam fora. Sob lentidão do jogo, esse relógio pode diferir do tempo de parede.

As estatísticas são zeradas a cada começo/recomeço de fase. As saídas são automáticas; não há menu para escolher o ramo. A primeira condição satisfeita decide, com prioridade explícita para falha de objetivo quando ela existe. Todos os nós não finais têm uma saída padrão.

## Bloqueio encontrado: a santa não consegue cair na fase 5

`level05.c` não define `npcHp`, portanto usa **100 HP** de `actors/npc.h`. Em `actors/npc.c`, cada dano por contato tira **12 HP** e inicia **5 segundos de invulnerabilidade**. Vários inimigos encostando no mesmo quadro provocam apenas uma perda de 12 HP. Não foi encontrada outra fonte de dano ao NPC.

Reproduzindo a ordem do temporizador em 50 e 60 Hz, mesmo com contato em todos os quadros desde o começo, cabem apenas **6 danos em 30 segundos**: 72 HP perdidos, **28 HP restantes**. Spawn, deslocamento e recuo dos inimigos só reduzem esse dano máximo. São necessários 9 danos para derrubar 100 HP.

Consequência: **6B existe e pode ser acessada por debug, mas a falha de proteção não a alcança numa partida normal com os valores atuais**. Excluindo esse ramo, restam 8 dos 16 percursos estruturais e 19 dos 20 nós. A disponibilidade prática dos outros ramos ainda depende da execução do jogador; não foi demonstrada por partidas nesta auditoria.

Proposta de correção para uma etapa de balanceamento: definir `.npcHp = 60` somente na fase 5. A queda passaria a exigir cinco danos, permitindo a falha dentro dos 30 segundos sem mudar a invulnerabilidade global. Isso torna a falha matematicamente possível; é preciso jogar para verificar a frequência real diante do recuo e do movimento dos inimigos. **Nenhuma alteração de balanceamento foi aplicada neste levantamento.**

## Implicações para escrever a história

- A perda da capela é a única bifurcação atual que muda o resultado de uma missão; as outras mudam o caminho de chegada.
- As rotas B não são consistentemente mais fáceis: 2B acrescenta lama; 6B acelera o spawn; 10B acrescenta lava. O plano antigo que descreve B como caminho de menor atrito não serve como regra atual.
- As diferenças devem aparecer nas chegadas a 2A/B, 6A/B, 10A/B e 13A/B. Nas convergências, as falas precisam funcionar para ambas.
- Há registro de nós visitados para o mapa e cenas vistas, mas o seletor de diálogos atual consulta somente nó e momento. Não há epílogo selecionado por histórico de escolhas.
- A fase 5 passa pelo fluxo de cena DEPOIS tanto no sucesso quanto na falha roteada. Não colocar ali uma fala incondicional dizendo que a capela foi salva.
- Dinorah tem retrato e uma participação por rádio antes da fase 7. Sua presença física, escolta e combate aliado não estão implementados.
- Os nomes de lugares da história são contexto textual; as arenas atuais não implementam portas, evacuação ou destruição de infraestrutura.

## Verificação realizada

Foi percorrido o grafo por script: 20 nós, 23 ligações, 16 percursos, nenhum ciclo ou destino ausente e 16 fases em todos os percursos, sempre terminando em `N_16`. Os 20 nós têm cena ANTES; os 22 pares nó/momento são únicos. As 47 falas foram submetidas a uma reprodução da quebra de texto de 26 colunas por 4 linhas, sem cortes.

A impossibilidade de queda da santa foi verificada por análise das fontes de dano e simulação isolada do temporizador em 50/60 Hz. Não foi feita nova compilação nem execução no emulador; o código e a ROM não foram modificados.

Próximo material: [tratamento completo proposto](tratamento-proposto.md), desenvolvido a partir do universo e da campanha que já existem.
