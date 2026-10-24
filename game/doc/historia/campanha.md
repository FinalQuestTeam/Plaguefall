# Campanha proposta e consequências das rotas

A campanha de 23 de outubro de 2026 liga a retirada da igreja, a recuperação dos recursos de O Último Chão e a destruição dos criadouros nos foguetes de São Jerônimo. São 19 versões de fase e 16 fases por partida. A [história completa e os impactos das rotas](tratamento-proposto.md) reúne o prólogo, as cenas, os diálogos e os encerramentos. A integração desse roteiro à ROM foi concluída; veja [implementação e playtests](../campanha-implementada.md).

## Início da história

O começo é a animação já existente no jogo, preservada com 14 planos, 18 cartelas e 1min41s. Depois vêm o menu, a nova partida, a chamada curta do padre e a fase 1 no pátio. Não há outro prólogo na oficina. A [abertura aprovada](storyboard-abertura-v2.md) e suas capturas estão incluídas no [storyboard da campanha](storyboard-campanha.md).

## Progressão das fases

| Fase | Local | Objetivo proposto | Resultado ou destino |
|---|---|---|---|
| 1 | Pátio da igreja | Sobreviver por 1min30s; um único tipo de inseto básico | Sem bomba → 2A; com bomba → 2B; todos saem da igreja |
| 2A | Pátio preservado | Eliminar 15 insetos; introduzir o atirador | Igreja inteira; seguir para 3 |
| 2B | Pátio destruído | Eliminar 15 insetos, com destroços impedindo algumas passagens | Igreja destruída; seguir para 3 |
| 3 | Rua até o galpão, 2.560 px | Alcançar o galpão | Abrir caminho para os civis; seguir para 4 |
| 4 | Interior do galpão | Eliminar 20 insetos | Abrigar o povo e preparar o resgate; seguir para 5 |
| 5 | Pátio do galpão | Proteger a santa e o comunicador por 2 min | Evacuação completa → 6A; falha com perdas civis → 6B |
| 6A | Esgotos, 3.072 px | Escoltar Dinorah | Percurso simples; seguir para 7 |
| 6B | Esgotos, 3.072 px | Escoltar Dinorah, abrir portões e aliviar pressão | Percurso com barreiras; seguir para 7 |
| 7 | Abrigo de O Último Chão na favela | Recuperar e entregar suprimentos de 5 pontos | Recursos recuperados; seguir para 8 |
| 8 | Entorno da base comprometida | Eliminar insetos prioritários e reduzir reforços | Sugestão inicial de 3 alvos; seguir para 9 |
| 9 | Caminho até a fábrica, 2.560 px | Alcançar a fábrica | Seguir para a fase 10 única, independentemente do dano sofrido |
| 10 | Fábrica | Destruir 10 conjuntos de ovos | Identificar os foguetes como próximo alvo; seguir para 11 |
| 11 | Máquinas da fábrica | Liberar válvulas e reativar a instalação | Atrair o enxame pelo calor; sugestão inicial de 3 válvulas; seguir para 12 |
| 12 | Acesso ao estaleiro, 3.072 px | Escoltar Dinorah até a sala dos trabalhadores | Viva → 13A; morta com Damião vivo → 13B |
| 13A | Sala de descanso | Eliminar 30 insetos | Dinorah assume o painel de manutenção em posição protegida; seguir para 14 |
| 13B | Sala de descanso | Eliminar 45 insetos | Damião assume a preparação técnica; Dinorah permanece morta; seguir para 14 |
| 14 | Energia do estaleiro | Ativar 5 máquinas | Alimentar controle e ignição; seguir para 15 |
| 15 | Posto de comunicação | Proteger o rádio por 2 min | Concluir a ignição dos motores e incendiar os criadouros; seguir para 16 |
| 16 | Área de lançamento em chamas | Derrotar Escorpião | Retirada de Damião e epílogo conforme os três resultados |

## Estados persistentes

| Estado | Consequência imediata | Consequência posterior |
|---|---|---|
| Igreja inteira ou destruída | Cenário e circulação em 2A/2B | Conversa e imagem da igreja no retorno |
| Resgate completo ou parcial | Escolta simples em 6A ou com barreiras em 6B | Falas de alívio ou luto na 7 e no epílogo |
| Dinorah viva ou morta | 30 eliminações na 13A ou 45 na 13B | Trio nas conversas finais ou somente Damião e padre; reconstrução com ela ou homenagem |

Os três resultados são independentes e geram oito combinações de encerramento. A igreja pode ser destruída e todos os civis resgatados. Dinorah pode sobreviver depois das perdas civis ou morrer depois de um resgate completo. A vitória final não apaga qualquer dessas consequências.

## Continuidade do resgate e de Dinorah

A santa é retirada da igreja pelo padre antes do combate inicial. O primeiro grupo de civis já embarcou quando começa a defesa de 2 minutos na fase 5. Se o comunicador cair, alguns escapam e os grupos ainda no chão sofrem perdas. O padre acompanha a evacuação e mantém contato por rádio.

Dinorah chega na fase 5 e permanece com Damião depois de 6A ou 6B. A morte dela na fase 6 reinicia a missão. Somente a falha da escolta na fase 12, com Damião vivo, torna sua morte definitiva e permite continuar na 13B. A morte de Damião tem prioridade de derrota, inclusive numa queda simultânea.

Se Dinorah sobreviver, ela prepara os comandos na fase 14, conduz a ignição na 15 e participa da conversa com Escorpião e da retirada na 16. Permanece em posição protegida após a 13A; essas fases não acrescentam outra condição de morte dela. Se morrer, Damião prepara a sequência e o padre acompanha sua execução automática. As conversas finais continuam entre os dois.

## Encerramento

Os ovos da fábrica são destruídos na fase 10. Reativar a fábrica na 11 atrai parte do enxame e abre o caminho ao estaleiro. Na 15, os motores queimam os criadouros dos foguetes. Escorpião emerge do fogo e precisa ser derrotado para Damião sair do local.

Não há instalação posterior de cargas nem exigência de bombas restantes no inventário. Nos dias seguintes, a resistência elimina os focos isolados e confirma a libertação de São Jerônimo. O planeta continua infestado.

O epílogo combina o estado da igreja, a presença ou ausência de vítimas civis e o destino de Dinorah. A versão completa contém as falas e as oito combinações.

## Integração na ROM

O [grafo](../../src/levels/graph.c) tem 19 nós: fase 10 única e fase 12 bifurcando pela sobrevivência de Dinorah. `core/campaign_state.c` mantém três consequências independentes; `levels/story.c` seleciona as conversas 14–16 e oito epílogos.

Os mapas, sprites e objetivos estão integrados. A [validação da campanha](../campanha-implementada.md) reúne os dez ensaios de emulador na ROM final, os limites de carga e as limitações dos testes automáticos. A auditoria anterior permanece como registro histórico.
