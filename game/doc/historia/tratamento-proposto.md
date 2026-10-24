# História completa da campanha e impactos das rotas

Revisão narrativa de 23 de outubro de 2026. A campanha acompanha a retirada da igreja, a recuperação de recursos de O Último Chão e o ataque aos foguetes que sustentam a infestação de São Jerônimo. São 16 fases por partida e 19 versões de fase, com três resultados independentes: o estado da igreja, as perdas no resgate e a sobrevivência de Dinorah.

A história começa com a animação de abertura que já existe no jogo. Seus 14 planos, 18 cartelas, monólogo e chamado do padre são preservados. Este roteiro orienta a campanha que continua depois dela; a integração das novas fases e variantes à ROM é uma etapa posterior. Os diálogos estão em formato de leitura; a adaptação às caixas do jogo deve preservar o sentido e dividir falas longas.

## Premissa e personagens

No sertão industrial de um Brasil futuro, foguetes que antes representavam progresso voltaram trazendo ovos e organismos invasores. A rede de transporte espalhou a infestação pelas instalações e pelos bairros de trabalhadores. São Jerônimo é uma das regiões ocupadas; destruir seus criadouros não liberta automaticamente o restante do planeta.

Damião era mecânico no porto de lançamento e sonhava em viajar nas máquinas que consertava. Perdeu o braço esquerdo durante a crise e usa uma prótese feita com peças recuperadas pela comunidade. Seu conhecimento de manutenção, antes tratado como trabalho sem futuro, será decisivo para enfrentar os invasores. Ele chama todos os insetos de baratas e usa o humor para suportar o medo e o cansaço.

O padre, identificado como Comando no rádio, organiza abrigos, retirada e comunicação. A fé participa do cuidado com as pessoas e de sua forma de lidar com perdas. Ele acompanha a evacuação e continua falando com Damião pelo rádio; não precisa estar fisicamente nas arenas seguintes.

Dinorah é técnica de campo de O Último Chão, conhece o estaleiro e tem uma história de organização sindical entre seus trabalhadores. É direta, provocadora e competente. Sua relação com Damião combina atrito político, respeito profissional e confiança conquistada sob pressão. Ela chega ao pátio do galpão na fase 5 e permanece na operação após qualquer resultado do resgate.

Escorpião coordena o enxame local. É o primeiro inseto a se comunicar com os humanos, apenas no confronto final. Sua fala tenta justificar a ocupação pela decadência do mundo que encontrou; a campanha não confirma essa justificativa como verdade.

## Fluxo da campanha

```text
1 ─┬─ 2A ─┬─ 3 → 4 → 5 ─┬─ 6A ─┬─ 7 → 8 → 9 → 10 → 11 → 12 ─┬─ 13A ─┬─ 14 → 15 → 16
   └─ 2B ─┘              └─ 6B ─┘                            └─ 13B ─┘
```

| Decisão ou resultado | Rota A | Rota B |
|---|---|---|
| Uso de bomba na fase 1 | Sem bomba: igreja preservada, 2A | Com bomba: igreja destruída, 2B |
| Defesa da santa na fase 5 | Evacuação completa, 6A | Evacuação parcial e mortes civis, 6B |
| Escolta na fase 12 | Dinorah sobrevive, 13A | Dinorah morre, 13B |

As rotas convergem geograficamente, mas seus resultados permanecem nas conversas e no epílogo. O dano sofrido na fase 9 e o tempo gasto na fase 12 não criam bifurcações nesta versão.

## Prólogo com a animação de abertura existente

O início da história é a [animação já integrada ao começo do jogo](../../art/intro-monologo-v2/README.md), com 14 planos, 18 cartelas e 1min41s de monólogo. A ordem das imagens, o texto e a encenação seguem o [storyboard aprovado da abertura](storyboard-abertura-v2.md). Não há um novo prólogo em que Damião descobre os ovos numa oficina.

A animação apresenta a pergunta sobre o Diabo, o sonho, o trabalho, o retorno dos foguetes, os ovos, a ausência dos tripulantes, os invasores, a prótese esquerda, o povo, a reza, o chamado do padre, a retirada e a decisão de proteger. As lembranças do ofício pertencem aos planos 3 e 4 dessa animação; o chamado do padre traz a ação ao pátio da igreja.

### Monólogo de Damião

> Você já ouviu falar que o Diabo dá tudo que a gente quer?
>
> Mas sempre da maneira mais filha da puta possível?
>
> Eu sonhava com astronautas, extraterrestres e foguetes.
>
> Eu consertava essas máquinas, achando que um dia iam me deixar subir.
>
> As naves que levavam os meus sonhos…
>
> hoje voltam trazendo ovos.
>
> De quem foi nelas, nem sinal.
>
> Só aquelas merdas saíram de dentro. Patas, asas e zumbido.
> Pra mim, é tudo barata.
>
> Já perdi um braço. Quase perdi uma perna.
>
> Mas esse povo ainda precisa de mim.
>
> Minha mãe sempre mandava eu levar uma reza.
> Eu levo. No bolso da munição.

