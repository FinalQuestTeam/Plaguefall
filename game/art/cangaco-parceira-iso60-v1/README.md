# Dinorah — sprites cangaço cyberpunk

Derivados do concept v2 aprovado: mulher brasileira com implantes, placas reaproveitadas em vermelho-óxido, tecido marrom e arma de fogo. ID de recurso: `parceira`; nome narrativo: **Dinorah**.

**Células 32×48, oito direções e as mesmas animações de Damião.** A câmera elevada a 60° acima do chão foi usada como referência visual; o topo do chapéu e dos ombros domina a leitura. A revisão compara desenhos 2D ao guia geométrico de Damião, sem medir um ângulo 3D exato a partir dos pixels.

- [Folha mestra nativa completa](parceira/parceira.png), 192× 768.
- [Folha mestra nativa reduzida](parceira/parceira-compacta.png), 192× 768.
- [Corrida reduzida, prévia 4×](previews/parceira-corrida-4x.gif).
- [Repouso reduzido, prévia 4×](previews/parceira-repouso-4x.gif).
- [Comparação com Damião, mesma ampliação](previews/damiao-parceira-comparacao-4x.png).
- [Todas as poses canônicas, prévia 4×](previews/parceira-todas-poses-4x.png).
- [Paleta indexada](palette.json) / [paleta GIMP](palette.gpl).
- [Recursos SGDK](parceira.res) / [catálogo](catalog.json).
- [Pacote completo](redrex-parceira-iso60-v1-sgdk.zip).

## Folhas e direções

Cada direção está em uma folha 192×96: seis colunas e duas linhas, sem margem ou grade. Célula 32×48, apoio na linha 46, mesma referência vertical de Damião. A matriz completa tem quatro quadros parados e duas células transparentes na primeira linha; seis de corrida na segunda. A matriz reduzida tem dois parados e quatro de corrida, com as células restantes transparentes. As mestras empilham as oito folhas na ordem N, NE, L, SE, S, SO, O, NO.

| Direção | Matriz completa | Matriz reduzida |
|---|---|---|
| N | [PNG](parceira/directions/parceira_N.png) | [PNG](parceira/directions/parceira_N_compacta.png) |
| NE | [PNG](parceira/directions/parceira_NE.png) | [PNG](parceira/directions/parceira_NE_compacta.png) |
| L | [PNG](parceira/directions/parceira_L.png) | [PNG](parceira/directions/parceira_L_compacta.png) |
| SE | [PNG](parceira/directions/parceira_SE.png) | [PNG](parceira/directions/parceira_SE_compacta.png) |
| S | [PNG](parceira/directions/parceira_S.png) | [PNG](parceira/directions/parceira_S_compacta.png) |
| SO | [PNG](parceira/directions/parceira_SO.png) | [PNG](parceira/directions/parceira_SO_compacta.png) |
| O | [PNG](parceira/directions/parceira_O.png) | [PNG](parceira/directions/parceira_O_compacta.png) |
| NO | [PNG](parceira/directions/parceira_NO.png) | [PNG](parceira/directions/parceira_NO_compacta.png) |

Cinco vistas desenhadas: N, NE, L, SE, S. SO/O/NO espelham SE/L/NE horizontalmente, como Damião. Isso também espelha os detalhes assimétricos do equipamento e do implante; frente/costas nunca são criadas por VFLIP. A sequência NE foi corrigida separadamente para manter quatro repousos com pés apoiados e corrida com arma voltada para a mesma diagonal.

## Animações e paleta

A versão reduzida usa as mesmas poses de origem de Damião: `[0,2,4,6,7,9]`, formando dois quadros parados e quatro de corrida. Mesmo ritmo do runtime: 24/9 ticks por quadro em NTSC 60Hz; 20/7 em PAL 50Hz. As prévias reduzidas usam 400ms por quadro parado e 150ms de corrida. As prévias completas usam 200ms/100ms.

