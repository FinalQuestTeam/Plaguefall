# Guia dos cenários e da narrativa ambiental

Os ambientes acompanham a passagem de uma comunidade em fuga para uma operação contra a base infestada. Cada cenário deve revelar quem usava o lugar, o que aconteceu e por onde seguir. A leitura principal precisa funcionar na tela pequena, antes dos detalhes de desgaste.

## Direção comum

Arquitetura do sertão brasileiro: reboco de cal, portas azuis, tijolo exposto, telha cerâmica e vegetação seca nas bordas externas. A tecnologia é industrial e remendada: encaixes reaproveitados, encanamento azul gasto, isoladores cerâmicos e recipientes de água. Carapaça, ovos e resina gradualmente ocupam essa infraestrutura.

As pranchas usam vista elevada aproximada de 60 graus acima do chão. O centro tem valores mais calmos e área livre; história e volumes ficam principalmente no perímetro. Na arte final, separar o piso caminhável da decoração e dos obstáculos que realmente receberão colisão.

## Leitura em três distâncias

1. **Forma grande:** igreja, galpão, plataforma, comporta ou ninho identifica o lugar.
2. **Vestígio principal:** telhas caídas, transmissor quebrado, carga aberta ou ovo dentro do duto explica o acontecimento.
3. **Detalhe próximo:** reboco recém-partido, ferramenta ausente ou marca de enchente reforça a leitura, sem carregar sozinho a informação.

## Continuidade entre cenários

- Banco, água, portão e telhado da igreja estabelecem um vocabulário no prólogo. O epílogo retoma essa linguagem com reparo e retorno. A fratura nova no reboco deve se distinguir do desgaste antigo.
- A santa já foi retirada nos cenários 2A/2B; os nichos ficam vazios. Ela acompanha o abrigo e torna-se o foco central da plataforma na 5.
- O resgate confirmado usa luz azul, rampa humana e marcas de embarque; a falha usa equipamento rompido e trilhas que deixam a plataforma por terra. Evitar objetos que sugiram a morte de Dinorah.
- Os encaixes de manutenção e o azul industrial repetem-se dos túneis à câmara final. Essa familiaridade torna críveis o conhecimento de Damião e a rota de fuga.
- A infestação começa como vestígio na rede, aparece dentro dos dutos, ocupa a carga e termina envolvendo vigas e câmaras inteiras. A estrutura humana continua identificável sob ela.
- Igreja preservada/danificada permanece independente do resgate. Um cenário comum não deve indicar a volta de Dinorah na rota em que ela partiu.
- Os suportes da fase 15 e da câmara 16 ficam vazios até a vitória contro Escorpião. A instalação das cargas é um acontecimento posterior.
- Os dois quadros do epílogo mostram a região já livre; o lado danificado representa reconstrução depois da libertação, e não uma região ainda infestada.

## Terrenos e contraste

| Tipo | Leitura visual | Distribuição de referência |
|---|---|---|
| Piso comum | Terra ou concreto de valor médio e textura contida | Centro e corredores legíveis |
| Lama | Marrom denso, borda irregular, sulcos e reflexo restrito | Superior direito e inferior esquerdo |
| Lava industrial | Laranja luminoso com borda escura e origem num tubo | Superior esquerdo e inferior direito |
| Ninho | Ovos oliva, resina e placas de carapaça | Perímetro; distinguir do piso de dano |

A referência lógica é src/levels/layouts.c. Nos terrenos simples, os pares ocupam dois retângulos; no misto, lama e lava ficam em cantos opostos. As pranchas orientam a composição e não reproduzem medidas exatas de colisão.

## O que cada fase conta