**Padre, pelo rádio:** “Damião… Damião, tá me ouvindo? Aqui é o padre. Ainda tem gente aqui dentro. A gente tá tirando todo mundo pelos fundos, mas eles já chegaram no pátio. Segura eles mais um pouco.”

**Damião:** “Tô ouvindo. Hoje ninguém vai pro céu antes da hora.”

O padre leva a imagem de Nossa Senhora Aparecida para fora antes do combate. Ela acompanha os civis e pode reaparecer na fase 5 mesmo que a igreja seja destruída. A referência ao Diabo pertence à interpretação de Damião; não estabelece um pacto literal como origem da invasão.

### Da animação à fase 1

O fluxo existente é FinalQuest → APRESENTA → logo Plaguefall → animação de abertura → menu. Ao escolher nova partida, a conversa curta de missão retoma a situação do pátio, sem repetir o monólogo ou criar outra cena de descoberta dos ovos. A animação continua tocando uma vez por boot e pode ser pulada com START.

**Padre:** “Damião, aqui é o padre. Segure o pátio. Tem gente fugindo pelo fundo.”

**Damião:** “Tô indo. Hoje ninguém vai pro céu antes da hora.”

Essa chamada pertence à entrada da fase 1. A defesa de 1min30s começa depois dela.

## Ato 1 A retirada

### Fase 1 Até o último sair

**Local:** pátio da igreja. **Objetivo:** sobreviver por 1min30s enquanto os civis saem. **Inimigos:** um único tipo básico de ataque por contato.

Damião segura a aproximação dos insetos. O espaço permite aprender movimentação, tiro e itens sem a pressão de projéteis inimigos. O cronômetro representa o tempo necessário para retirar a última pessoa; não há uma segunda condição de eliminar todos os inimigos.

A chamada curta acima faz a transição para o combate. O tempo necessário à retirada é apresentado como objetivo de 1min30s.

Antes de o jogador poder usar a bomba, o risco deve ficar claro.

**Padre:** “As paredes já estão comprometidas. Uma explosão aqui pode derrubar a igreja.”

Na conclusão, o padre confirma a saída do último civil. Usar qualquer bomba durante a fase determina a destruição da igreja e a ida à 2B; terminar sem usar bomba leva à 2A. Todos conseguem deixar a igreja nas duas rotas. As perdas civis posteriores dependem da fase 5.

### Fase 2A A igreja de pé

**Local:** o mesmo pátio, com a igreja preservada. **Objetivo:** eliminar 15 insetos. **Novidade:** primeiro inimigo de disparo, misturado ao básico.

Com os civis fora da igreja, Damião elimina os perseguidores antes de acompanhar a retirada. A fachada preservada confirma visualmente a consequência da fase anterior.

**Padre:** “Todos saíram. Você protegeu nosso povo e manteve a igreja de pé.”

**Damião:** “Então vamos embora antes que elas tragam reforço.”

A igreja permanece inteira, mas o bairro está cercado. Ela não é segura para uma permanência imediata. Ao concluir as 15 eliminações, Damião segue para a fase 3.

### Fase 2B Entre os escombros

**Local:** pátio da igreja destruído. **Objetivo:** eliminar 15 insetos. **Inimigos:** os mesmos da 2A, incluindo o primeiro atirador.

Destroços da parede e do telhado criam desvios, interrompem linhas de tiro e reduzem alguns espaços de circulação. Devem existir caminhos legíveis para contornar os bloqueios. A mudança de cenário torna o impacto da bomba jogável.

**Padre:** “Graças a Deus, todos saíram… Mas a nossa igreja…”

**Damião:** “Vidas valem mais que prédios, padre.”

O padre reconhece a sobrevivência das pessoas e lamenta a perda do lugar. Damião defende sua decisão sem comemorar a destruição. Não são acrescentadas mortes ou perdas obrigatórias de inventário à escolha da bomba. A conclusão leva à fase 3.

### Fase 3 Abram caminho

**Local:** rua até o galpão, com 2.560 pixels de comprimento. **Objetivo:** alcançar a entrada do galpão.

É a primeira fase de deslocamento. Damião vai à frente, atravessando encontros distribuídos entre trechos abertos e passagens estreitas. O padre mantém os civis atrás da área de combate; eles avançam após a confirmação do caminho.

**Padre:** “Vá na frente e abra caminho até o galpão. Eu levo o povo logo atrás.”

**Damião:** “Só venham quando eu avisar.”

Na chegada, Damião percebe que o prédio também está ocupado.

**Damião:** “A rua está livre. Segurem o povo aí fora. Tem barata dentro do galpão.”

Alcançar o destino conclui a fase; não é necessário eliminar todos os insetos da rua. A entrada no galpão leva à fase 4.

