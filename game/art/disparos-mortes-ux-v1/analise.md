# Disparos e mortes — proposta para aprovação

Não implementada em `src`, `res` ou ROM. Esta pasta é uma revisão visual local.

## Diagnóstico

`src/system/video/tilegen.c`, `buildTiles`, gera dois discos sólidos de8×8: índice4 da PAL1 para jogador,5 para inimigos. `spritelist.c` desenha um único sprite8×8 por tiro e não consulta a velocidade para orientar o desenho. Eles têm menos volume e material que os atores atuais.

`enemy_red.c` dispara para Torreão, Fuzileiro e Artilheiro. `enemy_boss.c` dispara o leque do Escorpião. Os demais inimigos não atiram. Não introduzir novos ataques ao trocar a arte.

`shots_enemy.c` não recebe a identidade do atirador. Na implementação será necessário passar um estilo no spawn e preservá-lo até o projétil sumir. Não inferir a origem pela posição ou por um ponteiro para Enemy, que pode ter sido reaproveitado. O campo mode de FShot só tem semântica no tiro do jogador; pode guardar o estilo nos inimigos, desde que o contrato fique explícito. Não aumentar o registro sem necessidade.

Direção visual derivada de vx/vy, sem atan2 em runtime: comparações/módulos para escolher oito setores. O tiro em leque conserva seu vetor real de movimento; só a imagem usa oito orientações. Três tiles canônicos + flips cobrem os oito setores. Não guardar oito cópias por cor. A simulação usa atan2 apenas no navegador.

## Proposta visual

A: bala metálica curta, base de latão; espinhos coloridos com ponta clara, contorno e rebarbas. B: ponta óssea mais clara e longa, bala alongada. A é recomendada por separar melhor a origem amiga/hostil.

Torreão vermelho (PAL1:3), Fuzileiro âmbar (5), Artilheiro violeta (8), Escorpião ciano (2). Todos mantêm ponta clara (1) e contorno preto opaco (11). Jogador usa latão (9) e ponta clara (1). A cor do corpo do inimigo continua indicando sua classe; a cor do espinho identifica o tipo de atirador. Laranja/violeta/ciano nos tiros não criam comportamentos novos.

Não mudar velocidade, dano, cadência, quantidade ou colisão. Preservar boca da arma por desenho e a projeção de altura. Como o contorno vazio do sprite mudou, verificar a sensação de justiça do acerto em movimento antes de considerar ajuste de hitbox. O código atual testa o tiro inimigo como raio3 somado ao raio7 do jogador.

## Morte atual e casos especiais

`enemies.c:enemyDie` desativa imediatamente, divide a Alcateia, deixa poça e sorteia drop. O cache em `enemygfx.c:ENEMYGFX_prepare` libera o quadro se active=false. Apenas acrescentar poses ao catálogo não fará uma morte aparecer: criar registros visuais separados, sem IA nem colisão, antes de liberar o ator.

Entradas necessárias: dano direto, fogo, cadeia e bomba. A bomba tem caminho próprio `ENEMIES_killAll`, não sorteia drop e não mata o chefe. Preservar essas regras e produzir efeitos visuais de modo consistente. O pool não pode atrasar uma morte lógica, pontuação, divisão ou drop, nem reutilizar ponteiros para atores que podem nascer na mesma vaga.

`flow.c`, OBJ_WON, abre o resultado imediatamente. Proposta: concluir a meta no acerto fatal, congelar combate e terminar a curta queda antes de abrir resultado (~300ms comuns/~500ms chefe). É uma mudança de apresentação a ser aprovada junto da arte. Cronometrar em fps para PAL/NTSC; não usar os mesmos números de frames em ambas as regiões.

## Orçamento calculado no código atual

`tiles.h`: NUM_TILES89, cache320, ícones15×16, retratos72, herói48. Com TILE_USER_INDEX16:

| Reserva | Intervalo de tiles absoluto, inclusivo | Uso proposto no combate |
|---|---|---|
| Objetos |16–104|Sem expandir o bloco|
| Cache inimigos |105–424|Continuar com320tiles|
| Ícones |425–664|Contagem425–604; tiros605–619|
| Retratos |665–736|Pool visual de morte, até72tiles|
| Herói |737–784|Preservado|
| Cenário |785–1424|Até640tiles|
| HUD |1425–1435|11tiles|
| Barra NPC |1436–1439|4tiles|
| Fonte |1440…|Não invadir|

