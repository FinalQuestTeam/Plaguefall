# Inimigos gigantes — cangaço cyberpunk — concepts v1

Quatro pranchas de pintura digital no estilo do
[protagonista v3](../protagonista/protagonista-cangaco-cyberpunk-v3.png):
fundo bege, materiais gastos, implantes e placas reaproveitadas sobre corpos
orgânicos gigantes. Uma silhueta humana sugere escala. As imagens são estudos
artísticos, sem pretensão de precisão biológica.

## Pranchas

| Família do projeto | Nova referência | Prancha | Prompt |
|---|---|---|---|
| sq | Besouro serra-pau | [PNG](sq/sq-serra-pau-v1.png) | [Prompt](sq/prompt-v1.txt) |
| tri | Mutuca | [PNG](tri/tri-mutuca-v1.png) | [Prompt](tri/prompt-v1.txt) |
| pen | Saúva-soldado | [PNG](pen/pen-sauva-soldado-v1.png) | [Prompt](pen/prompt-v1.txt) |
| boss | Escorpião-amarelo-do-Nordeste | [PNG](boss/boss-escorpiao-nordeste-v1.png) | [Prompt](boss/prompt-v1.txt) |

Cada prancha comum tem quatro variantes: figura principal à esquerda e três
figuras menores à direita. O tamanho das figuras na composição não estabelece
uma escala relativa entre variantes.

## Correspondência com os nomes existentes

| ID | Nome no jogo | Referência | Posição na prancha |
|---|---|---|---|
| sq_red | Torreão | serra-pau | principal à esquerda |
| sq_yellow | Batedor | serra-pau | direita superior |
| sq_purple | Baluarte | serra-pau | direita central |
| sq_orange | Aríete | serra-pau | direita inferior |
| tri_red | Fuzileiro | mutuca | principal à esquerda |
| tri_yellow | Caçador | mutuca | direita superior |
| tri_purple | Escudeiro | mutuca | direita central |
| tri_orange | Adaga | mutuca | direita inferior |
| pen_red | Artilheiro | sauva-soldado | principal à esquerda |
| pen_yellow | Alcateia | sauva-soldado | direita superior |
| pen_purple | Fortaleza | sauva-soldado | direita central |
| pen_orange | Meteoro | sauva-soldado | direita inferior |
| boss | Lacraia | escorpiao-chefe | vista principal à esquerda; vistas complementares à direita |

O nome Lacraia e o identificador boss são preservados no catálogo para
rastreabilidade; o novo concept visual do chefe é um escorpião, que é um
aracnídeo. Dummy e Alvo são recursos de teste e não receberam novas criaturas.

## Estado da entrega

- Quatro PNGs de 1536 × 1024 pixels, com fundo opaco.
- Doze variantes comuns e um chefe com vistas complementares.
- Prompts completos e [catálogo por ID](catalog.json).
- Geração pela ferramenta integrada image_gen, usando a imagem do protagonista
  como referência visual.
- Nenhuma substituição de sprite ou alteração de comportamento na ROM.

A futura produção de sprites continua sujeita à câmera a 60° acima do chão,
oito direções e restrições do Mega Drive. Estas pranchas não são exportações SGDK,
não têm paleta indexada e não validam enquadramento ou anatomia para animação.
