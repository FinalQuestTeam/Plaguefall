# Campanha proposta e consequências das rotas

O novo fluxo liga a fuga da igreja, a tentativa de resgate e a destruição dos ninhos de São Jerônimo. Mantém os 20 nós e as 16 fases por partida do grafo atual. A versão extensa, com cenas e diálogos, está em [Fluxo proposto da história](tratamento-proposto.md). Os acontecimentos desta revisão ainda precisam ser adaptados ao roteiro da ROM.

## Progressão das fases

| Fase | Lugar e ação narrativa | Objetivo jogável atual | Consequência ou próximo passo |
|---|---|---|---|
| 1 | Pátio atrás da igreja; Damião protege a fuga organizada por Dinorah e pelo padre | Eliminar 10 | Sem bomba → igreja poupada, 2A; com bomba → destruição parcial, 2B |
| 2A | Rua de serviço; todos fugiram e os suprimentos foram retirados | Eliminar 12 | O grupo alcança o novo abrigo; confiança de Dinorah reforçada |
| 2B | Baixio; os destroços impedem o acesso direto | Eliminar 12, lama | O grupo alcança o novo abrigo; perda de materiais e discussão sobre a explosão |
| 3 | Pátio térmico do abrigo de manutenção; defender os acessos enquanto o padre procura um caminho | Eliminar 14, lava | Encontrar uma saída para a plataforma de evacuação |
| 4 | Túneis de manutenção; Damião vai na frente para abrir a passagem | Eliminar 16, lama | Os refugiados podem alcançar a plataforma |
| 5 | Plataforma; proteger o sinalizador escondido na santa | Proteger por 30 s | Sinal confirmado → 6A; sinalizador destruído → 6B |
| 6A | Perímetro de embarque; cobrir a partida das naves humanas de resgate | Eliminar 20, lava | Refugiados resgatados; Damião e Dinorah planejam investigar os ninhos |
| 6B | Corredor da retirada; cobrir a saída por terra após o resgate abortado | Eliminar 20, lava e spawn mais rápido | Dinorah briga com Damião, o padre tenta intervir e ela parte com os refugiados |
| 7 | Baixio das antenas; seguir os rastros que convergem para a base | Eliminar 22, lama e duplas | Na 6A, Dinorah ajuda; na 6B, Damião investiga com o padre no rádio |
| 8 | Fornalha; descobrir os ninhos nos sistemas de resfriamento | Eliminar 24, lava e duplas | Os dutos conectam os criadouros locais e oferecem um meio de destruí-los |
| 9 | Alfândega ocupada; romper a defesa das elites | Eliminar 24 | Sem perder HP → 10A; perdeu HP → 10B |
| 10A | Acesso dos técnicos; localizar o depósito industrial | Eliminar 26, lama | Chegar ao setor de demolição |
| 10B | Dreno térmico; entrar pelo subsolo e localizar o mesmo depósito | Eliminar 26, lava e lama | Chegar ao setor de demolição |
| 11 | Depósito; obter cargas e descobrir que os alertas foram ignorados pelo Consórcio | Eliminar 28, lava e lama | Preparar a demolição dos acessos que alimentam os ninhos |
| 12 | Comporta; romper o bloqueio antes do fechamento automático | Eliminar 30, lava e lama | Menos de 60 s → 13A; 60 s ou mais → 13B |
| 13A | Linha quente; aproveitar o acesso direto | Eliminar 34, lava | Alcançar as galerias |
| 13B | Decantação; contornar a comporta fechada | Eliminar 34, lama | Alcançar as mesmas galerias |
| 14 | Pátio dos enxames; enfrentar a concentração de defensores | Eliminar 37, lava e lama, trios | Identificar Lacraia como a matriz que bloqueia os pontos das cargas |
| 15 | Boca das galerias; romper o último bloqueio e confirmar a retirada dos refugiados | Eliminar 40, lava e lama, trios | Conferir explosivos e rota de saída de Damião |
| 16 | Câmara central; derrotar Lacraia para conseguir instalar as cargas nos ninhos | Derrotar o chefe, piso de caverna | Cena de instalação das cargas, fuga e detonação |

## Estados que permanecem após as convergências

O resultado da igreja e o resultado do resgate são independentes. Há quatro combinações de resultados: igreja poupada e resgate realizado; igreja danificada e resgate realizado; igreja poupada e resgate falho; igreja danificada e resgate falho. A mesma bifurcação 6A/6B pode acontecer depois de qualquer versão da fase 2.

O estado da igreja aparece nas falas sobre recursos do abrigo, nas lembranças da explosão, no cuidado ao preparar as cargas e na imagem final. A santa foi retirada pelo padre durante a fuga inicial; sua presença na fase 5 não depende de a igreja permanecer intacta.

O resultado do resgate determina quem acompanha a investigação. Em 6A, Dinorah permanece e colabora por rádio. Em 6B, ela parte com o povo, e o padre mantém Damião informado durante a retirada. As fases comuns precisam de falas que respeitem essa ausência. O êxito final não provoca uma reconciliação automática.

Dano na fase 9 e tempo na fase 12 alteram a aproximação da base. Não curam a relação entre os personagens nem mudam o resgate já ocorrido. A janela de 60 segundos da comporta deve ser comunicada antes da fase 12.

## Encerramento comum e diferenças do percurso

Lacraia precisa cair para Damião alcançar os pontos de instalação. Em seguida, ele coloca as cargas recuperadas na base, sai pelo túnel e detona os ninhos. As cargas fazem parte da missão e não dependem do estoque de bombas do jogador.

Uma passagem de alguns dias mostra a eliminação dos insetos isolados e confirma a libertação da região. O planeta continua ocupado, com pedidos de ajuda chegando pelo rádio.

Na rota 6A, o povo retorna do posto de resgate e Dinorah participa dos preparativos com Damião. Na 6B, a caravana chega por terra e o afastamento de Dinorah permanece. A igreja aparece inteira ou parcialmente destruída conforme o resultado da fase 1. Todos os percursos terminam com São Jerônimo livre.

## Correspondência com a implementação atual

O [levantamento das fases](auditoria-fases.md) registra os objetivos e as condições já implementados. A defesa da fase 3 continua representada pela eliminação dos inimigos nos acessos; não pressupõe um segundo NPC para proteger. Resgate, dano à igreja, aquisição das cargas e demolição são acontecimentos para as cenas da nova versão.

O seletor atual usa nó e momento, sem variar cenas comuns por resultados anteriores. Será necessário consultar as rotas visitadas ou registrar os dois estados narrativos e selecionar suas versões de diálogo. A fase 7 atual faz Dinorah falar incondicionalmente e deverá ser adaptada.

A queda da santa na fase 5 está bloqueada pelos valores atuais de vida e invulnerabilidade. A rota 6B precisa de ajuste de balanceamento para ser alcançável. Uma cena DEPOIS da fase 5 deve tratar separadamente sucesso e falha, pois ambos passam por esse momento do fluxo.
