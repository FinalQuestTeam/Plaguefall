# Guia das imagens da fase 3

Especificação de arte de 25 de outubro de 2026 para a rua entre a igreja e o galpão. A fase terá três tipos de trecho: início, rua repetível e chegada. Este guia orienta a criação das imagens e sua revisão antes da integração ao jogo.

Damião vai à frente para abrir caminho; o padre acompanha o povo depois. O objetivo permanece alcançar o galpão, em um percurso de 2560 pixels. A decoração deve caracterizar uma rua de bairro do sertão industrial e oferecer desvios legíveis durante o combate.

[Primeira proposta visual para avaliação](../../art/phase03-three-segments-v1/review.html): panorama, trechos, emendas, objetos e comparação com a paleta da primeira fase. A proposta visual foi integrada; consulte a [versão nativa e os testes](../../art/phase03-three-segments-v1/integration-v1/review.html).

## Sequência dos três trechos

| Imagem | Tamanho nativo | Posição na fase | Função |
|---|---|---|---|
| A Início na igreja | 512×320 px | x 0 a 511 | Reconhecer a igreja e entender a saída do pátio para a rua. |
| B Rua repetível | 512×320 px | x 512 a 1023, 1024 a 1535 e 1536 a 2047 | Sustentar a travessia com muros, fachadas, calçadas e pista contínuos. |
| C Chegada ao galpão | 512×320 px | x 2048 a 2559 | Revelar o abrigo e conduzir ao ponto de chegada. |

Montagem: **A → B → B → B → C**. O início terá versões com a igreja intacta e destruída; ambas usam o mesmo enquadramento e encaixe. Portanto, são três tipos de trecho, quatro imagens de base e uma folha separada de objetos.

## Estilo e referências

A referência principal é a arte nativa das primeiras fases: pixel art, câmera ortográfica elevada próxima de 60° acima do chão, telhas de barro, reboco gasto, metal envelhecido e tecnologia incorporada ao ambiente brasileiro. Materiais, luz e escala devem formar um único bairro.

| Referência existente | O que preservar |
|---|---|
| [Pátio da igreja](../../art/phase01-pattern-v1/complete-native.png) | Identidade da igreja, telhado, fachada, porta azul, desgaste e relação com o pátio. |
| [Igreja como módulo de 200×112](../../art/phase01-pattern-v1/modules/church.png) | Silhueta completa e resolução nativa. Não redimensionar para caber no início. |
| [Igreja destruída](../../art/phase01-pattern-v1/damaged-native.png) | Continuidade da consequência da bomba na fase 1. |
| [Interior do galpão](../../art/campaign-pattern-v2/early/04-warehouse/map-native.png) | Estrutura industrial, materiais, pórtico e relação da entrada com a fase 4. |
| [Entrada existente do galpão](../../art/campaign-pattern-v2/early/03-street/modules/warehouse-entrance-whole.png) | Vocabulário do portão e dos batentes. É uma referência de identidade, não um recorte para colar com seu antigo fundo. |
| [Veículo existente](../../art/campaign-pattern-v2/early/03-street/modules/van-whole.png) | Escala inicial de 72×40 px, perspectiva e desgaste. |
| [Guidebook da campanha](guia-producao-visual-fases.md) | Objetivo da fase 3, personagens, materiais e continuidade narrativa. |

Manter Damião em 32×48 como régua de comparação durante a montagem. Casas devem ter telhado, fachada, portas e base conectados. O desenho das portas precisa seguir a projeção das referências; a célula inteira do personagem não representa a altura visível de uma porta nessa câmera.

A rua precisa se distinguir do pátio por calçada, meio-fio, sarjeta e piso de circulação. Escolher uma família coerente de pavimento gasto, compatível com a paleta existente; evitar uma superfície ocre uniforme em toda a fase. O chão terá menos contraste que personagens e obstáculos. As sombras seguem a direção da igreja de referência.

## Composição comum aos três trechos

Cada imagem cobre toda a altura de 320 pixels, com as seguintes funções:

- **Área superior:** arquitetura, fundos dos lotes, vegetação e limites físicos reconhecíveis.
- **Campo de circulação:** pista, calçada acessível e objetos que produzem desvios.
- **Área inferior:** meio-fio, muro baixo ou borda de lote que explique o limite do percurso.
- **Extremidades:** entrada ou saída contínua. Só o início absoluto e o fim absoluto podem ter fechamento lateral; os módulos intermediários não recebem paredes verticais nas emendas.

