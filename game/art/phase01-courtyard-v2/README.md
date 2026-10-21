# Fase 1 — Pátio da igreja, revisão 2.1

[Revisão visual](revisao.html) · [Vídeo de movimentação e combate](validation/ntsc/fase01.mp4) · [Partida completa, controle automático](validation/ntsc/partida-completa.mp4) · [ROM jogável](../../out/release/Plaguefall.bin).

**Aprovada pelo usuário em21/10/2026**, revisão2.1. A produção dos capítulos2 a6 segue em [sete telas para revisão](../phases02-06-v1/revisao.html), incluindo as variantes2A/2B e6A/6B. Cada novo conjunto aguarda aprovação antes da integração.

## O que foi corrigido

- Arte refeita com câmera ortográfica elevada a60°: telhado predominante, fachada curta e objetos vistos de cima, usando os sprites de Damião como referência de câmera e escala.
- Mundo ampliado de512×256 para **512×384**. A área caminhável retangular é480×256; os objetos ficam acima dela, junto à igreja. O chão livre passou de43.200 para122.880 pixels, cerca de **2,84 vezes** a área anterior. Não existem os antigos blocos invisíveis na metade inferior.
- Exportação em resolução nativa, com detalhes de um pixel: removida a passagem intermediária por256×128 e a substituição aproximada de tiles. O mapa usa módulos da arte gerada e deduplicação exata. A paleta continua dentro das16 cores do hardware.
- Boca da arma calibrada para os seis quadros usados em cada direção, incluindo espelhamento. Animação, disparo e desenho compartilham a mesma preparação do quadro. A origem deixa de ser deslocada artificialmente para dentro da arena. A colisão do projétil considera seus seis pixels visíveis, sem a margem transparente de um pixel. Se o cano ou o projétil entra no muro, o tiro colide nesse ponto.
- Cantos inferiores com as peças de junção da própria arte. Cantos, faixa horizontal e pilastras do portão usam a mesma translação de32 pixels; os dois estados da igreja compartilham esses muros.
- Colisão dos tiros contra o plano em que são desenhados. O deslocamento visual de16 pixels já não provoca desaparecimento antecipado na borda inferior.
- Bancos e bagagens baixos não bloqueiam projéteis. Os limites de movimento dos pés e do tiro em altura são distintos e definidos explicitamente. O tiro atinge os muros quando sua imagem chega ao limite visível.
- HUD com faixa preta opaca, incluindo caveira, inventário e modo ativo. Os ícones recebem cópias com pixels de fundo pretos não transparentes; os sprites originais dos itens são preservados. A camada do HUD tem prioridade sobre os atores.

A igreja ainda muda parcialmente com a bomba, mantém esse estado após a pausa e determina2A/2B. Ladainha de Ferro permanece como trilha da fase.

## Memória e rolagem

**640 tiles**,20.480 bytes de padrões, uma paleta, dois mapas de6.144 bytes e11 cópias de ícones opacos. O atlas do cenário utiliza temporariamente a reserva dos pisos antigos; os pisos são restaurados ao sair da fase.

O plano do VDP continua64×32. O mundo de64×48 tiles usa uma janela circular: ao mover a câmera, apenas as novas linhas do mapa entram, até128 bytes de cenário e128 bytes de limpeza de decalques por linha. Os padrões de tiles permanecem residentes. A faixa nova de cenário tem cópia própria na fila DMA; não referencia um buffer de pilha já liberado. Sangue usa o mesmo endereçamento circular, evitando escrita fora do plano ao passar de y256.

Limites de carga preservados: quatro inimigos e seis projéteis por lado. O benchmark inclui rolagem horizontal e vertical contínua com esses limites preenchidos. Não há teste em console físico.

## Verificação de colisões e partidas

A revisão2.1 verifica **768 origens de tiro** junto aos muros esquerdo e direito, para cima e para baixo, parado e correndo, cobrindo os seis quadros. Em659 casos, também confronta o projétil e o quadro real do personagem na VRAM/SAT, sem confundir o DMA pendente com a imagem já exibida. Outras4.096 comparações de pixels conferem os dois cantos inferiores na ROM, com e sem dano na igreja. As contagens somam PAL e NTSC.

O script executa448 verificações de movimento e412 disparos em corredores livres por região, cobrindo uma grade no pátio e a borda inferior. Também compara pixels reais do emulador com o mapa exportado após cruzar e revisitar a antiga altura de256 pixels. Capturas depois de reposicionamentos de teste aguardam a conclusão dos quadros lógicos, em vez de presumir que três VBlanks bastam para uma recarga completa.

São seis tentativas completas por região, PAL e NTSC. O controlador automático lê posições e usa apenas o joypad durante essas partidas: vida, inimigos, dano, itens e mortes seguem as regras normais, sem escritas na RAM do jogo após o estado inicial. Incluem vitórias, derrotas, pausa e uso de bomba. Cada desaparecimento de tiro observado é confrontado com muro ou inimigo no percurso. Os resultados e contagens exatas estão nos relatórios.

Os testes isolados de posição, benchmark e rotas usam RAM volátil para preparar casos e acelerar a conclusão; isso é separado das partidas normais. A ROM não é alterada pelos testes. O vídeo de demonstração mantém a vida para mostrar o cenário; o vídeo de partida completa conserva vida e dano normais.

[NTSC](validation/ntsc/report.json) · [PAL](validation/pal/report.json) · [Exportação e hashes](export.json).

## Produção e reprodução

Fontes e prompts estão em `source/`, gerados com a ferramenta integrada **image_gen.imagegen**. `intact-native.png` e `damaged-native.png` reproduzem os módulos e a paleta usados na ROM. `tileset.png`, `courtyard.tsx` e `phase01.tmx` permitem inspecionar o mapa no Tiled; o TMX ainda é uma exportação de inspeção, não um importador para o jogo.

```sh
python3 game/tools/pack_courtyard.py --check
make -C game -j4
arch -x86_64 /usr/bin/python3 game/tools/test_courtyard_emulator.py --matches 6 --movie
arch -x86_64 /usr/bin/python3 game/tools/test_courtyard_emulator.py --matches 6 --pal
python3 game/tools/check.py
```

A [revisão anterior](../phase01-courtyard-v1/README.md) e suas fontes foram preservadas. O mapa original de512×256 não é mais o cenário ativo.