### Fase 4 Um teto para a noite

**Local:** interior do galpão. **Objetivo:** eliminar 20 insetos.

Pilares e materiais armazenados organizam o combate em arena. A limpeza permite acolher as famílias enquanto O Último Chão procura uma forma de retirá-las da região.

**Padre:** “Precisamos de um teto para esta noite. Vou tentar contato com O Último Chão.”

**Damião:** “Então me dê um pouco de espaço para arrumar a casa.”

Depois do combate, os civis entram. Ao tentar contato com a resistência, o padre descobre uma oportunidade de resgate e decide usar um equipamento que trouxe consigo. A possibilidade de evacuar o povo antecipa a saída que esperavam organizar durante a noite.

**Padre:** “Consegui notícia de transportes de resgate. Talvez a gente não precise passar a noite aqui.”

### Fase 5 O sinal da santa

**Local:** pátio em frente ao galpão. **Objetivo:** proteger a santa e o comunicador por 2 minutos.

O padre revela o dispositivo escondido na base da imagem desde os tempos de atuação clandestina da resistência. O equipamento transmite identificação e posição de pouso. As naves são transportes humanos de sobreviventes, distintos dos foguetes contaminados.

**Padre:** “Escondi um comunicador na base da santa, nos tempos da resistência. Ainda podemos chamar o resgate.”

Dinorah chega pelo acesso usado por O Último Chão e ajuda a preparar a evacuação.

**Dinorah:** “Depois que esse povo estiver seguro, vai ser mais fácil lutar.”

**Damião:** “Primeiro tiramos todos daqui.”

O chamado começa antes da defesa. Para manter uma possibilidade de resgate parcial mesmo numa falha precoce, a cena inicial confirma que o primeiro grupo já embarcou. Os 2 minutos cobrem a retirada dos grupos restantes e a chegada do último transporte. O rádio fornece avisos de embarque e aproximação.

**Padre:** “O primeiro grupo já embarcou. Precisamos manter o sinal até a última nave sair.”

**Sucesso:** o comunicador permanece operacional durante os 2 minutos. Todos os civis saem da área, e a campanha segue para a 6A.

**Padre:** “O último grupo embarcou. Todos estão a salvo.”

**Falha:** o objetivo é destruído antes do fim. Os transportes já em saída escapam, mas a posição dos grupos restantes é tomada. Uma cena curta confirma as mortes; a consequência não pode ficar apenas implícita num contador. Damião sobrevive e a campanha segue para a 6B.

**Padre:** “O sinal caiu! Quem já embarcou conseguiu sair… Perdemos gente aqui embaixo.”

O padre acompanha os evacuados e permanece no rádio. Dinorah fica com Damião em ambos os resultados. A falha muda as perdas civis e o caminho dos esgotos, sem provocar a partida dela.

## Ato 2 O Último Chão

### Fase 6A Pela passagem de baixo

**Local:** esgotos da cidade, com 3.072 pixels. **Objetivo:** escoltar Dinorah até o abrigo de O Último Chão.

Com o povo evacuado, os dois buscam recursos para continuar combatendo a infestação. Dinorah conhece a entrada da base e precisa de cobertura no deslocamento.

**Dinorah:** “O povo conseguiu sair. Agora me leve até a base e eu arranjo recursos para continuarmos.”

**Damião:** “Mostre o caminho.”

A escolta apresenta regras simples: Dinorah acompanha Damião, espera por cobertura e para quando ele se distancia demais. Os esgotos oferecem a passagem que evita a concentração inimiga na superfície. Chegar à saída com ela viva leva à fase 7.

### Fase 6B O peso dos que ficaram

**Local:** esgotos da cidade, com 3.072 pixels e barreiras. **Objetivo:** escoltar Dinorah até o mesmo abrigo, abrindo a passagem.

O acesso mais direto ficou comprometido durante o cerco. A retirada obriga o uso de um ramal com portões e tubulações pressurizadas. A escolta combina proteção, abertura de barreiras e válvulas que permitem atravessar os trechos perigosos. Os números de portões e válvulas serão definidos no desenho do percurso.

**Dinorah:** “Não conseguimos tirar todos. Baixas acontecem, Damião.”

Damião chora antes de conseguir responder.

**Damião:** “Eram meu povo…”

**Padre, pelo rádio:** “Deus tem um plano, meu filho. Agora precisamos seguir com fé.”

Dinorah reage tentando manter a operação em movimento; sua dureza não encerra o luto de Damião. O padre continua acompanhando os sobreviventes à distância. Chegar ao abrigo leva à fase 7.

**Regra das duas versões da fase 6:** a morte de Dinorah reinicia a missão. Não cria uma rota narrativa adicional. O ponto em que sua morte pode se tornar definitiva é a fase 12.

### Fase 7 O que ainda resta

**Local:** abrigo de O Último Chão, na favela. **Objetivo:** recuperar suprimentos em 5 pontos e entregar as cinco cargas no depósito seguro.

