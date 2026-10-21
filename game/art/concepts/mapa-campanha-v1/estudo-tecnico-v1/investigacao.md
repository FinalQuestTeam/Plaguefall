# Investigação — mapa ilustrado no Mega Drive

Data: 21/10/2026. Escopo: leitura de código, consulta à documentação do SGDK e provas de conversão fora do jogo. Nenhuma implementação na ROM.

## Parecer

A ideia é viável. O concept atual funciona como direção de atmosfera e narrativa, mas sua composição precisa mudar para a resolução do jogo. O problema dominante é a quantidade de informação disputando os mesmos pixels. Mais memória ou mais cores não recuperam um prédio que ficou com poucos pixels de largura.

Recomendo **quatro mapas regionais de 320 × 160**, mostrados dentro da tela de 320 × 224. Cada um recebe uma das quatro bifurcações e de quatro a seis locais principais, com um esquema pequeno do caminho completo para situar a região. A arte deve ser desenhada para essa escala, com marcos grandes, terreno simples e espaço reservado às rotas. Os recortes desta investigação demonstram escala e cor; não são a arte regional final.

O panorama inteiro fica como referência de produção. Para o jogador, preservar os detalhes que identificam cada lugar — igreja, nave de resgate, antena, comporta, entrada dos ninhos — e retirar o excesso de pedras, cabos finos, telhas e brilhos isolados.

## O que foi medido

As provas usam a paisagem original sem os textos da prancha. Reutilizam a função de paleta do exportador do título, em RGB333: 8 níveis por componente, 15 cores opacas mais a entrada zero em cada banco. Cada célula de 8 × 8 usa **um único banco de paleta**. Depois, os pixels são empacotados em 4bpp e decodificados para conferir o resultado. Tiles iguais, incluindo espelhamentos, podem ser reutilizados sem alterar os pixels.

Não houve dithering adicional, substituição aproximada de tiles, pintura nova ou execução em emulador. O aspecto pontilhado das provas vem também da textura da própria imagem original. O RGB apresentado é uma aproximação digital dos valores RGB333; não simula sinal composto, CRT, overscan nem diferenças de console.

| Prova | Pixels de arte | Bancos | Tiles únicos | Padrões na VRAM | Recurso bruto¹ |
|---|---:|---:|---:|---:|---:|
| Mapa inteiro reduzido | 320 × 160 | 2 | 800 | 25.600 B | 27.264 B |
| Trecho da base ampliado | 320 × 160 | 2 | 800 | 25.600 B | 27.264 B |
| Mesmo trecho, mais cores | 320 × 160 | 3 | 800 | 25.600 B | 27.296 B |
| Panorama mais largo | 512 × 160 | 2 | 1.280 | 40.960 B | 43.584 B |
| Panorama mais largo | 640 × 160 | 2 | 1.600 | 51.200 B | 54.464 B |

¹ Padrões + tilemap compacto em ROM + paletas. Não inclui interface, marcadores, tabelas de posição, alinhamento ou padding da ROM. O tilemap compacto de 320 × 160 tem 1.600 bytes; o plano de hardware continua reservado separadamente na VRAM.

Nesta pintura todos os tiles das cinco provas são distintos, mesmo admitindo espelhamento. Logo, não há ganho de deduplicação. Textura espalhada por toda a superfície tem custo alto; módulos de chão e telhado reaproveitáveis oferecem uma economia real numa arte preparada para tiles.

A terceira paleta reduziu o erro RGB médio do recorte de 11,710 para 11,659 neste quantizador. As paletas automáticas apresentam cores repetidas entre bancos: 21 cores opacas distintas no recorte de dois bancos e 24 no de três. Isso não é o limite do hardware: dois bancos permitem até 30 cores opacas distintas e três até 45. Uma paleta desenhada por material pode usar melhor os bancos. **O teste mostra que acrescentar um banco automaticamente não resolve a densidade; não prova que três paletas seriam inúteis numa arte redesenhada.**

O erro RGB mede aproximação de cor; não mede reconhecimento de edifícios ou facilidade de encontrar a rota. A visão geral tem erro numérico ligeiramente menor e, mesmo assim, é menos útil para reconhecer os lugares.

