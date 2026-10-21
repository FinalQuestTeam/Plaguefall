# Cenários, formatos de arena e trilha

## Estado desta entrega

A fase 1 está integrada à ROM como pátio de 512×384 pixels: cenário em tiles, câmera, HUD fixo, obstáculos físicos, colisão dos tiros, igreja preservada/danificada e saídas 2A/2B. A meta continua sendo derrotar 10 inimigos enquanto cobre a retirada. As pessoas em fuga são apresentadas no diálogo e nos vestígios do cenário; esta versão não adiciona NPCs de evacuação animados.

[Revisão visual e vídeo](../art/phase01-courtyard-v2/revisao.html) · [Pacote de arte e testes](../art/phase01-courtyard-v2/README.md).

A primeira fase foi aprovada em 21/10/2026. Os capítulos 2 a 6 foram produzidos em paralelo e também receberam aprovação explícita para integração, com sete mapas por incluírem 2A/2B e 6A/6B. Esses cenários estão ativos na campanha, cada um com mapa, limites, câmera e perigos próprios. [Revisão dos elementos](../art/phases02-06-v1/revisao.html). As músicas continuam associadas às 20 definições existentes.

A validação integrada foi concluída. Foram 42 partidas novas nos sete mapas, com 7 conclusões, 35 derrotas e nenhum tempo limite, além de 12 partidas de regressão da fase 1. Os 28 ensaios de carga somaram 8.400 quadros, mantendo 60 FPS NTSC / 50 FPS PAL; o maior uso de CPU no percentil 95 foi 76,12% em NTSC e 50,59% em PAL. Relatórios: [NTSC](../art/phases02-06-v1/validation/ntsc/report.json) e [PAL](../art/phases02-06-v1/validation/pal/report.json). Os registros de ROMs temporárias existentes nas pastas individuais descrevem ensaios anteriores de renderização e, nas revisões com lava ampliada, de dano e travessia; não equivalem aos resultados finais da campanha integrada.

## Distribuição musical ativa

Todas as faixas são as composições já existentes. A seleção permanente da campanha usa `MUSIC_selectTrack`; a audição na galeria continua restaurando o estado anterior. As curvas de ameaça continuam individuais. Na fase 1, a Ladainha acelera de 64 para 90 BPM entre um e quatro inimigos.

| Fase | Ambiente | Música | Motivo |
|---|---|---|---|
| 1 | Pátio da igreja | Ladainha de Ferro | Comunidade, fé e defesa da retirada |
| 2A | Rua de serviço | Ladainha de Ferro | Continuidade da igreja preservada |
| 2B | Igreja danificada / desvio | Entardecer | Peso da destruição e do desvio |
| 3 | Abrigo de manutenção | Entardecer | Fragilidade do abrigo improvisado |
| 4 | Túneis de manutenção | Breu | Investigação subterrânea |
| 5 | Sinalizador na santa | Ladainha de Ferro | Fé ligada à tecnologia e ao resgate |
| 6A | Resgate confirmado | Entardecer | Alívio e despedida dos refugiados |
| 6B | Retirada por terra | Breu | Falha do sinal e ruptura com Dinorah |
| 7 | Rede de antenas | Entardecer | Caminhada e descoberta da ligação com a base |
| 8 | Fornalha | Baião de Ferrugem | Calor, máquinas e avanço ofensivo |
| 9 | Alfândega | Breu | Descoberta da infestação nas cargas |
| 10A | Acesso dos técnicos | Baião de Ferrugem | Damião volta ao terreno conhecido |
| 10B | Dreno térmico | Breu | Custo do desvio sob a base |
| 11 | Depósito | Baião de Ferrugem | Avanço por equipamento e carga industrial |
| 12 | Comporta | Baião de Ferrugem | Pressão da janela de passagem |
| 13A | Linha quente | Baião de Ferrugem | Manter o impulso da passagem conquistada |
| 13B | Decantação | Breu | Lentidão, sujeira e isolamento |
| 14 | Pátio dos enxames | Breu | Domínio orgânico da instalação |
| 15 | Galerias dos ninhos | Baião de Ferrugem | Avanço final e preparação das cargas |
| 16 | Câmara do Escorpião | Breu | Ameaça da matriz; curva própria mais rápida |
| Desfecho | Depois da luta | Entardecer | Retorno à dimensão humana da vitória |

## Formatos integrados e próximas propostas

As fases 1 a 6 abaixo usam os cenários aprovados na campanha. As medidas das fases 7 em diante continuam como plantas propostas. A área navegável reserva espaço para volumes e bordas.