A base também foi invadida. Caixas e materiais ficaram espalhados quando seus defensores recuaram. Damião transporta uma carga por vez, escolhendo caminhos entre coleta e entrega. Cada entrega deve ser reconhecível; alcançar um ponto de coleta sozinho não conclui o objetivo.

**Dinorah:** “Essas baratas estão em todo lugar!”

**Damião:** “Esses suprimentos mantêm a resistência viva. Não vamos deixar nada para elas.”

**Padre:** “Cautela. Agora cada passo importa.”

Depois das entregas, uma fala reconhece o resultado do resgate.

**Se todos foram resgatados — Dinorah:** “O povo está seguro. Agora temos com que continuar.”

**Se houve perdas — Damião:** “A gente trouxe os suprimentos. Queria ter trazido todo mundo.”

A recuperação garante meios para a próxima operação, mas não transforma o abrigo novamente num lugar seguro.

### Fase 8 Cortar o chamado

**Local:** entorno da base comprometida. **Objetivo:** eliminar os insetos prioritários que atraem o enxame.

Alguns insetos estão coordenando a chegada de reforços. Damião precisa identificá-los e alcançá-los entre os inimigos comuns. A cada alvo prioritário morto, a pressão de reforços diminui. Não há exigência de exterminar todos os inimigos da região.

**Padre:** “Se continuarem chegando, vamos gastar tudo o que acabamos de recuperar.”

**Damião:** “Então eu não deixo uma viva.”

**Dinorah:** “Use a cabeça. Mate quem está chamando o resto.”

**Parâmetro inicial sugerido:** 3 alvos prioritários identificados. O número deve ser confirmado no balanceamento, sem mudar a lógica da missão.

Ao fim, a ameaça imediata diminui. A base continua comprometida e o grupo decide atacar a origem dos reforços. O padre relaciona os relatos sobre ovos à antiga fábrica, criando o destino da fase seguinte.

### Fase 9 O caminho dos ovos

**Local:** corredor industrial até a fábrica, com 2.560 pixels. **Objetivo:** alcançar a fábrica.

Os encontros combinam inimigos de contato e de disparo em posições mais exigentes que na primeira travessia. A ação passa da recuperação de recursos ao ataque aos criadouros.

**Padre:** “Foi naquela fábrica que ouvi os primeiros relatos sobre os ovos.”

**Damião:** “Então é para lá que eu vou. Primeiro abro caminho. Depois resolvo o resto.”

Dinorah acompanha a operação pelo rádio a partir de uma posição protegida, enquanto Damião abre o acesso. Alcançar a entrada conclui a fase. Sofrer dano não altera o destino: todos seguem para a fase 10.

### Fase 10 O berçário

**Local:** interior da fábrica. **Objetivo:** destruir 10 conjuntos de ovos.

Os ovos ocupam máquinas e áreas de manutenção. Cada conjunto tem leitura visual própria e contribui uma unidade para o contador. Insetos defendem os pontos, mas matar inimigos comuns não substitui a destruição dos ovos.

**Damião:** “Nunca vi tanto ovo junto.”

**Dinorah:** “Vai ficar olhando com medo ou vai acabar com eles?”

**Padre:** “Deus o acompanhe, Damião. Você está no caminho dos justos.”

Ao percorrer os setores, Damião reconhece o acesso de serviço que liga a fábrica ao estaleiro. O fluxo de insetos vindo de lá e os relatos sobre as cargas confirmam o próximo alvo: os foguetes que trouxeram e ainda abrigam criadouros. Destruir os dez conjuntos limpa esta fábrica, sem encerrar a infestação regional.

### Fase 11 Acender a isca

**Local:** setor de máquinas da fábrica. **Objetivo:** liberar as válvulas para recolocar a fábrica em funcionamento.

Damião percebe que o calor das máquinas pode concentrar os insetos num lugar distante do caminho até os foguetes. Dinorah ajuda a verificar os comandos; o padre propõe transformar essa observação numa distração.

**Damião:** “Quando eu era mecânico, essas pragas viviam se enfiando nas partes quentes das máquinas.”

**Padre:** “Então podemos fazer desta fábrica um chamado para elas.”

**Dinorah:** “Um homem de saia e um mecânico maneta. Quero ver esse plano funcionar.”

**Parâmetro inicial sugerido:** 3 válvulas, distribuídas em setores distintos. Cada ativação liga parte das instalações e torna perceptível o aumento do calor. A pressão muda durante a operação, com os insetos procurando os setores aquecidos.

Na conclusão, a fábrica volta a operar e começa a atrair o enxame. Isso abre uma janela de passagem até o estaleiro. Os ovos destruídos não reaparecem: os insetos estão tentando ocupar o local para formar um novo ninho. A distração é temporária, e os criadouros dos foguetes continuam sendo a ameaça principal.

## Ato 3 Queimar a origem