Arquivos: `comparativo-tecnico.png`, prévias PNG em escala nativa, `medicoes.json` e `medir.py`. Reproduzir com `python3 game/art/concepts/mapa-campanha-v1/estudo-tecnico-v1/medir.py`. O script escreve somente nesta pasta.

## Limites concretos deste projeto

| Item | Situação conferida | Consequência para o mapa |
|---|---|---|
| Resolução | Inicialização do SGDK em 320 × 224; o jogo usa essa configuração | Projetar e revisar em tamanho nativo desde o início |
| Célula gráfica | 8 × 8, 4bpp, 32 B por padrão | Uma célula seleciona um banco inteiro; uma imagem apenas reduzida a 32 cores pode continuar incompatível |
| Cores | 4 bancos de 16 entradas; RGB333; índice zero transparente nos planos/sprites | Reservar as cores de texto, rotas e ponteiro; validar os bancos por célula |
| VRAM padrão local | Dados de padrões até 0xBFFF: 48 KiB, 1.536 posições de tile. Planos/tabelas a partir de 0xC000 | Não considerar os 64 KiB inteiros como espaço livre para arte |
| Fonte nesta cópia do SDK | `LEGACY_FONT_LOCATION = 1`; fonte em 1.440–1.535, 96 tiles | O site atual do SGDK mostra outro padrão de fonte. Para este jogo, vale a configuração local |
| Tiles fixos do jogo | 85 tiles depois dos 16 de sistema | É possível preservá-los e emprestar o espaço dos inimigos, retratos, herói e chão durante o mapa |
| ROM atual | 1.179.648 B = 1.152 KiB; cabeçalho declara região linear de 2 MiB | Há 896 KiB entre o arquivo atual e essa fronteira; o estudo não exige aumentar esse endereçamento |
| RAM estática registrada | 7.318 B no relatório de build existente | Não equivale a RAM livre: heap, pilha, áudio e buffers de DMA também usam RAM |
| Transferência por quadro | SDK local define referência de 7.200 B NTSC e 8.000 B PAL em 224 linhas | Carga de 25.600 B de arte deve ocorrer com display apagado ou ser repartida, não despejada num único VBlank normal |

O mapa é uma tela exclusiva, sem combate. Isso permite reutilizar as reservas de gráficos temporariamente, como o título já faz. Não é necessário manter o mapa inteiro residente ao lado de todos os gráficos da fase.

### Orçamento conservador proposto de VRAM

Este é um contrato de produção, ainda não uma alocação implementada. Mantém as tabelas do VDP e a fonte no lugar atual.

| Intervalo de tiles | Uso | Tiles | Bytes |
|---|---|---:|---:|
| 0–15 | Sistema SGDK preservado | 16 | 512 |
| 16–100 | Elementos fixos preservados | 85 | 2.720 |
| 101–900 | Uma região ilustrada | 800 | 25.600 |
| 901–996 | Rotas, nós, bordas e esquema global | 96 | 3.072 |
| 997–1.028 | Ponteiro / halo / destino | 32 | 1.024 |
| 1.029–1.439 | Margem para refino e efeitos pequenos | 411 | 13.152 |
| 1.440–1.535 | Fonte existente | 96 | 3.072 |
| **Total do espaço de padrões** | | **1.536** | **49.152** |

Os 128 tiles da interface e dos marcadores são uma reserva proposta, que precisará ser medida quando houver arte final. A margem de 411 tiles não é uma garantia de que qualquer nova animação caberá; ela existe para absorver essa produção. Deve haver uma verificação automática de intervalos no exportador futuro.

Com esse layout, sobram no máximo 1.211 tiles para arte se toda a margem for consumida. O panorama de 512 × 160 medido precisa de 1.280 e ultrapassa esse orçamento; o de 640 × 160 precisa de 1.600. O primeiro poderia caber com arte modular ou sacrificando outras reservas; o segundo exigiria reduzir padrões, carregar partes ou reorganizar a VRAM. Não são opções impossíveis do hardware, mas aumentam o trabalho para uma tela que não precisa dessa complexidade.

