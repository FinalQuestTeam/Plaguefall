# Guia dos três blocos de cenário da fase 6

A fase 6 será composta por três tipos de imagem: entrada dos esgotos, galeria repetível e saída para o abrigo do Último Chão. A montagem proposta mantém os 3.072 pixels de deslocamento e a escolta de Dinorah. As variantes 6A e 6B compartilham a arquitetura; os mecanismos e a distribuição dos obstáculos distinguem os percursos.

[Representação visual dos três blocos](../../art/phase06-three-segments-v1/review.html): panorama completo, variação 6B, objetos, emendas e exploração de câmera.

Esta especificação orienta a nova composição. O cenário atualmente integrado permanece como referência de materiais e escala até a produção e revisão do novo panorama.

## Montagem dos blocos

| Bloco | Imagem base | Posição na fase | Função |
|---|---|---|---|
| A | Entrada dos esgotos, 512×320 px | x 0–511 | Ligar a retirada do galpão à passagem subterrânea e apresentar a escolta. |
| B | Galeria repetível, 512×320 px | x 512–1023, 1024–1535, 1536–2047 e 2048–2559 | Sustentar o deslocamento com materiais contínuos e diferentes desvios. |
| C | Saída para o abrigo, 512×320 px | x 2560–3071 | Mostrar o acesso à favela e oferecer uma chegada reconhecível. |

**Sequência: A → B1 → B2 → B3 → B4 → C.** B1 a B4 são instâncias da mesma imagem B, com objetos posicionados separadamente. O total é 512 + 4×512 + 512 = 3.072 px. As faixas de conexão não se sobrepõem nem alteram esse comprimento.

## Identidade visual e continuidade

Preservar a pixel art nativa, a projeção elevada das fases anteriores, a escala dos personagens e a direção das sombras. O lugar deve parecer infraestrutura de esgoto do mesmo bairro industrial: alvenaria gasta, concreto úmido, grades, tubulações envelhecidas e equipamentos de manutenção.

Usar como referências o [guia visual da campanha](guia-producao-visual-fases.md), a [composição atual da 6A](../../art/campaign-corridors-v3/corrections/6A-guidebook/revisions/01-crossing-context/complete-native.png), os módulos existentes de [6A](../../art/campaign-corridors-v3/corrections/6A-guidebook/modules/) e [6B](../../art/campaign-corridors-v3/corrections/6B-guidebook/modules/), e o [método dos três trechos da fase 3](guia-imagens-fase03.md).

O piso seco precisa se distinguir do canal por material, altura de borda e sombra. Água escura fica confinada ao canal; não usar grandes manchas soltas que pareçam buracos na área caminhável. O chão terá menos contraste que Damião, Dinorah, inimigos e mecanismos. Manter luz e paleta consistentes entre A, B e C, sem mudar as cores a cada repetição.

## Organização vertical comum

| Região proposta | Altura | Conteúdo |
|---|---|---|
| Superior | y 0–79 | Parede de contenção, arcos rasos, tubulações e fundos de manutenção. |
| Campo de deslocamento | y 80–271 | Passagem seca de 192 px de altura bruta, com desvios e áreas para defender Dinorah. |
| Inferior | y 272–319 | Canal de drenagem, borda e limite físico contínuo. |

Essas coordenadas preservam a faixa vertical de referência dos esgotos atuais. Recuos locais podem ocupar parte das faixas, desde que a rota continue legível. O canal permanece do mesmo lado em todas as emendas. Entrada e saída podem ter fechamentos laterais; B terá conexão aberta à esquerda e à direita.

Não criar uma parede horizontal no meio do caminho nem alternar arbitrariamente o canal entre cima e baixo. O desenho deve mostrar a passagem seca inteira, inclusive a parte próxima do limite inferior.

## Bloco A com a entrada dos esgotos

Desenhar uma escada de serviço inteira, ligada a um patamar seco e a um arco ou acesso de manutenção. Ela explica como Damião e Dinorah desceram do setor do galpão. O tratamento do metal e da alvenaria mantém a continuidade das fases 4 e 5; o galpão inteiro não reaparece debaixo da terra.

A escada é o marco único do início. Sua estrutura, apoio e desembarque precisam estar resolvidos na imagem. A entrada dos personagens terá espaço para ambos e para a primeira esquiva, antes de qualquer obstáculo importante. O movimento para a direita deve ser evidente pelo piso e pela continuidade da galeria.