Essas áreas não obrigam a desenhar faixas retas e uniformes. Fachadas podem ter recuos e pequenas entradas, desde que o perfil nas bordas dos módulos permaneça compatível. A geometria do campo deve variar principalmente pela distribuição dos objetos.

Desenhar construções e objetos como peças completas. A montagem não deve conter retângulos de fundo antigo, fragmentos de telhado, paredes soltas, bases flutuantes ou sombras cortadas. Uma construção sair naturalmente pela lateral da câmera durante a rolagem é diferente de uma peça já nascer cortada na imagem de origem.

## Imagem A Início na igreja

A igreja deve ser o primeiro marco reconhecível. A composição mostra a ligação entre o pátio e a rua à direita, com mudança de piso e continuidade dos limites. A entrada do personagem fica em espaço seguro, com direção de avanço clara e margem para esquiva.

Reutilizar o corpo completo da igreja na escala nativa. Posicionar o telhado abaixo da área coberta pelo HUD no enquadramento de apresentação. Reservar espaço entre a igreja e a saída do módulo para a transição do piso; evitar ligar o portão diretamente a uma emenda sem área de aproximação.

**Versão intacta:** a igreja conserva a aparência das fases 1 e 2A. Pertences da evacuação podem sugerir a retirada, usando poucos objetos existentes.

**Versão destruída:** alterar a igreja e os destroços locais conforme a fase 2B. Rua, luz, escala e perfil de saída permanecem iguais. Se o entulho modificar o caminho, declarar a colisão dessa variante e conservar uma passagem acessível.

O trecho termina em uma parte simples de muro, calçada e pista, seguindo o encaixe definido para B. A igreja não se repete nos trechos centrais.

## Imagem B Rua repetível

O lado direito deve encaixar no lado esquerdo da própria imagem. Usar uma sequência de muros e uma ou duas fachadas discretas, com construções inteiras dentro do módulo. Um portão residencial, uma janela ou um recuo pequeno ajudam a caracterizar o bairro sem criar um novo marco único em cada repetição.

O módulo base inclui arquitetura e piso. Carros, postes, caçambas e montes grandes de entulho ficam na folha de objetos, para que as três instâncias de B recebam distribuições diferentes.

Nas zonas de emenda, usar materiais simples: reboco, muro, calçada e pista. Manter portas, janelas, postes, carros e extremidades de telhados fora dessas zonas. Uma mancha muito particular, um número de casa ou uma placa chamativa denunciaria a repetição; reservar sinais únicos para A e C.

### Regras de encaixe

1. Definir uma faixa de conexão de **32 px em cada extremidade** de B. A saída de A e a entrada de C usam o mesmo perfil.
2. A borda de saída continua a borda de entrada em cada altura: piso, linha da sarjeta, altura do meio-fio, parede e sombra. Não basta aproximar as cores.
3. Texturas devem manter a cadência através da emenda. Não é necessário duplicar a mesma coluna de pixels nos dois lados, pois isso pode engrossar linhas.
4. O encontro dos módulos não recebe margem transparente, linha de contorno vertical ou sombra que pareça uma parede.
5. Conferir **A/B, B/B e B/C**, em montagem contínua e no tamanho nativo.
6. Repetir B sem espelhar ou girar o trecho inteiro. Essas operações inverteriam luz, portas e perspectiva.

As faixas de 32 px são uma proteção para composição e revisão, não uma sobreposição: cada imagem contribui com seus 512 pixels, sem somar ou subtrair comprimento.

## Imagem C Chegada ao galpão

A entrada começa com o mesmo perfil de rua de B. O galpão surge como marco distinto, com estrutura completa, portão e base apoiados no chão. Materiais e abertura devem corresponder ao espaço que será visto na fase 4.

Deixar um pequeno espaço de aproximação livre diante da entrada. Os últimos obstáculos diminuem de densidade para que o jogador reconheça o destino e alcance o ponto de chegada sem ficar preso entre destroços.

A silhueta principal e o acesso precisam caber no enquadramento de apresentação de 320×224, considerando o HUD. Se o galpão continuar além desse enquadramento, seus módulos adjacentes devem mostrar uma continuidade intencional; a imagem de origem terá a construção resolvida, sem cortes arbitrários no portão ou telhado.

O fechamento da fase fica depois da área de chegada ou na própria construção. Não colocar um muro invisível sobre pista que pareça continuar livre.

## Folha separada de objetos da rua

