# Campanha — um caminho de volta ao chão

## Estrutura existente

O grafo tem 20 nós e cada partida atravessa 16 fases: quatro etapas possuem versões A/B que voltam ao caminho comum. As decisões são tomadas pelas condições de `levels/graph.c`, sem menu de escolha narrativa. Os nomes de lugar abaixo orientam as falas e a arte futura; a preparação continua mostrando os números das fases.

Todas as cenas de chegada são registradas em `levels/story.c`. Há também uma cena depois da 15 e o final depois da 16. Cenas comuns não lembram uma rota específica depois da convergência: o motor atual não escolhe falas por histórico completo.

## Ato 1 — promessa de céu, vida no chão

Damião contém a primeira incursão, atravessa os terrenos industriais e recebe uma tarefa que torna concreta a razão de lutar: proteger um ponto de encontro da comunidade.

| Nó | Lugar proposto | Objetivo atual | Função da cena |
|---|---|---|---|
| 1 | Pátio de retorno | Eliminar 10 | Abertura do Diabo; segurar passagem enquanto há gente fugindo |
| 2A | Rua de serviço | Eliminar 12, sem lama | Sem bomba na 1: Comando ainda consegue encaminhar Damião pelo acesso direto |
| 2B | Baixio do terminal | Eliminar 12, lama | Usou bomba na 1: o clarão denunciou a posição; Comando indica outro caminho |
| 3 | Sangria dos motores | Eliminar 14, lava | O pouso que era espetáculo deixa vazamento e perigo no chão |
| 4 | Canal de manutenção | Eliminar 16, lama | Os bichos usam a infraestrutura que Damião ajudava a manter |
| 5 | Capela do baixio | Proteger a santa por 30 s | Sustentar o ponto de rádio durante uma transmissão da resistência |

A bifurcação da bomba representa mudança de situação, sem presumir que o jogador destruiu uma ponte ou matou alguém. A rota A não é prêmio moral e a B não é pecado: ambas continuam a mesma operação.

## Ato 2 — o que merece ser salvo

A operação sai da defesa do abrigo e procura a instalação que mantém os ninhos em funcionamento. Damião reconhece o elo entre as cargas que consertava e a ocupação.

| Nó | Lugar proposto | Objetivo atual | Função da cena |
|---|---|---|---|
| 6A | Fundos da capela | Eliminar 20, lava | O ponto resistiu; Comando ouviu respostas de outros abrigos |
| 6B | Corredor da retirada | Eliminar 20, lava, spawns mais rápidos | A santa/estação caiu; reconhecer a perda e seguir pela passagem sob cerco |
| 7 | Baixio das antenas | Eliminar 22, lama, duplas | Dinorah entra pelo rádio: outras vozes mantêm a rede, em qualquer rota |
| 8 | Fornalha de retorno | Eliminar 24, lava, duplas | Revelar que o carregamento dos foguetes alimentava os ninhos |
| 9 | Alfândega automática | Eliminar 24, entrada das elites | A colmeia incorporou equipamento humano; aproximar a matriz |
| 10A | Acesso dos técnicos | Eliminar 26, lama | Sem dano na 9: Damião está em condição de seguir o acesso de manutenção |
| 10B | Dreno térmico | Eliminar 26, lava e lama | Sofreu dano na 9: Comando o conduz pelo dreno para sair do cerco |
| 11 | Casa das bombas | Eliminar 28, lava e lama | A denúncia central: o alerta já existia e as entregas continuaram |
| 12 | Comporta de carga | Eliminar 30, lava e lama | Os teleportadores apertam o cerco; tentar alcançar a próxima passagem a tempo |

A sobrevivência de Damião não apaga a perda da capela. A rota 6B não afirma uma morte humana que o jogo não mostra. A cena da 7 não declara que a estação anterior continua funcionando.

## Ato 3 — ninguém sobe sozinho

Damião chega ao núcleo local da ocupação. Lacraia oferece a imagem perversa da viagem que ele desejava: ser transportado como parte da carga. Ele recusa porque agora sabe para quem precisa voltar.

| Nó | Lugar proposto | Objetivo atual | Função da cena |
|---|---|---|---|
| 13A | Linha quente | Eliminar 34, lava | Venceu a 12 em menos de 60 s: alcançou a passagem direta antes do fechamento |
| 13B | Canal de decantação | Eliminar 34, lama | Levou 60 s ou mais: perdeu a janela e atravessa o canal sob a mesma pressão de spawn |
| 14 | Pátio dos enxames | Eliminar 37, lava e lama, trios | A matriz detecta o avanço; manter a tarefa concreta de abrir caminho |
| 15 | Boca do terminal | Eliminar 40, lava e lama, trios | Último bloqueio; depois da vitória, Comando localiza Lacraia |
| 16 | Ninho sob o porto | Derrotar Lacraia, piso de caverna | Confronto, recusa de virar carga e interrupção do comando local |

A “comporta” dá contexto à condição de tempo; não há porta animada ou contador adicional. O teleporte dos inimigos continua o comportamento existente. A matriz cair não elimina automaticamente todos os inimigos do Brasil.

## Encerramento

Damião confirma a queda da matriz. Comando chama o sobrevivente de volta. Ele fecha a ideia da abertura: ainda queria ver o mundo de cima, mas primeiro precisa garantir que alguém possa continuar vivendo embaixo.

O final não depende de qual rota foi tomada. “Voltar para casa” significa voltar à comunidade, mesmo se a capela foi perdida. Uma futura continuação pode mostrar recuperação de água, reparo de implantes e outros núcleos de ocupação; esta campanha termina com uma vitória local completa.

## Correspondência com a implementação

| Elemento disponível | Uso narrativo nesta revisão |
|---|---|
| `P_DAMIAO`, `P_COMANDO`, `P_LACRAIA`, `P_DINORAH` | Damião, Comando (padre) e Dinorah usam os concepts; Lacraia preserva a arte anterior |
| `ANTES` por nó | Cenas das rotas A e B recebem contexto próprio |
| `DEPOIS` em 15 e 16 | Preparação do confronto e encerramento único |
| `NPC` estático com HP | Santa e estação no mesmo ponto de proteção |
| Uso de bomba / dano / falha / tempo | Condições exatas das quatro bifurcações, sem novas variáveis |
| Lava / lama / caverna | Setores térmicos, canais e ninho, com a arte atual |

Não adicionar uma cena de sucesso em `N_5, DEPOIS`: esse momento também pode ser alcançado na falha roteada. A distinção fica nas chegadas a `N_6A` e `N_6B`. Não escrever um epílogo condicional sem antes implementar memória e seleção próprias para isso.