Nos últimos 32 px, A adota exatamente o perfil de conexão de B. Não colocar um equipamento alto, a escada ou uma porta atravessando essa faixa.

## Bloco B com a galeria repetível

Desenhar uma passagem de serviço com parede superior de alvenaria, tubulação horizontal, piso seco e canal inferior contínuo. Arcos e suportes simples dão ritmo à infraestrutura. Equipamentos grandes, entulho e mecanismos ficam em peças separadas, permitindo mudar a circulação sem alterar o encaixe da base.

O lado direito de B deve continuar o lado esquerdo do próprio B. Reservar 32 px em cada borda para materiais simples e contínuos. A linha do canal, a borda seca, as juntas do piso, a tubulação e as sombras precisam atravessar a emenda na mesma altura e com a mesma cadência.

Manter portas, placas únicas, luminárias marcantes, bocais de vapor, pilares grandes e objetos inteiros fora dessas faixas. Não espelhar o bloco para variar a aparência: isso inverteria luz, projeção e tubulação. A variação virá dos objetos e das situações de escolta.

### Variação das quatro passagens

| Instância | Distribuição proposta | Efeito na escolta |
|---|---|---|
| B1 | Equipamento compacto junto ao lado superior; aproximação inferior aberta. | Primeiro desvio amplo e uma posição segura para esperar cobertura. |
| B2 | Entulho baixo próximo do lado inferior, deslocado em relação ao equipamento anterior. | Travessia pelo centro e pela parte superior, com espaço para reagrupar. |
| B3 | Reutilizar equipamento e caixas em posições diferentes, sem fechar a passagem. | Segundo momento de defesa, sem copiar o arranjo de B1. |
| B4 | Poucos objetos junto às bordas e eixo de aproximação mais aberto. | Revelar a saída e reduzir a chance de Dinorah se prender perto do destino. |

Manter pelo menos 64 px livres nas passagens principais entre colisões; buscar bolsões de 96–128 px para cobertura e reencontro. Damião e Dinorah usam bases físicas de 16×16. Um corredor que permite apenas passar em fila e sem desviar não serve como trecho normal de combate desta proposta.

## Bloco C com a saída para o abrigo

Desenhar um acesso de manutenção reforçado, com escada ascendente e porta ou grade de entrada para o setor do Último Chão. Esse conjunto é o marco do fim; a favela e o abrigo serão revelados na fase 7. Evitar colocar uma casa isolada diretamente no piso do esgoto.

A entrada de C usa o mesmo perfil de B. Na aproximação final, diminuir a densidade de obstáculos e deixar a rota dos dois personagens chegar ao patamar. A área de chegada coincide com um acesso visível; o fechamento lateral fica depois dela ou faz parte da construção.

A escada, porta, batentes e patamar devem formar uma estrutura completa. O enquadramento de apresentação precisa mostrar o acesso e seu apoio fora dos 24 px do HUD. Durante a rolagem, os recortes da câmera não podem revelar fundos vazios ou peças soltas.

## Diferenças entre 6A e 6B

Na **6A**, a evacuação completa conduz à travessia direta: obstáculos comuns e pontos de cobertura, com Dinorah indicando o caminho até os recursos da base. Não haverá portas fechadas ou válvulas desenhadas como objetivos obrigatórios nesta variante.

Na **6B**, as perdas civis permanecem na história e o ramal exige dois conjuntos de válvula e portão. Propor o primeiro dentro de B1 e o segundo dentro de B3, com todos os componentes afastados das emendas. Cada conjunto usa peças próprias sobre a mesma base de galeria; não vira um quarto tipo de bloco de 512 px.

Cada portão precisa de batentes e paredes ligados aos limites visíveis, de modo que a folha realmente feche a passagem. Depois de aberto, sobra um vão de pelo menos 64 px para a escolta. Posicionar a válvula antes do bloqueio, com seu lado de operação protegido e um bolsão para Dinorah esperar fora do vapor e da animação de queda.

Preservar os verbos já implementados: aliviar a pressão, atingir a folha com quatro tiros e aguardar sua queda para atravessar. Tubos e bocal devem explicar visualmente a ligação entre válvula, vapor e portão. Os estados fechado, aliviado, danificado, caindo e aberto serão avaliados sobre a mesma composição.