### Fase 12 A última travessia

**Local:** acesso ao estaleiro espacial, com 3.072 pixels. **Objetivo:** escoltar Dinorah até a sala de descanso dos trabalhadores.

Dinorah se reúne com Damião na saída da fábrica para atravessar o setor exposto. A sala do sindicato oferece abrigo e acesso aos sistemas de serviço usados na operação final. A escolta retoma as regras aprendidas nos esgotos, com maior pressão ao abrir passagens.

**Damião:** “As baratas estão indo fazer ninho na fábrica. É nossa chance de entrar no estaleiro.”

**Dinorah:** “Me leve até a sala do sindicato. Conheço aquele setor.”

**Padre:** “Vamos preparar ali nossa última incursão.”

**Sucesso:** Dinorah alcança o destino viva. A campanha segue para a 13A e mantém sua participação até o final.

**Falha com Damião vivo:** Dinorah morre durante a travessia. O combate é interrompido para uma breve cena de perda. Damião alcança a sala numa transição narrativa, e a campanha continua na 13B. A morte é definitiva nesta partida.

**Damião:** “Dinorah? Dinorah, responda!”

**Padre:** “Damião… você precisa sair daí.”

A morte de Damião continua sendo derrota e reinício, mesmo que ocorra junto à queda de Dinorah. O tempo da travessia não decide a sobrevivência dela.

### Fase 13A Velhos piquetes

**Local:** sala de descanso dos trabalhadores. **Objetivo:** eliminar 30 insetos.

Dinorah chega viva, mas a sala está ocupada. Ela se recolhe a um compartimento protegido enquanto Damião elimina os invasores. Esta fase é de limpeza, sem um segundo objetivo de escolta ou de proteger uma barra de vida de Dinorah.

**Dinorah:** “Fiz muito piquete saindo dessa sala.”

**Damião:** “Vocês vermelhos gostavam mesmo era de ficar sem trabalhar.”

**Padre:** “Vou gastar um pouco da água benta que trouxe para abençoar este lugar.”

O deboche entre os dois aparece depois de uma travessia em que dependeram um do outro. Ao concluir, Dinorah acessa o painel de manutenção ligado à rede de controle do estaleiro. Ela permanece nesse ponto protegido, orientando Damião pelo rádio nas fases 14 a 16.

### Fase 13B Um lugar vazio

**Local:** a mesma sala de descanso. **Objetivo:** eliminar 45 insetos.

Damião entra sem Dinorah. O contingente maior representa a ocupação mais intensa do setor após a travessia interrompida. São 45 eliminações acumuladas, sem exigir esse número de inimigos simultâneos.

**Damião:** “Ela era grosseira… Mas eu respeitava aquela mulher. Eu devia ter protegido ela.”

**Padre:** “Que Deus a receba. Nenhum de nós devia precisar pagar esse preço.”

A morte não é tratada como uma exigência divina para a vitória. Ao fim da limpeza, Damião usa seu conhecimento de manutenção para acessar os controles. O padre continua como sua única voz aliada nas conversas finais.

### Fase 14 Devolver a força às máquinas

**Local:** subestação e instalações do estaleiro. **Objetivo:** ativar 5 máquinas de energia.

As máquinas alimentam os sistemas de controle e ignição dos motores. Damião precisa circular entre os cinco pontos sob ataque. As ativações tornam o cenário progressivamente operacional, mas os motores ainda não entram em ignição.

#### Conversa com Dinorah viva

**Dinorah:** “Conheço esses circuitos. Ligue as cinco máquinas e eu preparo o comando de ignição.”

**Damião:** “Com os motores funcionando, a gente queima os ninhos debaixo dos foguetes.”

**Padre:** “Vou conferir se ainda há alguém no perímetro.”

**Dinorah:** “Confira mesmo. Depois que começar, ninguém pode estar lá.”

Dinorah verifica os circuitos pelo painel de manutenção e prepara o comando para a próxima etapa. O padre coordena a conferência do perímetro pela rede de resistência.

#### Conversa com Dinorah morta

**Damião:** “Com energia, consigo acionar os motores. O fogo pega os ninhos embaixo dos foguetes.”

**Padre:** “Vou conferir o perímetro e a retirada. Você prepara a ignição.”

Damião configura a sequência a partir dos controles de serviço antes de avançar. O padre acompanha a operação pelo rádio. Não é necessário introduzir outra pessoa para ocupar o papel de Dinorah.

Nas duas versões, ativar as cinco máquinas libera a fase 15. A ausência de Dinorah muda quem prepara e acompanha os comandos, sem mudar o objetivo ou impedir a vitória.

### Fase 15 Não deixem o sinal cair

**Local:** posto de comunicação do estaleiro. **Objetivo:** proteger o rádio por 2 minutos.

O rádio mantém o enlace de controle e a comunicação entre os setores durante a ignição escalonada. O console de serviço depende desse enlace para concluir a sequência. Assim, a proteção do equipamento tem uma função concreta além de permitir conversa.