Quatro regiões no pior caso de 800 tiles, com tilemaps compactos e duas paletas, somam **109.056 bytes** de recursos brutos. Com até 4.096 bytes de padrões compartilhados de interface e marcadores, a estimativa é **113.152 bytes, cerca de 110,5 KiB**, antes de pequenas tabelas, código, alinhamento e padding. Não foi criado um novo build para transformar essa previsão em tamanho final da ROM.

## Direção de arte para preservar riqueza

| Preservar e ampliar | Simplificar ou agrupar |
|---|---|
| Silhueta da igreja, torre e porta azul | Telhas individuais, rachaduras e pedras soltas |
| Nave de resgate e forma da plataforma | Luzes pontuais e grades muito finas |
| Antena parabólica e feixes de dutos | Cabos de um pixel atravessando a rota |
| Comporta e seus dois acessos | Miudezas industriais com o mesmo contraste do destino |
| Massas de ovos, quitina e metal tomado | Ovos minúsculos espalhados por todo o chão |

Metas de desenho propostas, a confirmar em provas de arte: marcos principais com cerca de 32–48 px de largura, alguns chegando a 56 px; ponteiro de 12–16 px; contornos importantes com 1–2 px; caminho com 2 px claros e borda escura; pelo menos alguns pixels de respiro entre rótulo, ponteiro e arquitetura. São orientações visuais, não limites de hardware.

O terreno precisa ter faixas tranquilas para os traçados. Textura concentrada em rochas e ruínas, em vez de um ruído uniforme. Poucos tons por material, sombras em blocos e brilhos usados nos marcos importantes. Evitar dithering automático sobre toda a imagem: ele pode aumentar o ruído e impedir a reutilização de tiles. Uma retícula localizada pode ser testada em sombras grandes.

As duas paletas de arte podem atender materiais quentes e frios, mas cada tile escolhe só uma. Essas transições precisam ser planejadas nas bordas de telhados, dutos e chão. PAL0 atende a interface; PAL1/PAL2 atendem a paisagem; PAL3 fica disponível para uma terceira família de cores se o refino da infestação justificar. Durante o mapa, essa reserva é independente do uso das paletas em combate, desde que tudo seja restaurado ao sair.

## Composição e regiões

Tela proposta: **16 px de cabeçalho + 160 px de mapa + 48 px de informações**. O cabeçalho identifica a região e o avanço global; o rodapé recebe nomes completos e a consequência. A fonte atual de 8 × 8 oferece 40 colunas. Trabalhar com até 36–38 caracteres por linha e margem lateral; não reduzir o texto importante para caber dentro dos ícones. Acentos exigem glifos próprios; a primeira adaptação pode seguir o texto ASCII em maiúsculas já usado no jogo.

| Região | Locais principais | Bifurcação |
|---|---|---|
| Comunidade | 1, 2A, 2B, 3, 4 | Bomba / igreja preservada ou danificada |
| Evacuação | 5, 6A, 6B, 7 | Sinal protegido / retirada por terra |
| Base industrial | 8, 9, 10A, 10B, 11 | Sem dano / dreno térmico |
| Ninhos | 12, 13A, 13B, 14, 15, 16 | Menos de 60 s / decantação |

Esse enquadramento mantém as 20 localidades e as convergências reais em 3, 7, 11 e 14. O epílogo não recebe um nó extra. No esquema global, usar pontos e ramificações, sem escrever todos os nomes. Na região em foco, números e formas distinguem os locais; o nome extenso pertence ao rodapé.

Nas transições 4→5, 7→8 e 11→12, enquadrar a região de destino e incluir a origem junto à borda como ligação de entrada. O ponteiro permanece nessa origem até a viagem ser confirmada. Isso evita desaparecer com o local atual na troca de painel. Um fade curto pode substituir qualquer movimento de câmera; o VDP não oferece zoom de plano por hardware. Uma aproximação real exigiria outra versão da arte ou processamento adicional.

Usar “ETAPA 10/16” quando o próximo destino for 10A/10B, a partir da coluna do grafo, e não “NÓ 12/20”. Também evita chamar a falha do sinalizador de objetivo concluído com sucesso.