Os objetos serão peças reutilizáveis de cenário em tiles. Os PNGs de trabalho terão transparência fora da silhueta, com a sombra inteira e margem de corte. Não depender de sprites de hardware para cobrir a rua.

As caixas abaixo são referências iniciais de produção. Conferir cada uma junto de Damião e das construções antes de fechar a folha.

| Objeto | Caixa inicial | Função visual e de percurso | Colisão proposta |
|---|---|---|---|
| Carro ou utilitário abandonado | 72×40 ou 80×48 px | Principal obstáculo baixo; gera um desvio perceptível. | Base sólida para pés e bloqueio de tiros conforme o volume fechado. |
| Poste simples | 16×64 ou 16×80 px | Ritmo e escala da rua; manter a luminária e a base inteiras. | Somente a base bloqueia pés. Sem bloqueio de tiros nesta proposta. |
| Monte de destroços | 48×32 px | Estreitar um lado da pista, com silhueta baixa clara. | Núcleo sólido para pés; não bloquear tiros acima do entulho baixo. |
| Fragmentos pequenos | 16×16 ou 24×16 px | Desgaste e ligação do objeto com o chão. | Sem colisão. |
| Caixotes ou caçamba | 32×32 ou 48×40 px | Complementar um veículo ou lote, sem ocupar todo o centro. | Base sólida; bloqueio de tiros apenas quando a forma indicar altura suficiente. |

Cada peça terá ponto de apoio, sombra, caixa de colisão dos pés e indicação de bloqueio de tiros separados. A colisão não inclui a sombra nem toda a caixa transparente do PNG. A versão visual e a geometria precisam ser conferidas juntas no motor.

### Distribuição nas três repetições

| Instância | Composição proposta |
|---|---|
| B1 | Veículo junto ao lado superior, poste na calçada e faixa inferior aberta para contornar. |
| B2 | Entulho junto ao lado inferior e poste em outra posição; passagem pelo centro e pela parte superior. |
| B3 | Reutilizar o veículo ou os caixotes em posição diferente, deixando a aproximação ao galpão visível. |

As posições serão ajustadas na revisão do panorama; não copiar o mesmo arranjo de objetos a cada 512 pixels. Manter a identidade dos materiais em todas as instâncias, sem mudanças aleatórias de cor para disfarçar a repetição.

O personagem usa uma base física de 16×16. Planejar passagens principais com **64 px livres quando possível** e não aceitar gargalos menores que **32 px** nesta proposta. Medir a abertura entre as colisões, não entre sombras. Preservar áreas de combate e esquiva entre obstáculos; a rua não deve virar um zigue-zague estreito obrigatório.

## Arquivos previstos e tamanho de trabalho

| Arquivo futuro | Conteúdo |
|---|---|
| `01-inicio-igreja-inteira.png` | A com igreja intacta, 512×320. |
| `01-inicio-igreja-destruida.png` | Variante narrativa de A, 512×320. |
| `02-rua-repetivel.png` | B sem os obstáculos independentes, 512×320. |
| `03-chegada-galpao.png` | C com a aproximação e o destino, 512×320. |
| `04-objetos-rua.png` | Folha com objetos completos e separados por margem transparente. |
| `05-panorama-intacto.png` | A+B+B+B+C com os objetos distribuídos, 2560×320. |
| `05-panorama-destruido.png` | Mesma montagem com a variante destruída de A, 2560×320. |
| `06-colisoes.png` | Bases sólidas, passagem contínua, ponto inicial e chegada sobre o panorama. |

Os nomes identificam as entregas futuras; este guia não cria essas imagens. Ilustrações de trabalho em resolução maior devem manter a mesma proporção e ser avaliadas depois em resolução nativa. Ampliações de revisão usam vizinho mais próximo; não aplicar desfoque para esconder emendas.

## Paleta e orçamento de memória

A arte final do cenário deve usar a **PAL3 existente, com 16 entradas RGB333**, preservando as reservas dos personagens, inimigos, efeitos e HUD. A decisão sobre textura de rua precisa funcionar nessa paleta antes de detalhar todo o panorama.

A reserva residente de cenário é de **640 tiles de 8×8, equivalentes a 20 KiB**. A implementação de 26/10 mantém os gráficos exatos na ROM e usa um cache da região visível. A janela máxima de 41×26 células abaixo do HUD exige no máximo 640 padrões distintos nos dois estados. Repetir B e os objetos não duplica seus padrões na VRAM quando estão no cache.

