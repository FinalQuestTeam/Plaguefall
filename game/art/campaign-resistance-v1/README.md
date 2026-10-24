> Revisão anterior: cenários e resultados abaixo foram substituídos pelo fluxo de imagens completas. Consulte [a revisão atual](../campaign-whole-scenes-v1/resistance/README.md). Os relatórios antigos não validam os novos mapas.

# Campanha — favela e sindicato v1

Implementação das fases7,8,13A e13B. As fases7/8 compartilham mapa768×384;13A/B compartilham o mesmo cômodo512×384 e exatamente a mesma colisão.

-7: abrir cinco fontes pelo lado sul, parando0,5s sem atirar; pegar o bornal ao lado e levar uma carga por vez ao depósito oeste. Transporte reduz velocidade20%; só a quinta entrega conclui.
-8: destruir três insetos transmissores de4HP. Cada morte aumenta o intervalo de reforço de2 para4,6 e8 segundos. Mortes comuns não concluem.
-13A:30 eliminações. Dinorah aparece trabalhando no compartimento norte fechado e seguro.
-13B:45 eliminações. Mesma sala e limites; o chapéu e a ferramenta substituem Dinorah, sem fantasma ou nova fala.

Cenas nativas de155 tiles, uma paleta16cores compartilhada. Objetos de missão usam o pacote ImageGen já integrado em`objectivegfx`; o estado lógico de cinco fontes não cria cinco famílias novas de arte. Limites configurados:7=4,8=6,13A/B=5 inimigos ativos; seis projéteis por grupo. Os valores são limites de produção, não afirmações de FPS antes do relatório do emulador.

## Fontes e reprodução

`source/kit.png` foi gerada com ImageGen built-in. `assets/` contém extrações convertidas para leitura em baixa resolução. O exportador converte para paleta3bits por canal e tiles4bpp; não sintetiza raster substituto. O piso reutiliza o desenho nativo`FLOOR_STONE_ART`, escurecido para leitura dos personagens. Dinorah reutiliza o sprite aprovado existente. `geometry.json` registra posições e sólidos.

Reproduzir: `python3 game/tools/build_campaign_resistance.py`.

O teste geométrico percorre posições com os mesmos pés16×16 e comprova acesso às cinco cargas, depósito e aproximações dos três transmissores. O teste da ROM está em`game/tools/test_campaign_resistance_emulator.py`; relatórios distinguem controles, preparação pela RAM e carga isolada. Capturas são da ROM emulada; as imagens `*-map.png` são reconstruções do atlas nativo.

## Prompt do kit (ImageGen built-in)

Use case: stylized-concept. Asset type: actual sprite atlas for a Sega Mega Drive top-down action game in a Brazilian industrial favela after an insect invasion. Create ONE sprite atlas on a pure magenta #ff00ff background. Exact layout:4columns by2rows of equal square cells with generous magenta margin, no grid lines, no labels, no text. Row1col1: small favela house module with orange exposed brick facade, flat gray concrete roof and blue rooftop water tank, top-down three-quarter view; row1col2: second gray plaster favela house module with brown door and rooftop cables, same view; row1col3: low broken red brick wall, same view; row1col4: two blue-gray workers' metal lockers with an open door, same view. Row2col1: wooden bench with workers' toolboxes; row2col2: small maintenance console dark gray with green pilot light; row2col3: female worker's red cap with a wrench carefully laid beside it, a memorial prop; row2col4: rolled blankets, pots and stacked crates of an evacuated resistance shelter. Pixel art, crisp outlined chunky pixels,16-color retro palette, each item isolated and fully contained in its cell, no characters, no shadow beyond a few pixels, no full scenes. Every item distinct, readable at approximately48×48pixels. Render no decorative borders.