Os ataques vêm por acessos distintos. Motores entram em funcionamento durante a defesa, com mudanças de luz, som e fogo ao fundo. O rádio precisa permanecer operacional até o último comando. Não é preciso eliminar todos os inimigos.

#### Conversa com Dinorah viva

**Dinorah:** “Estou no comando de ignição. Preciso de dois minutos e dessa comunicação funcionando.”

**Damião:** “Pode trabalhar. Nenhuma barata encosta no rádio.”

**Padre:** “Perímetro livre. Podem começar.”

Durante a defesa, Dinorah confirma os comandos enviados pelo painel da sala de descanso.

**Dinorah:** “Primeiro motor aceso. Segure mais um pouco!”

**Damião:** “Você sempre pede só mais um pouco!”

**Dinorah:** “E você sempre reclama trabalhando. Continue!”

Na conclusão:

**Dinorah:** “Último motor acionado. Damião, saia daí!”

#### Conversa com Dinorah morta

A sequência foi preparada por Damião na fase anterior e é executada pelos controles automáticos. O padre acompanha a confirmação dos comandos.

**Padre:** “A sequência começou. Precisamos manter este posto até o último motor acender.”

**Damião:** “Então ninguém encosta nesse rádio.”

Na conclusão:

**Padre:** “Último motor aceso. Saia do posto, Damião!”

**Sucesso:** aos 2 minutos, a ignição termina e o fogo alcança os criadouros dos foguetes. **Falha:** se o rádio cair antes disso, a missão é reiniciada. Não existe uma quarta bifurcação narrativa.

### Fase 16 A voz do enxame

**Local:** área de lançamento em chamas. **Objetivo:** derrotar Escorpião.

A ignição destrói os criadouros sob os foguetes, mas força Escorpião a sair da área atingida. Ele emerge entre as chamas e bloqueia a retirada de Damião. A voz pode chegar traduzida pelo rádio, mantendo a surpresa de um invasor que se comunica pela primeira vez.

#### Conversa com Dinorah viva

**Dinorah:** “Tem alguma coisa saindo do fogo… Damião, cuidado!”

**Escorpião:** “Este mundo já estava podre antes de chegarmos. É estranho que ainda resistam tanto.”

**Dinorah:** “Essa coisa está falando?”

**Damião:** “E já começou falando besteira.”

**Padre:** “Damião, mantenha distância. Ainda não sabemos do que ele é capaz.”

**Damião:** “Nossa casa tem problema. Mas não vai ser barata que vai decidir nosso futuro.”

Dinorah continua acompanhando os sistemas e a área de lançamento pelo painel. Um aviso curto durante o confronto mantém sua participação na operação.

**Dinorah:** “O fogo está fechando o acesso. A saída de serviço continua livre!”

#### Conversa com Dinorah morta

**Padre:** “Damião, alguma coisa está saindo do fogo!”

**Escorpião:** “Este mundo já estava podre antes de chegarmos. É estranho que ainda resistam tanto.”

**Damião:** “Estranho é você achar que a gente ia entregar nossa casa.”

O padre acompanha Damião durante o confronto, sem falas ou ações atribuídas a Dinorah.

#### Confronto e conclusão

O combate culmina a leitura de investidas, projéteis e janelas de ataque aprendida durante a campanha. Uma divisão do chefe em três momentos de combate pode ser estudada no balanceamento; não é condição para a continuidade narrativa.

Derrotar Escorpião permite a retirada de Damião pela passagem de serviço. O fogo já destruiu os criadouros dos foguetes, e os ovos da fábrica foram eliminados na fase 10. Não há uma nova missão de instalar cargas depois do chefe, nem exigência de guardar bombas no inventário para concluir a campanha.

## Epílogo e consequências permanentes

### Resultado comum

Damião deixa o estaleiro enquanto os motores queimam os últimos focos nos foguetes. Sem os criadouros e sem o comando local de Escorpião, a resistência consegue eliminar os insetos isolados nos dias seguintes. Uma passagem de tempo confirma São Jerônimo livre da ocupação local.

A comunidade inicia o retorno e a recuperação dos bairros. O rádio ainda recebe chamados de outras regiões; o planeta permanece infestado. A vitória permite reconstruir, mas não devolve as pessoas que morreram.

### Encerramento com Dinorah viva

Depois do confronto, Dinorah confirma o resultado da ignição e sai do setor protegido para se reunir com Damião.

**Dinorah:** “Os motores queimaram os criadouros. Acabou aqui.”

**Padre:** “O povo vai poder voltar.”

**Damião:** “E agora?”

**Dinorah:** “Agora dá trabalho reconstruir.”

**Damião:** “Quero ver você fugir do serviço.”

**Dinorah:** “Pode deixar, maneta. Eu fico.”

