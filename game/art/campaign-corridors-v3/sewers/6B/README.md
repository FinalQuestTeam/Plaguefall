# Esgoto 6B — câmaras conectadas, versão3

Mundo3072×320. Esta entrega substitui a antiga faixa contínua: cisterna, canais/galerias, instalação de bombas e abrigo formam espaços com larguras e direções diferentes. A6B incorpora duas câmaras de pressão com aproximações em alturas diferentes. Fontes completas ImageGen e prompts estão em `source/`; o [parecer](review.json) descreve decisões, rejeições anteriores e limites.

O gerador privado é `compose.py`. Execute `python3 game/art/campaign-corridors-v3/sewers/6B/compose.py --publish` para reproduzir os arquivos desta pasta. A função `render('6B')` retorna `(files,meta)`: `files` contém os três bancos binários, `meta` o manifesto. A importação gera somente as prévias privadas do próprio diretório; não altera C, recursos ativos ou ROM.

Contrato: `native/tiles.bin`4bpp, `native/map.bin`384×40palavras big-endian, `native/palette.bin`16palavras RGB333 big-endian. `complete-native.png` reconstrói os bancos exatamente. Índice0 permanece preto e reservado; nenhum pixel visível usa0. Não há substituição aproximada de padrões. Custos: cenário378,objetivos256,total634/640. Todos os estados de mecanismo estão incluídos na reserva256 da6B.

O manifesto usa `start` como pés (top-left), `route_points` como centros (−8para pés), `solids` como `[x,y,w,h,bool]` em8px. Água usaFalse; arquiteturaTrue. `camera_interest` possui bboxes de arquitetura≤320×200 e `preferred_feet` legais. `camera_player_y` é200; as amostras184/200/248 estão separadas. Na6B, `valve_approaches` e `gate_shot_approaches` também são PÉS, declarado em `approach_coordinates`.

Verificação local: bancos reproduzíveis, reconstrução exata com zero diferença de pixels, RGB333, orçamento, rota16×16com margem8. O validador compartilhado também exige todas as posições livres conectadas: 6074/6074. Nenhum limite técnico equivale à aprovação de composição. As imagens `qa-interest.png` usam o sprite real de produção sobre o cenário nativo e **não são emulação**.

A integração compartilhada, captura na ROM, travessia com combate, FPS, SAT e consequências são responsabilidade da bateria do root. Resultados de ROM anteriores não foram reaproveitados como aprovação desta revisão.

Os portões globais permanecem separados do fundo. Quatro tiros após a válvula iniciam0,8sde colapso ainda sólido; o sprite inteiro então some e libera32pxentre os apoios nativos. As três imagens completas fechada/colapso/aberta e `qa-gate-states.png` mostram a mesma instalação, sem folha baked sob o estado aberto.