| Fases | Formato / estado | Dimensão de referência | Composição e percurso |
|---|---|---|---|
| 1 | Retângulo horizontal, integrado | 512×384 | Igreja ao norte, miolo livre e barricadas periféricas |
| 2A / 2B | Rua horizontal, integrada | 512×320 | Rua aberta / desvio entre escombros e lama |
| 3 | Praça do abrigo, integrada | 384×384 | Abrigo periférico e centro para defesa |
| 4 | Corredor de manutenção, integrado | 512×288 | Tubulação, acessos técnicos e trechos secos |
| 5 | Praça de defesa, integrada | 384×384 | Santa no centro, aproximações pelas bordas |
| 6A / 6B | Retângulo de embarque, integrado | 512×320 | Rampa e sinal confirmado / passagem por terra |
| 7 | Retângulo horizontal | 512×256 | Antenas e cabos indicam o percurso |
| 8 | Praça industrial | 384×384 | Fornalha e ovos nos dutos periféricos |
| 9 | Retângulo de carga | 512×256 | Pilhas de carga criam acessos legíveis |
| 10A | Corredor técnico | 512×224 | Ferramentas, armários e portas de serviço |
| 10B | Corredor vertical | 256×512 | Descida, marcas de cheia e vazamentos |
| 11 | Praça de depósito | 384×384 | Estoque e alertas abandonados nas bordas |
| 12 | Corredor de comporta | 512×224 | Mecanismo e janela de passagem à vista |
| 13A | Corredor horizontal | 512×224 | Linha quente aberta |
| 13B | Corredor vertical | 256×512 | Canal de sedimento e comporta fechada |
| 14 | Pátio amplo | 512×320 | Aproximações de enxames e estruturas incorporadas |
| 15 | Galeria horizontal | 512×256 | Pontos de inspeção e suportes para cargas |
| 16 | Arena do chefe | 384×320 | Ninho central, acesso às cargas e saída reconhecível |

As fases 1 a 6 compartilham uma janela circular de 64×32 tiles no VDP, com mapas próprios e tamanhos reais diferentes. A câmera respeita os limites de cada mundo; apenas as novas linhas expostas são transferidas. Cada arena carrega seus padrões e sua paleta. As plantas futuras exigirão os mesmos cuidados com limites, janela e colisões.

Para as fases futuras, cada aprovação deve mostrar composição em resolução nativa, atlas, obstáculos, áreas de dano, objetivo, percurso e evidência ambiental principal. A integração acompanha a aprovação explícita dos elementos e a medição no emulador para a carga daquela fase.

## Integração dos capítulos 2 a 6

As áreas navegáveis medem 480×208 nas ruas e plataformas, 352×272 nas praças e 480×192 nos túneis. Os perigos ficam nos extremos, com rota seca contínua para a base física de 16×16 do personagem. A fase 5 preserva o objetivo de proteger a Santa por 30 segundos; as demais preservam suas metas de abates e músicas. Arquitetura e bagagens permanecem no perímetro. As fases 2B e 4 usam as áreas de lama da planta, aplicando a lentidão existente ao jogador e aos inimigos.

A exportação usa uma paleta de 16 cores por cenário, tiles de 8×8 deduplicados sem substituição aproximada, mapas compactos e cópias de 64×48 para o anel do VDP. Os recursos ativos da campanha derivam desses pacotes. A revisão mantém os limites, perigos, vestígios narrativos e módulos para consulta.

Na fase 5, a Santa já está desenhada no mapa. A entidade protegida usa contato lógico de 40×40 em (176,200), centro em (196,220), sem desenhar outra Santa por cima. A pedra física de 40×16 em (176,208) bloqueia os pés e deixa passar os tiros. O toque exato nas bordas também atinge o objetivo, permitindo que inimigos vindos dos lados causem dano sem atravessar a pedra. Um sinal de 8×8 pisca em (192,200), e o HUD continua mostrando a vida. Cada acerto causa 12 pontos, recuo, onda de choque e 2,5 segundos de invulnerabilidade; essa duração permite tanto resgate confirmado em 6A quanto falha em 6B dentro da defesa de 30 segundos. Os NPCs legados conservam 24×24 e 5 segundos de invulnerabilidade.

## Lava integrada e histórico de revisão

Após a revisão visual, os campos quentes passaram a ocupar33,02% do piso na3 e36,92% na6A/6B. A arte e as caixas de dano são coincidentes. Módulos de líquido e borda substituem as pequenas manchas decorativas; as duas zonas em cantos opostos restringem o recuo e conservam um caminho seco. Os testes isolados habilitam LAVA_update original e verificam o dano, o fim do dano e uma travessia seca pelo controle. A galeria inclui o sprite32×48 de Damião para comparação de escala.

Na integração atual, o brilho lento da lava é feito por variações dos próprios tiles, com transferências parceladas ao VDP. A paleta compartilhada permanece estável durante esse efeito: chão, paredes, personagens e HUD não mudam de cor junto com a lava. As caixas de dano mantêm as dimensões aprovadas.

A bateria integrada também verificou dano e reinício da lava, passagem seca, lentidão da lama, colisões, pausa, fonte e HUD, brilho restrito aos tiles de lava e as rotas da defesa da Santa. Os resultados dos dois relatórios finais correspondem aos hashes atuais da ROM e dos recursos.