Ela participa da reconstrução com sua competência técnica e sua experiência de organização. A sobrevivência consolida a parceria com Damião, sem exigir que os dois deixem de discordar.

### Encerramento com Dinorah morta

**Padre:** “Os criadouros foram destruídos. O povo vai poder voltar.”

**Damião:** “Ela devia estar aqui para ver.”

**Padre:** “Vamos levar a memória dela conosco.”

No retorno, a comunidade faz uma homenagem a Dinorah junto ao espaço dos trabalhadores. Damião e o padre seguem na reconstrução; ela não reaparece em retratos, mensagens novas ou conversas de presente.

### Estado da igreja

**Preservada:** a igreja volta a receber a comunidade depois que o bairro é liberado. Sua fachada permanece inteira na imagem final.

**Destruída:** os sobreviventes se reúnem diante dos escombros e começam a organizar a reconstrução. Não há restauração instantânea nem mudança retroativa para uma igreja apenas levemente danificada.

**Padre, se a igreja foi preservada:** “A igreja continua de pé. Agora precisamos fazer o bairro voltar a viver.”

**Padre, se a igreja foi destruída:** “Vamos levantar essas paredes de novo. Primeiro, cuidar de quem voltou.”

### Resultado do resgate

**Evacuação completa:** o retorno confirma que todas as pessoas retiradas da igreja foram salvas no resgate. Não se deve sugerir ausência de perdas em toda a guerra, nem usar essa fala para negar a eventual morte posterior de Dinorah.

**Evacuação parcial:** o retorno inclui a lembrança das vítimas do pátio do galpão. Os sobreviventes e as famílias que perderam pessoas participam da reconstrução. A morte do chefe não apaga esse resultado.

**Damião, se todos foram resgatados:** “Todo mundo que saiu daquela igreja conseguiu voltar. Já valeu a luta.”

**Damião, se houve perdas:** “A gente venceu. Mas ainda vai faltar gente quando chamarem os nomes.”

A conclusão usa o encerramento de Dinorah e acrescenta as falas de igreja e resgate correspondentes. Os três resultados devem se somar; um não substitui o outro.

## Quadro de impactos

| Estado | Quando é definido | Impacto jogável | Impacto nas conversas | Impacto no epílogo |
|---|---|---|---|---|
| Igreja preservada | Fase 1 sem bomba | 2A com circulação livre de escombros | Padre agradece pela preservação; lembrança no retorno | Fachada inteira e retomada do espaço |
| Igreja destruída | Fase 1 com bomba | 2B com destroços e desvios | Padre lamenta; Damião prioriza vidas | Ruínas e início da reconstrução |
| Evacuação completa | Santa protegida por 2 minutos na fase 5 | 6A com escolta simples | Alívio na 6A, confirmação na 7 e no retorno | Todos os civis daquela retirada sobrevivem |
| Evacuação parcial | Objetivo destruído na fase 5 | 6B com escolta, portões e válvulas | Luto na 6B, lembrança na 7 e no retorno | Homenagem às vítimas e famílias com ausências |
| Dinorah viva | Escolta concluída na fase 12 | 13A com 30 eliminações; demais objetivos finais iguais | Participa das fases 14, 15 e 16 e do encerramento | Reconstrução e parceria com Damião |
| Dinorah morta | Falha da escolta na fase 12 com Damião vivo | 13B com 45 eliminações; demais objetivos finais iguais | Somente Damião e padre como aliados nas fases finais | Homenagem a Dinorah e luto preservado |

### Oito combinações de encerramento

| Igreja | Resgate | Dinorah | Composição do encerramento |
|---|---|---|---|
| Preservada | Completo | Viva | Igreja inteira, civis salvos e parceria na reconstrução |
| Preservada | Completo | Morta | Igreja inteira, civis salvos e homenagem a Dinorah |
| Preservada | Parcial | Viva | Igreja inteira, memória das vítimas civis e Dinorah na reconstrução |
| Preservada | Parcial | Morta | Igreja inteira, memória das vítimas civis e homenagem a Dinorah |
| Destruída | Completo | Viva | Reconstrução da igreja, civis salvos e parceria com Dinorah |
| Destruída | Completo | Morta | Reconstrução da igreja, civis salvos e homenagem a Dinorah |
| Destruída | Parcial | Viva | Reconstrução da igreja, memória das vítimas civis e Dinorah presente |
| Destruída | Parcial | Morta | Reconstrução da igreja e memória das vítimas civis e de Dinorah |

São oito combinações de cenas e falas do mesmo desfecho regional. Não exigem oito fases finais ou oito chefes diferentes.

## Regras de continuidade