Exemplo de rodapé em até 38 caracteres por linha:

```text
AGORA 9: ALFANDEGA
PROXIMA 10A: ACESSO DOS TECNICOS
ROTA: VOCE SAIU SEM DANO
A SEGUIR
```

## Arquitetura futura sugerida

1. **Plano B:** pintura estática regional. Carregar padrões já preparados em ROM, sem converter a imagem em tempo real.
2. **Plano A:** nós, linhas e textos. As ligações vêm das saídas de `GRAPH`; os pontos de desenho ficam em metadados de apresentação por nó. Não congelar os traçados na pintura, pois isso dificulta mostrar o percurso e manter o mapa sincronizado com a campanha.
3. **Marcador:** versão inicial em tiles do plano A, sem custo de sprite, com halo trocando poucos padrões. Se desejarmos viagem suave por pixel, usar um pequeno sprite dedicado com controle explícito da lista de sprites. Nunca escalar o personagem de combate em tempo real; desenhar um ponteiro ou busto pequeno apropriado ao mapa.
4. **Estado:** receber explicitamente o nó atual e o próximo. `currentLevel` já mantém o atual, `pendingLevel` guarda o resultado de `GRAPH_resolve`, e `phaseStats` ainda existe antes da próxima fase. As regras do mapa devem comunicar o resultado, sem recalcular outra escolha independente.
5. **Histórico:** `visited` já tem 32 bits para 20 nós. Na campanha atual, sem ciclos, os pares de nós visitados recuperam o percurso. Para suportar depuração com saltos sem inventar ligações, registrar as transições efetivamente percorridas, por exemplo em uma máscara de 23 arestas, se necessário. “Visitado” hoje é marcado ao entrar, não ao vencer: não usar esse sinal isoladamente como comprovação de objetivo bem-sucedido.
6. **Atualização:** arte fica parada. Animar apenas halo, ponteiro, um pequeno sinal ou material dos ninhos. Evitar reenviar a imagem ou redesenhar todas as letras a cada quadro.

### Entrada e saída da tela

O título já carrega 1.120 tiles de ilustração com duas paletas e restaura o chão e o cache de inimigos ao sair. É um precedente útil, mas o mapa precisa de seu próprio contrato de restauração.

Entrada proposta: aguardar fades/DMA pendentes, terminar efeitos da fase, ocultar sprites antigos, apagar/escurecer a tela, carregar a região e suas paletas, montar os planos, desenhar o estado e revelar. Manter as chamadas por quadro de música/entrada se a carga for distribuída em vários quadros. Uma carga imediata com display apagado também precisa ser medida; não prometer custo zero de CPU ou continuidade de áudio sem teste.

Saída proposta: ocultar o marcador, limpar os planos e restaurar scroll, Window, plano e prioridade de texto; devolver as paletas de jogo, o chão e invalidar o cache de inimigos. O herói é recarregado por `HERO_load()` ao iniciar a fase e retratos são recarregados pelas cenas, mas os caminhos de preparação, história, teste e retorno ao menu também devem ser exercitados.

Não executar `TILEGEN_init()` apenas para restaurar uma paleta: os 85 padrões fixos podem permanecer preservados. `TILEGEN_palette()` devolve PAL0/PAL1; `FLOOR_init()` regenera os tiles de chão; `ENEMYGFX_reset()` impede reutilizar endereços que a arte sobrescreveu. A paleta de chão deve ser restaurada por uma chamada ou carga explícita antes de ser usada; `FLOOR_init()` sozinho gera padrões, não reinstala a paleta ativa. Salvar/restaurar 64 palavras de CRAM custa 128 B e pode complementar esse contrato, sem substituir a regeneração dos padrões sobrescritos.

O estado `ST_MAP` atual chama `SPRITES_hide()` **depois** de `ROUTEMAP_update()`. Portanto, acrescentar um sprite ao update sem alterar essa ordem fará o ponteiro sumir. A versão em tiles evita esse conflito; a versão suave exige integrar uma função de desenho do mapa àquele estado.

## Desempenho e carregamento

