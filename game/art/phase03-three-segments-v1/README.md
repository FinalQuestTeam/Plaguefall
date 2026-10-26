# Fase 3 com três trechos

Pacote de revisão visual baseado no [guia de imagens](../../doc/historia/guia-imagens-fase03.md).

Composição planejada: início na igreja, rua repetida três vezes e chegada ao galpão, total de 2560×320 pixels. A igreja usa a arte nativa existente. As duas condições narrativas serão apresentadas com a mesma rua.

Abra a [revisão interativa](review.html) para ver o panorama, alternar os estados da igreja, comparar as cores de geração com a paleta da fase 1, retirar os objetos e percorrer os enquadramentos de 320×224. Damião aparece somente como régua de escala nessa simulação.

## Imagens de avaliação

- [Panorama com igreja intacta](palette-preview/05-panorama-intacto.png) e [com igreja destruída](palette-preview/05-panorama-destruido.png), 2560×320.
- [Início intacto](palette-preview/01-inicio-igreja-inteira.png), [início destruído](palette-preview/01-inicio-igreja-destruida.png), [rua B](palette-preview/02-rua-repetivel.png) e [chegada ao galpão](palette-preview/03-chegada-galpao.png), 512×320.
- [Três repetições de B sem objetos](palette-preview/02-rua-tres-repeticoes.png), [folha de objetos](04-objetos-rua.png), [proposta de colisões](06-colisoes.png) e [enquadramentos principais](palette-preview/07-cameras-principais.png).

O sprite da igreja foi copiado sem redimensionamento: 200×112 em x48,y24. A versão danificada vem da mesma região da imagem existente da primeira fase. As duas cópias são verificadas pixel a pixel no [manifesto](manifest.json); a conversão para a paleta de comparação também preserva a igreja intacta.

Os objetos foram gerados em folha com transparência. A exportação usa teste de alfa de 184 para remover o halo suave das fontes e produzir contornos opacos; nenhuma transparência gradual é prevista para o Mega Drive. A arte gerada integral está em `source/`, e os objetos separados estão em `objects/`.

## Implementação no jogo

A implementação nativa e as capturas reais ficam em [integration-v1/review.html](integration-v1/review.html). Somente a fase 3 usa este novo cenário. A igreja foi deslocada 8 pixels para baixo na montagem para manter o telhado abaixo do HUD; a câmera apresenta a construção inteira. Os pixels do sprite permanecem iguais aos da primeira fase.

O panorama usa 3070 padrões exatos no estado intacto e 3086 no destruído, armazenados na ROM. O jogo mantém uma reserva fixa de **640 tiles / 20 KiB de VRAM** e atualiza apenas as faixas que entram na câmera. A prova exaustiva de janelas, com até 41×26 células abaixo do HUD, encontra no máximo 640 padrões visíveis em ambos os estados. Não há troca por tiles aproximados. O céu/vegetação de pequenos intervalos entre construções usa uma faixa repetida de 32×8; edifícios e objetos foram preservados.

O cache usa **11.260 bytes de heap** com a igreja intacta e **11.292 bytes** com ela destruída, além dos pequenos controles estáticos. Mapas e gráficos ficam na ROM. O carregamento antecipa até quatro padrões nas folgas da rolagem. O percentual de saída espera um quadro com pouca transferência de cenário para atualizar; combate e vida continuam imediatos. A pausa libera esse heap, guarda a identidade dos slots no espaço temporário já existente do HUD e restaura os gráficos ao retomar. O início e o galpão têm foco de câmera; as fachadas centrais acompanham a rolagem contínua.

Carros, postes, entulho, caçamba e caixas têm 13 bases sólidas arredondadas para a grade de 8 pixels. Carros, caçamba e caixas também barram os projéteis; os obstáculos baixos deixam os tiros passar. O percurso de 16 pixels continua conectado, com desvios e aproximação livre ao galpão.

Reprodução: `node assemble.cjs`, `node export-stream.cjs`, depois `python3 ../../tools/campaign_corridors.py` a partir deste diretório. O exportador aceita `--check`; a geração usa Node com `@napi-rs/canvas`. A geometria autoral está em `integration-v1/manifest.json`, e os testes de ROM são `game/tools/test_phase03_stream_emulator.py` e `game/tools/test_phase03_load_emulator.py`.

Os relatórios da entrega identificam o SHA256 da ROM. O percurso e o combate nativo usam controle; as provas isoladas de composição/contato e de carga declaram os ajustes de RAM. Esses ajustes existem apenas no processo de teste, sem atalhos de depuração na ROM de produção. A carga é medida em patrulha no trecho inicial e não representa uma revisão humana da dificuldade.

## Geração e revisão

Arte complementar criada com a ferramenta integrada `image_gen.imagegen`, usando as imagens existentes como referências. O [conjunto de prompts](prompts/) conserva as instruções completas da rua, fundo do início, galpão e objetos, incluindo os ajustes do tamanho/enquadramento do galpão e da separação dos objetos. Não foi usada a API por CLI.

A montagem usa pavimento, meio-fio e limite inferior compartilhados para manter a fase de repetição nas quatro emendas. Os três trechos B são cópias idênticas da base e recebem objetos em posições diferentes. A revisão visual identificou o teto do galpão perto do HUD e ajustou sua implantação antes desta entrega. Textura densa de vegetação e repetição das fachadas continuam disponíveis para avaliação do usuário no panorama inteiro.

## Limite inferior

A câmera revela o final completo do cenário ao descer: de y=0 no eixo de apresentação até y=96 junto à borda sul. A aproximação começa com Damião em y=184 e chega ao extremo quando ele alcança y=248. O campo caminhável termina em y=263; meio-fio, muro e vegetação de y=264 a y=319 são cenário visível fora da área de movimento. Cinco trechos foram verificados por controle nas duas regiões, com comparação dos tiles até a última linha da imagem.