O layout não tem folga antes da fonte no pior caso. Não acrescentar tiles fixos à frente do cenário. Reutilizar as reservas de telas fora do combate requer um dono explícito: descarregar/salvar, restaurar antes de pausa/ajuda/rádio/transição e recarregar ao retomar. O countdown já salva/restaura seus180tiles e não deve restaurar por cima dos projéteis. Mantê-los no fim da reserva evita isso. Resultados, rádio e menus podem usar essas reservas fora do combate.

### Tiros

5 estilos×3tiles×32bytes=480bytes residentes;15tiles. Hoje:2tiles/64bytes. Cabe no fim da reserva dos ícones sem mover outros assets. Não há quinto banco de paleta: PAL0 flash/texto, PAL1 objetos/inimigos, PAL2 Damião e PAL3 cenário. Todas as cores do estudo vieram da paleta de objetos do projeto; não trocar cores de PAL1 durante os tiros.

### Mortes

Opção econômica:4quadros×4tiles×32=512bytes, todos residentes; até4efeitos simples,1sprite cada. É a alternativa de saturação, não quatro novas partículas por morte.

Opção recomendada:3poses novas por espécie, uma direção de queda. Sete espécies16×16, três24×24 e duas32×32: (7×4+3×9+2×16)×3×32=8.352bytes de ROM sem compressão. Chefe:36×3×32=3.456bytes; total11.808bytes. Cinco vistas da queda custariam59.040bytes. Os dois alvos de teste não fazem parte do cálculo. Estes são tamanhos de arte bruta; não uma medição do futuro binário.

Separar a memória da arte (ROM) dos quadros residentes (VRAM):4slots de16tiles=64tiles/2.048bytes permitem4mortes comuns no tamanho original. Quando o chefe morre,36tiles dele +2slots comuns de16=68tiles/2.176bytes. Cabe nos72tiles de retratos; o gerenciador deve adaptar a ocupação sem cortar o chefe. Nem todos os quadros ficam residentes; o próximo é transferido quando houver orçamento.

Estimativa de RAM:4registros de16bytes=64bytes, por exemplo posição, idade, tipo, quadro, slot, direção e flags. Confirmar sizeof no compilador68000. Não conservar o Enemy inteiro nem quadros descomprimidos por morte.

`ENEMYGFX_prepare` limita4transferências de inimigos/VBlank e preserva1024bytes e2entradas de fila para SAT/HUD. Cada quadro normal exige128/288/512bytes e o chefe1.152bytes. O teto deve ser compartilhado com mortes/herói/SAT/cenário: não adicionar4transferências de morte ao teto existente. Se necessário, manter o quadro anterior ou usar estilhaço simples.

O hardware impõe80sprites/tela,20/linha e320pixels/linha. Um corpo comum usa1sprite; chefe48×48 usa4. Um tiro continua1sprite. O pool adiciona até4sprites comuns, ou4do chefe+2comuns. Admitir tiros e corpos antes de efeitos de morte. Em bomba ou saturação, reduzir efeitos; não ocultar projéteis ativos. Carcaças não ficam como sprites eternos: terminar na poça de BG_A já existente. Conferir resíduo com a câmera móvel; não ampliar o decalque nesta etapa.

## Validação ainda necessária após aprovação

- Ataques normais e leques nas8direções, disparo de Damião nas âncoras reais, gelo/fogo/raio ativos, sem afetar cadência/dano/colisão.
- Contraste no chão claro, interior escuro, lama/lava e contra efeitos; formas devem continuar distinguindo hostilidade sem depender da cor.
- NTSC/PAL com bomba, fogo, cadeia, Alcateia e chefe; pontos, drops e filhotes uma única vez.
- Pool cheio, sprites na mesma linha e pressão de DMA; nenhum tiro ocultado por efeito.
- Pausa/ajuda/rádio, contagem e transições restaurando as reservas corretamente.
- Última morte visível antes do resultado, sem movimento ou dano durante a espera.

## Arquivos e procedência

`revisao.html` e `revisao.js`: estudo independente em canvas. `assets/disparos-8direcoes.png`: char-maps de8×8, seguindo o formato procedural já usado no jogo. Não são recursos consumidos pela ROM.

`source/mortes-concept.png`: estudo de imagem criado pelo image_gen integrado; prompt salvo em `source/prompt-mortes.txt`. `assets/morte-*.png`: recorte, redução com vizinho mais próximo e quantização para estudar a leitura em16/32pixels. Não são desenhos finais nem animação validada no jogo.

Personagens reutilizam as sheets aprovadas em `cangaco-insects-sized-v3` e `cangaco-protagonista-iso60-v2`. Cenário é uma captura congelada da validação anterior do rádio (`interface-ntsc/resumed-1.png`); a simulação sobrepõe posições e disparos para comparação, não comprova comportamento runtime. Nenhum build foi executado para esta revisão.