As posições atuais dos mecanismos e os pontos da escolta precisarão ser recalculados com o novo cenário; não copiar a rota antiga sobre obstáculos redistribuídos. Nas duas variantes, Dinorah deve chegar viva; sua morte aqui reinicia a fase. A bifurcação de sobrevivência permanente da personagem continua na fase 12.

## Peças de campo separadas

| Peça | Uso | Colisão |
|---|---|---|
| Bomba ou equipamento de manutenção completo | Desvio junto da parede, com base e tubos resolvidos. | Base bloqueia pés; partes altas bloqueiam tiros conforme o volume visível. |
| Caixas e ferramentas agrupadas | Cobertura secundária nas bordas. | Colisão apenas no volume apoiado no chão. |
| Entulho baixo | Desvio suave em outra instância de B. | Bloqueia pés no núcleo; tiros passam sobre a parte baixa. |
| Tubos e suportes de parede | Ritmo e identidade do esgoto. | Fora da passagem quando são apenas decoração. |
| Conjunto de pressão da 6B | Portão, batentes, válvula, bocal e indicação de perigo. | Folha dinâmica, estrutura permanente e área de vapor coerentes com a arte. |

Exportar as peças com transparência fora da silhueta, sombra inteira e âncora de apoio. Não incluir retângulos do piso de origem. Alinhar a montagem final à grade de 8 px quando isso conservar as formas e facilitar a reutilização dos tiles. A sombra não amplia automaticamente a colisão.

## Memória e produção nativa

O limite residente continua sendo 640 tiles, ou 20 KiB de VRAM para cenário e objetivos desse conjunto. Na 6B, os mecanismos existentes reservam 256 tiles; a base e os objetos estáticos devem caber nos 384 restantes. A meta para o kit comum é, portanto, até 384 tiles de cenário, validada depois da composição. A 6A atual usa 554 tiles e a 6B atual usa 368 de cenário mais 256 de objetivos; esses valores são referências da arte existente, não medições da proposta.

Repetir concreto, alvenaria e canal economiza padrões. Repetir a imagem B não garante sozinho o orçamento: novos detalhes e sobreposições podem gerar tiles adicionais. Contar o atlas completo, preservar a paleta nativa e conferir a reconstrução exata. Simplificar materiais secundários se necessário; não trocar tiles por padrões apenas parecidos.

Um mapa completo de 3072×320 com entradas de 16 bits ocupa 30.720 bytes na ROM. Repetir os módulos reaproveita gráficos, mas só reduzirá esses dados do mapa se a futura integração também consultar a composição por blocos. Não presumir essa otimização apenas pela existência de três PNGs. O cache de cenário da fase 3 não é uma exigência para esta proposta.

## Entregas e revisão do conjunto

1. Produzir A, B e C inteiros, na paleta e escala aprovadas, e uma folha de peças completas.
2. Montar A+B+B+B+B+C sem objetos e inspecionar a continuidade do piso, canal, paredes e tubulações nas cinco emendas.
3. Distribuir os objetos e montar os panoramas completos de 6A e 6B; incluir os dois conjuntos de pressão na 6B.
4. Sobrepor colisões, rota dos dois atores, pontos de espera, áreas de operação e chegada. Conferir passagens e acesso aos mecanismos nos estados aberto e fechado.
5. Revisar cada panorama inteiro e recortes de 320×224 a cada 160 px, incluindo as emendas, a entrada, a saída e os extremos verticais de câmera. Considerar o HUD e os dois personagens em escala nativa.
6. Empacotar os tiles e comparar a reconstrução com o panorama. Registrar separadamente cenário, mecanismos, dados de mapa e VRAM.
7. Na integração, testar escolta, espera, reagrupamento, colisão, mecanismos, chegada, pausa e rolagem contínua. Medir carga em NTSC/PAL com os limites atuais de três inimigos e quatro tiros por grupo, sem alterar o balanceamento para esconder problemas de desempenho.

Reprovar emendas com paredes verticais indevidas, tubos interrompidos, canal mudando de altura, fundos antigos colados, escadas cortadas na origem, colisões sem apoio visual ou obstáculos que prendam Dinorah. A revisão das imagens completas precede a substituição do cenário no jogo.