| Fase | Evidência que precisa sobreviver à simplificação | Terreno |
|---|---|---|
| [Prólogo e fase 1](imagens/01-patio-igreja.png) | A fila saiu por aqui: bancos viraram barricada, recipientes de água ficaram junto à porta e o caminho dos fundos permanece aberto. | Sem lama ou lava |
| [Fase 2A](imagens/02a-rua-servico-v2.png) | A igreja continua inteira; marcas ordenadas de passagem e espaços vazios dos suprimentos mostram uma evacuação concluída. | Sem lama ou lava |
| [Fase 2B](imagens/02b-igreja-danificada-v2.png) | Telhas e reboco recém-caídos identificam o dano da bomba; suprimentos presos sob a parede explicam a perda e o desvio. | Lama nos cantos superior direito e inferior esquerdo |
| [Fase 3](imagens/03-abrigo-manutencao.png) | Redes, biombos e uma farmácia improvisada mostram quem depende da defesa; o passado industrial continua perigoso. | Vazamento térmico nos cantos superior esquerdo e inferior direito |
| [Fase 4](imagens/04-tuneis.png) | A passagem foi limpa para outras pessoas cruzarem depois: tampas abertas, marcas de ferramentas e uma rota seca ligam entrada e saída. | Lama nos cantos superior direito e inferior esquerdo |
| [Fase 5](imagens/05-sinalizador-santa.png) | A santa retirada da igreja torna-se o centro da composição; os preparativos do embarque revelam a função do sinal. | Sem lama ou lava |
| [Fase 6A](imagens/06a-resgate-v2.png) | Marcas de embarque, a rampa recolhendo e o sinal confirmado contam que o povo conseguiu partir. | Vazamento térmico nos cantos superior esquerdo e inferior direito |
| [Fase 6B](imagens/06b-retirada.png) | O sinal quebrado e as bagagens arrastadas para longe do pouso mostram que o resgate falhou e a saída passou a ser por terra. | Vazamento térmico nos cantos superior esquerdo e inferior direito |
| [Fase 7](imagens/07-antenas.png) | Rastros orgânicos seguem os mesmos cabos que antes ligavam a comunidade à base; a infraestrutura revela o rumo da investigação. | Lama nos cantos superior direito e inferior esquerdo |
| [Fase 8](imagens/08-fornalha.png) | O jogador vê pela primeira vez como a máquina virou criadouro: ovos crescem no calor e na água dos dutos. | Vazamento térmico nos cantos superior esquerdo e inferior direito |
| [Fase 9](imagens/09-alfandega.png) | Caixas de carga abertas por dentro e equipamentos humanos incorporados à defesa mostram a origem e a adaptação da infestação. | Sem lama ou lava |
| [Fase 10A](imagens/10a-acesso-tecnicos.png) | Armários e ferramentas identificam a antiga vida de Damião; a rota humana de manutenção ainda permite atravessar a instalação. | Lama nos cantos superior direito e inferior esquerdo |
| [Fase 10B](imagens/10b-dreno-termico.png) | Níveis antigos de enchente, grades arrebentadas e calor vazando mostram o custo do desvio sob a base. | Lava no superior esquerdo/inferior direito; lama nos cantos opostos |
| [Fase 11](imagens/11-deposito.png) | Cargas industriais, caixas ainda lacradas e alertas abandonados contam que havia recursos e conhecimento, mas as operações continuaram. | Lava no superior esquerdo/inferior direito; lama nos cantos opostos |
| [Fase 12](imagens/12-comporta.png) | A comporta em movimento e os sinais mecânicos de fechamento tornam a janela de tempo visível antes do desvio. | Lava no superior esquerdo/inferior direito; lama nos cantos opostos |
| [Fase 13A](imagens/13a-linha-quente.png) | A passagem ainda aberta e o metal em resfriamento registram que Damião chegou dentro da janela. | Vazamento térmico nos cantos superior esquerdo e inferior direito |
| [Fase 13B](imagens/13b-decantacao.png) | A comporta fechada aparece ao fundo; sedimento e ferrugem indicam a passagem mais lenta que precisou ser usada. | Lama nos cantos superior direito e inferior esquerdo |
| [Fase 14](imagens/14-patio-enxames.png) | A ocupação passa de manchas a arquitetura: carapaças usam aço e cabos para fechar a aproximação da câmara. | Lava no superior esquerdo/inferior direito; lama nos cantos opostos |
| [Fase 15](imagens/15-galerias.png) | Suportes e pontos de inspeção revelam onde as cargas poderão entrar; a saída pelos túneis continua reconhecível. | Lava no superior esquerdo/inferior direito; lama nos cantos opostos |
| [Fase 16](imagens/16-camara-escorpiao.png) | O ninho ocupa o coração da instalação; os acessos humanos sobreviventes tornam visível como Damião poderá destruí-lo. | Sem lama ou lava |
| [Epílogo e variantes da igreja](imagens/epilogo-retorno-igreja-v2.png) | O mesmo lugar do prólogo reaparece livre dos ninhos: a versão preservada recebe o retorno, e a versão danificada mostra reparos. | Sem lama ou lava |

## Elementos para uma biblioteca comum

| Conjunto | Peças principais | Função na história |
|---|---|---|
| Igreja e comunidade | Banco, nicho, janela azul, telhas, portão, água, cobertas, caixa de remédios | Abrigo, fuga, perda e reconstrução |
| Manutenção | Tampa de inspeção, válvula, flange, grade, painel de ferramentas, isolador | Trabalho de Damião e caminhos conhecidos |
| Resgate | Base da santa, sinalizador, luz de aproximação, barreira, rampa, bagagem | Espera, confirmação ou fracasso do embarque |
| Base de lançamento | Carga aberta, braço de inspeção, depósito, registro de risco, comporta | Origem da ocupação e responsabilidade humana |
| Ninhos | Ovo, resina, placa de carapaça, viga incorporada, bocal ocupado | Reprodução e domínio progressivo da infraestrutura |
| Desfecho | Suporte vazio, acesso lateral, andaime, telhas separadas, luz reaproveitada | Preparação da demolição, fuga e recuperação |

## Transformação em telas

Antes de pintar detalhes, redesenhar a planta de cada arena na mesma câmera e escala. Fixar uma arquitetura única da igreja para todas as aparições: as pranchas são estudos, não plantas intercambiáveis. Nas versões da igreja e da plataforma, reutilizar módulos e trocar as peças que carregam o resultado da história.

Separar chão repetível, paredes baixas, volumes do perímetro, vestígios narrativos e objetivos interativos. Banco, caixa de remédios, tampa de inspeção, sinalizador e suporte de carga precisam de silhuetas próprias. A sujeira miúda pode ser simplificada; a relação entre esses objetos e o lugar deve permanecer.

Ao adaptar para 320×224, primeiro conferir massas e contraste com os sprites. Reservar a linha superior para o HUD e evitar que o cenário esconda inimigos, tiros ou perigos. Converter para as restrições de tiles e paletas depois de aprovar a composição. Decoração desenhada não cria automaticamente obstáculos, animações, destruição ou cenas de embarque no jogo.