A maior parte do custo ocorre ao entrar na tela. Somente a arte de 800 tiles usa 25.600 B. Em transferências de aproximadamente 4 KiB por quadro são necessárias sete parcelas para os padrões, além dos mapas, paletas e preparação. Sete quadros correspondem a cerca de 117 ms em 60 Hz ou 140 ms em 50 Hz; são cálculos de carga, não medições no emulador. O fade pode acomodar esse trabalho, mas é preciso medir com a música e a fila de DMA reais.

Com padrões prontos e sem compressão, o DMA pode ler diretamente da ROM. Não reservar um framebuffer RGB em RAM: 320 × 224 em 8bpp já usa 71.680 B, acima dos 64 KiB da RAM principal. Um buffer 4bpp é menor, mas também desnecessário para uma tela estática. Desenhar tilemaps por linha usa cerca de 80 B de buffer para 40 entradas; estado e animação acrescentam pouco. Isso é uma previsão de desenho, não uma medição de heap livre.

Compressão pode economizar ROM; não diminui a quantidade de padrões que precisa estar na VRAM. Se adotada depois, considerar o tamanho do buffer de descompressão. Para esta primeira versão, cerca de 110,5 KiB brutos são uma troca razoável por carga simples e uso pequeno de RAM.

## Critérios de aprovação antes de integrar

1. Produzir uma região final em escala nativa, com sua bifurcação; comparar a arte no tamanho real e em ampliação inteira, usando também a fonte e as rotas finais.
2. Verificar reconhecimento imediato dos marcos, contraste do ponteiro e leitura de “AGORA/PROXIMA”. Testar os caminhos A e B para não cobrir um marcador com outro rótulo.
3. Exportar e conferir RGB333, uma paleta por tile, limites de índices, entrada zero e roundtrip dos padrões. Não usar substituição aproximada para fazer o orçamento caber.
4. Só depois integrar uma região e testar NTSC/PAL, áudio, pulo da animação e passagem mapa→diálogo→preparação→fase. Verificar ponteiro estável e ausência de tiles antigos ou paletas contaminadas.
5. Testar todas as bifurcações, inclusive a falha da fase 5, e as fronteiras entre regiões. O salto de depuração não substitui a resolução normal das condições.
6. Conferir em emulador e, quando disponível, em console/CRT ou saída composta. Texto, retículas e linhas de um pixel precisam dessa avaliação; não foi realizada nesta investigação.

## Fontes conferidas

Os números de projeto se referem aos arquivos locais, não a uma configuração genérica do SDK:

- `SGDK/inc/config.h`: fonte em localização legada.
- `SGDK/src/vdp.c`: layout padrão 0xC000/0xD000/0xE000/0xF000/0xF400 e resolução.
- `SGDK/inc/vdp.h`, `vdp_tile.h`, `pal.h` e `dma.h`: formato, atributos, cores e capacidades de transferência.
- `game/src/system/video/screens/routemap.c`: mapa atual e histórico.
- `game/src/core/flow.c`: origem/destino, resolução da rota e ocultação de sprites em ST_MAP.
- `game/src/system/video/titlebg.c`: precedente de empréstimo e restauração de gráficos.
- `game/src/levels/arena.c`: scroll, Window, fonte e saída do cenário.
- `game/src/system/video/enemygfx.c`, `tilegen.c`, `floor.c`: cache, padrões e paletas.
- `game/doc/build-validation.json` e tamanho dos arquivos de ROM: última validação existente, sem novo build.

Referências primárias públicas: [VDP no SGDK](https://stephane-d.github.io/SGDK/vdp_8h.html), [atributos e carregamento de tiles](https://stephane-d.github.io/SGDK/vdp__tile_8h_source.html), [paletas e RGB333](https://stephane-d.github.io/SGDK/pal_8h.html), [DMA](https://stephane-d.github.io/SGDK/dma_8h.html). A configuração de fonte da documentação pública atual difere desta cópia local; foi usada a cópia local para o orçamento.

O resultado desta etapa é uma recomendação fundamentada e cinco provas offline, sem alteração de código do jogo, recursos carregados pela ROM ou binários de jogo.