1. A santa sai da igreja antes que uma bomba possa destruí-la. Ela continua disponível na fase 5 depois de 2A ou 2B.
2. A fase 1 salva todos da igreja nas duas rotas. A bomba altera o prédio e o pátio; as mortes civis são consequência da fase 5.
3. O primeiro grupo já embarcou antes de começar a defesa da santa. Qualquer falha nessa defesa ainda permite um resgate parcial, sem contradizer a cena da 6B.
4. Dinorah participa da operação depois de 6A e de 6B. O resultado do resgate não determina sua morte, partida ou ausência posterior.
5. Até a fase 12, Dinorah precisa estar viva para prosseguir. Morrer nas escoltas da fase 6 reinicia a missão.
6. Na fase 12, somente a morte de Dinorah com Damião vivo leva à 13B. A morte de Damião sempre tem prioridade de derrota e reinício.
7. Depois da 13A, Dinorah participa de todas as conversas das fases 14, 15 e 16, com trabalho concreto na preparação e no comando da ignição. Depois da 13B, as conversas seguem entre Damião e o padre, sem substituto novo.
8. Dinorah aguarda em posição protegida após a escolta bem-sucedida. As fases 13A a 16 não acrescentam outra condição de morte dela.
9. O padre fala pelo rádio após acompanhar a evacuação. Conferir o perímetro significa coordenar a rede de resistência, sem exigir sua presença física junto a Damião.
10. Os ovos destruídos na fábrica não reaparecem. A fábrica reativada atrai insetos para um novo ninho, criando uma distração temporária.
11. Na fase 14, ligar a energia prepara os sistemas. A ignição começa na 15 e termina antes de Escorpião aparecer na 16.
12. As falhas da fase 5 e da fase 12 têm continuação narrativa. As demais falhas de missão reiniciam a fase. Os três resultados são reiniciados ao começar uma nova campanha.
13. Nenhuma convergência de rota apaga o estado da igreja, as perdas civis ou a morte de Dinorah. O epílogo combina os três estados.
14. A libertação é regional e acontece após a destruição dos criadouros e a limpeza dos focos restantes. Não depende de uma eliminação instantânea de todos os insetos do planeta.

## Adaptação ao jogo

### Mudanças no fluxo e nos objetivos

| Área | Adaptação necessária |
|---|---|
| Grafo | Unificar 10A e 10B na fase 10; manter as bifurcações 2A/2B, 6A/6B e 13A/13B, com 19 nós no total |
| Condições | Manter bomba na fase 1 e falha de proteção na 5; substituir o tempo da fase 12 pelo resultado da escolta |
| Tempos e distâncias | Fase 1 com 90 s; fases 5 e 15 com 120 s; fases 3 e 9 com 2.560 px; fases 6A, 6B e 12 com 3.072 px |
| Objetivos compostos | Integrar transporte de cinco cargas na 7, alvos prioritários na 8, dez conjuntos de ovos na 10, válvulas na 11 e cinco máquinas na 14 |
| Falha da fase 12 | Interromper a escolta, apresentar a perda e continuar na 13B, com prioridade para a derrota se Damião também morrer |
| Conversas | Selecionar variantes por estado da campanha além de nó e momento da cena |
| Rádio final | Representar o enlace de controle, a sequência de ignição e seu progresso durante os 120 s |
| Encerramento | Compor imagens e falas dos três estados independentes |

A implementação atual do [grafo](../../src/levels/graph.c) ainda separa 10A/10B pelo dano na fase 9 e 13A/13B pelo tempo da fase 12. O [seletor de história](../../src/levels/story.c) consulta nó e momento; precisa receber as variantes de continuidade. As [missões experimentais](../fases-experimentais.md) oferecem referências de transporte, alvos prioritários, válvulas, energia, escolta e defesa de rádio; sua integração e adaptação à campanha continuam necessárias.

As contagens de 3 alvos prioritários na fase 8 e 3 válvulas na fase 11 são sugestões iniciais. Quantidade de barreiras na 6B, frequência de reforços, vida dos objetivos e padrões do chefe dependem de playtest. Os outros números de objetivo, durações e comprimentos seguem a estrutura da campanha.

### Conferência de narrativa e rotas na integração

- Percorrer as duas saídas da fase 1 e verificar o cenário da fase 2 e o estado da igreja no epílogo.
- Concluir e falhar a defesa da fase 5, inclusive logo no início, confirmando o primeiro embarque e as perdas somente na rota parcial.
- Verificar que Dinorah continua presente nas fases 7 a 12 depois de qualquer resultado do resgate.
- Testar reinício por morte de Dinorah na fase 6 e continuação pela 13B por morte dela na 12.
- Testar morte simultânea de Damião e Dinorah na fase 12, mantendo a derrota de Damião como prioridade.
- Conferir as versões com e sem Dinorah nas fases 14, 15, 16 e no encerramento.
- Confirmar que as cinco ativações de energia não iniciam o incêndio antes da fase 15 e que o rádio precisa sobreviver aos 120 s completos.
- Conferir as oito combinações de epílogo, preservando todos os resultados anteriores.
- Adaptar as falas aos limites de tela e conferir sua leitura no jogo; os avisos durante combate não devem ocultar ameaças ou exigir leitura longa.
