# Rotas da campanha — padrão visual v2

Candidato atual: **6A,6B e12,3072×272px**. Fontes inteiras foram geradas pelo ImageGen nativo e inspecionadas antes dos recortes. Os prompts e fontes estão em `cycle-1/`; a crítica do primeiro ciclo foi preservada. O segundo ciclo mantém construções inteiras, materiais com seção completa, cantos e margens. O [parecer](review.json) registra melhorias, problemas restantes e provas. Aprovações anteriores foram substituídas; falta revisão na ROM integrada.

A região superior termina em y143; campo percorrível y144..239; limite inferior real y240..271. Laterais têm24px. Os três mundos preservam comprimento3072px, Dinorah, objetivos e ramificações. Entradas, manutenção/pressão e chegadas usam marcos completos; gabinetes/carga inteiros alteram levemente as rotas, com espaço para os personagens.

| Fase | Cenário | Objetos residentes, todos estados | Total/640 |
|---|---:|---:|---:|
|6A|602|0|602|
|6B|373|256|629|
|12|600|0|600|

A6B mantém os sprites globais: gate191+valve65. Os apoios fixos pertencem ao cenário. Depois da pressão e quatro tiros, o portão continua bloqueando por0,8s durante o colapso; então o sprite some e libera corredor32px. O estado final conserva os apoios e o pavimento nativos. Os panoramas completos de todos os estados estão em `current/06b/` e ampliados em `review-evidence/`.

O gerador de produção é `game/tools/build_campaign_routes.py`; ele usa `build_art.py`, sem aproximação de padrões. A redução inicial das fontes usa LANCZOS; a escolha das cores RGB333 é nearest exata, e o reuso8×8 é apenas para padrões idênticos. Índice0 preto reservado. Cada mapa384×34 contém26112bytes e a paleta32bytes. `manifest.json` aponta para cada fonte, panorama, estado, geometria e custo. Os canônicos antigos também apontam para a composição atual.

Verificações locais concluídas: exportação reproduzível; reconstrução binária com zero diferença de pixels;16coresRGB333; varredura16×16 e BFS até a chegada; contratos C reais de válvulas/portões50/60Hz; atlas global intacto. O harness de escoltas foi adaptado para altura272, colapso transiente e ocultação final. A ROM compartilhada será construída e testada pelo responsável da integração.

As pranchas de câmera com Damião/Dinorah usam pixels reais dos sprites de produção e um HUD estático; **não são capturas do emulador**. A revisão cruzada estática não encontrou fragmentos isolados, mas ressalvou a cadência regular do piso e a necessidade de verificar contato/oclusão no runtime. Céu amplo na12 e repetição longa de paredes permanecem limitações explícitas. Nenhuma medição anterior de FPS, carga ou dificuldade é atribuída a esta nova revisão.
