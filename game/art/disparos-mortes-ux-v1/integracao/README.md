# Tiros A e morte 2 — integração

Escolhas aprovadas pelo usuário: A (quitina) e opção2 (recuo, patas e queda). Os dados finais estão em `game/res/combat/`, referenciados por `combat_art.res`. Fontes de imagem e prompts do image_gen integrado estão em `source/`; as39 poses nativas exportadas ficam em `native/`. Não foram redesenhados os atores vivos.

## Comportamento

- Damião usa projétil metálico curto. Cada atirador preserva um estilo próprio no `mode` do seu FShot inimigo; a física, o dano, os leques e as cadências não mudaram. O modo dos tiros do jogador continua reservado aos itens.
- Cinco estilos, três tiles canônicos por estilo. A seleção por vx/vy usa comparações, com flips para as oito direções. Um sprite8×8 por tiro; sem DMA por projétil. São15tiles/480bytes no fim da reserva de ícones, tiles650–664 absolutos, fora dos180tiles da contagem.
- `COMBATGFX_spawn` copia tipo e posição antes de liberar a entidade. `CombatDeath` tem14bytes, confirmado pelo ELF: quatro registros totalizam56bytes. Não participa de IA, colisão, spawn, contagem nem drop.
- As13espécies combatentes têm3poses próprias, com flash inicial e duração normalizada pelo fps (300ms comuns,500ms chefe). Os dois alvos de treino mantêm seu resíduo simples.
- Até quatro mortes comuns. Para o chefe, o pool muda para36tiles dele e dois slots de16tiles comuns. A reserva de retratos tem72tiles e comporta os68usados. Uma morte de chefe substitui efeitos comuns anteriores para garantir sua apresentação. Excedentes mantêm apenas a poça de BG_A.
- Mortes e inimigos compartilham o limite de4transferências de quadros/VBlank. Com efeitos ativos, os vivos usam até3, garantindo oportunidade aos efeitos. A fila mantém a reserva de1024bytes e duas entradas para HUD/SAT. Sob pressão o quadro anterior é mantido. Corpos vivos, tiros e marcadores entram na lista de sprites antes das carcaças. Os itens entram depois: continuam coletáveis no mesmo instante, mas não cobrem a própria animação de morte.
- Pausa e ajuda já salvam/restauram o intervalo inteiro de VRAM emprestado. A idade dos efeitos só avança no jogo ativo ou no assentamento da última morte; fica congelada na pausa.
- A meta conclui no acerto fatal. Quando há animação pendente, `settleKind` congela combate e estatísticas até ela terminar; só então abre resultado ou rádio final. START ainda permite pausar durante essa espera. Reinício de fase limpa a espera e todos os efeitos.
- Bomba preserva a regra sem drops; fogo, raio e divisão mantêm o caminho lógico original. Poças também são deixadas pela bomba.

## Validação

`validacao.json` identifica a ROM isolada em `rom/`, seus tamanhos e os seis relatórios com o mesmo SHA256. A ROM tem1.441.792bytes. O ELF mediu144bytes de dados inicializados e9.222bytes de BSS, no conjunto atual de alterações do workspace.

O teste dedicado usa RAM apenas para posicionar atores/projéteis e selecionar fases; simulação, mortes, carregamento de VRAM, pausa, ajuda, encerramento e rádio usam o código de produção. Verifica as39poses e seus bytes em VRAM, os40casos de direção/estilo no SAT, estilos após a remoção do atirador, morte lógica imediata, contagem única, bomba sem drop, Alcateia, fogo, raio e espera antes do resultado/rádio. O teste de pressão compara quadros equivalentes incluindo a mesma fase de piscar do herói, para que diferenças de admissão não sejam causadas pela invencibilidade. Confere80sprites/tela,20/linha e320pixels/linha, além da preservação de tiros ao acrescentar efeitos.

Também passaram os testes existentes de interface e resultados das20fases em NTSC/PAL. Exportação reproduzível (`exportar.py --check`), mira diagonal do jogador em50/60Hz e `git diff --check` passaram.

Comandos a partir da raiz do repositório:

```sh
python3 game/art/disparos-mortes-ux-v1/integracao/exportar.py --check
make -C game -j4 release
arch -x86_64 /usr/bin/python3 game/tools/test_combat_art_emulator.py --build-dir game/art/disparos-mortes-ux-v1/integracao/rom
arch -x86_64 /usr/bin/python3 game/tools/test_combat_art_emulator.py --pal --build-dir game/art/disparos-mortes-ux-v1/integracao/rom
```

Os GIFs da revisão vêm de capturas sequenciais da simulação no emulador NTSC. Apenas a permanência do último quadro foi ampliada para a leitura na página. A galeria de poses mostra os dados exportados, não capturas do jogo.

Nenhum commit, push ou atualização de main foi solicitado nesta etapa. As outras alterações já presentes no workspace foram preservadas.