A meta inicial de um atlas completo com 608 tiles não foi atingida. O banco final tem 3070 padrões no estado intacto e 3086 no destruído, guardados na ROM; somente até 640 ficam visíveis de uma vez. Os estados são exclusivos. O cache consome 11.260/11.292 bytes de heap, liberados durante a pausa. Essa escolha conserva os pixels das construções e dos objetos.

Três imagens não garantem automaticamente baixo consumo. Telhas, reboco, piso e muros devem reutilizar padrões intencionais. Se o conjunto exceder o orçamento, simplificar materiais e detalhes secundários antes de comprometer a silhueta dos edifícios. Não substituir tiles por padrões apenas parecidos que produzam fragmentos ou manchas.

Os três módulos também podem permitir reduzir o mapa na ROM mediante consulta por trecho. Isso exige adaptação do renderizador: apenas repetir imagens na montagem não reduz automaticamente os dados do mapa exportado pelo caminho atual.

## Ordem de produção e revisão

1. Fixar a paleta, as referências da igreja e do galpão, a escala e o perfil das emendas.
2. Compor A, B e C inteiros. Construir o panorama A+B+B+B+C e conferir a leitura de rua antes de detalhar os objetos.
3. Revisar a repetição de B e os encontros A/B, B/B e B/C. Corrigir saltos de piso, altura, cor ou sombra.
4. Preparar os objetos separados, distribuir as três instâncias e desenhar as colisões correspondentes.
5. Produzir as duas versões do panorama, conferir construções completas e percurso contínuo.
6. Verificar os recortes de câmera; ajustar arquitetura e posições antes do empacotamento final.
7. Contar tiles e conferir a reconstrução exata da imagem nativa. Integrar à fase 3 depois da revisão visual do conjunto.
8. No jogo, verificar rolagem, colisão, chegada, leitura de combate e carga NTSC/PAL com os mesmos tetos de inimigos e tiros da fase. Comparar as capturas reais com o panorama revisado.

### Vistas obrigatórias para revisão

- Panorama completo de 2560×320, com e sem a camada de colisões, nas duas condições da igreja.
- Rua B repetida três vezes, primeiro sem objetos e depois com a distribuição proposta.
- Recortes de 320×224, com os 24 px superiores ocupados pelo HUD, percorrendo a rua a cada 160 px e incluindo x=2240 no fim.
- Recortes centrados nas emendas x=512, 1024, 1536 e 2048, além das vistas da igreja e do galpão.
- Enquadramentos verticais reais da câmera: o panorama tem 320 px de altura e a tela mostra 224. Conferir os limites de rolagem e os pontos de apresentação, sem pressupor que toda a altura cabe na tela ao mesmo tempo.

No enquadramento de apresentação de cada marco, seu telhado, fachada, base e acesso precisam estar legíveis, fora do HUD. Durante a movimentação, o recorte da câmera deve ser natural e não revelar bordas vazias, partes isoladas ou uma construção impossível de reconhecer.

## Critérios para aceitar as imagens

| Aspecto | Condição para seguir à integração |
|---|---|
| Identidade | Igreja reconhecível como a das primeiras fases; chegada coerente com o galpão da fase 4. |
| Rua | Calçada, sarjeta, pista e limites distinguíveis sem depender de texto explicativo. |
| Encaixe | A/B, B/B e B/C continuam sem linha vertical, degrau ou mudança de luz. |
| Construções | Telhados, aberturas, paredes e bases resolvidos; nenhum retângulo de fundo antigo colado sobre outro material. |
| Repetição | B funciona repetido; objetos e desvios diferenciam as três passagens. |
| Circulação | Início e chegada conectados, passagens medidas e margem de esquiva. |
| Colisão | Carros, postes e entulho colidem de acordo com sua base visível e função declarada. |
| Câmera | Igreja, obstáculos e galpão têm vistas legíveis; emendas permanecem estáveis durante a rolagem. |
| Memória | Máximo comprovado de 640 tiles visíveis por estado; cache com reserva fixa de 20 KiB de VRAM. |
| Arte nativa | Paleta e montagem preservadas na reconstrução dos tiles, sem suavização ou substituição aproximada. |

Reprovar qualquer panorama com casas fragmentadas, ruído atrás dos telhados, objetos flutuando, rua sem caracterização, repetição de obstáculos idêntica ou limite invisível sobre chão aparentemente livre. O orçamento de memória e os testes do motor não substituem a revisão visual da composição inteira.