Paleta única compartilhada com Damião/PAL2, 15 cores visíveis, RGB de 3 bits por componente, índice 0 transparente e alfa binário. A parceira concentra as cores quentes no chapéu, tronco e roupa; Damião conserva as áreas principais em cinza e azul. Não se acrescenta uma quinta paleta para mostrar os dois. A figura ainda tem diferenças de forma e posição próprias de cada pose; o registro de repouso limita a variação do centro dos pixels de apoio inferior a um pixel.

## Recursos e custo

Recurso completo, separado da imagem, conferido pelo ResComp instalado:

```text
SPRITE parceira "parceira/parceira.png" 4 6 FAST 6 NONE BALANCED FAST
```

O arquivo `parceira.res` também contém a alternativa `parceira_compacta`, com tempos 24/9 por animação para NTSC. Deve-se escolher a alternativa necessária. Em PAL, a temporização deve acompanhar os 20/7 ticks do renderer atual.

Para o renderer manual do projeto, `runtime/frames.bin` já está em cinco vistas × seis poses, em ordem de coluna, dividido como Damião: 32×32 e 32×16. Há uma declaração BIN separada em `runtime/parceira.res`.

| Medida | Custo do pacote reduzido |
|---|---:|
| Quadros canônicos em ROM | 30 × 768 = 23040 bytes |
| Arquivo de paleta | 32 bytes, idêntico ao de Damião e reutilizável |
| Quadro ativo | 24 tiles = 768 bytes |
| Peças de hardware no renderer manual | 2: 32×32 +32×16 |
| Transferência por troca de quadro |até 768 bytes |
| Nova paleta necessária |0 |

A matriz completa tem 80 referências de quadro, a reduzida 48, incluindo os espelhos. O binário histórico completo contém 50 quadros canônicos e 38400 bytes. A otimização automática de corte do recurso SPRITE pode gerar duas ou três peças, conforme a pose; as duas peças fixas se referem ao renderer manual e ao binário candidato.

**Dinorah já está integrada à [galeria ASSETS](../gallery-v1/README.md).** A prévia usa oito direções e duas poses de repouso, com a paleta de Damião. O papel mecânico da parceira ainda precisa ser implementado. Caso ela apareça simultaneamente com Damião, será necessário alocar o quadro ativo e admitir as duas peças na lista SAT; há 24 tiles não usados por Damião na reserva atual de personagens, mas o reaproveitamento deve ser feito na integração. Limites H40, DMA, RAM do estado e FPS continuam compartilhados e precisam ser medidos com a personagem em execução. Estes testes de assets não garantem quinze inimigos a 60FPS.

## Verificações e reprodução

[Relatório técnico](validation/report.json): PNGs indexados 4bpp, dimensões, alfa, paleta idêntica, quadros distintos, células vazias, margens, apoio, oito direções, espelhos e decodificação independente dos dois retângulos de hardware para todos os quadros. O ResComp confirmou 16 animações com 4/6 quadros e a alternativa com 2/4, incluindo os tempos. [Revisão visual](validation/camera-review.json) separada das verificações técnicas.

```sh
/opt/homebrew/bin/python3 game/art/cangaco-parceira-iso60-v1/export_sprites.py
/opt/homebrew/bin/python3 game/art/cangaco-parceira-iso60-v1/export_sprites.py --check
/opt/homebrew/bin/python3 game/art/cangaco-parceira-iso60-v1/validate_sprites.py
```

Arte criada com **image_gen integrado**, com [concept v2](../concepts/parceira/parceira-cangaco-cyberpunk-v2.png), guia geométrico e sprites de Damião como referências. [Prompt principal](prompts/parceira.txt), [correção NE parada](prompts/parceira-NE-idle.txt) e [correção NE corrida](prompts/parceira-NE-run.txt). Fontes preservadas em `originals/`.

A ferramenta forneceu fontes ampliadas; o exportador separa as poses pelo alfa, descarta poses excedentes, registra, reduz por vizinho mais próximo e indexa na paleta final. As poses são desenhadas pela ferramenta de imagem; o código não inventa membros ou movimentos. As prévias ampliadas ficam separadas dos PNGs nativos.
