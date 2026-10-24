# Storyboard visual da campanha de Plaguefall

O storyboard começa com os 14 planos e as 18 cartelas da animação já existente no jogo, preservados em capturas da ROM. Depois apresenta sete pranchas com 28 quadros: a chamada curta de missão, as 19 versões de fase e os componentes dos oito encerramentos. O PDF revisado tem 21 páginas. Cada prancha tem quatro quadros: A no alto à esquerda, B no alto à direita, C embaixo à esquerda e D embaixo à direita.

- [PDF para revisão](../../../output/pdf/plaguefall-storyboard-campanha-v1.pdf)
- [Storyboard com imagens e legendas](../../doc/historia/storyboard-campanha.md)
- [História completa e impactos](../../doc/historia/tratamento-proposto.md)
- [Quadros e legendas editáveis](quadros.json)
- [Script de composição](build_storyboard.py)

## Pranchas

| Prancha | Quadros |
|---|---|
| [01 Igreja](imagens/01-igreja-v2.png) | Chamada curta de missão, fase 1, 2A e 2B |
| [02 Galpão e resgate](imagens/02-galpao-resgate.png) | Fases 3, 4, 5 e falha do resgate |
| [03 Esgotos e base](imagens/03-esgotos-base.png) | Fases 6A, 6B, 7 e 8 |
| [04 Fábrica e escolta](imagens/04-fabrica-escolta.png) | Fases 9, 10, 11 e 12 |
| [05 Sindicato e ignição](imagens/05-sindicato-ignicao.png) | Fases 13A, 13B, 14 e 15 |
| [06 Escorpião e Dinorah](imagens/06-escorpiao-dinorah.png) | Chegada e combate da fase 16; Dinorah viva ou morta no epílogo |
| [07 Impactos](imagens/07-impactos-epilogo.png) | Igreja inteira ou destruída; resgate completo ou parcial |

## Direção e continuidade

A abertura segue a ordem, as falas e os tempos do [storyboard aprovado](../../doc/historia/storyboard-abertura-v2.md). O fluxo é animação → menu → nova partida → chamada curta do padre → fase 1. A nova imagem 01A mostra somente essa retomada no pátio; a antiga oficina não é o início da história.

As ilustrações seguem os concepts de Damião, Dinorah, padre Comando, Escorpião e pátio da igreja. Os cenários são recriados para a nova sequência, em vez de atribuir os antigos ambientes a fases que mudaram de objetivo.

As cenas de 2A e 2B, 6A e 6B e 13A e 13B são alternativas. Dinorah chega na fase 5 e continua depois de qualquer resultado do resgate. Viva após a fase 12, ela prepara circuitos, conduz a ignição e participa do confronto final pelo rádio. Morta, não reaparece; Damião e padre conduzem as conversas finais.

O quadro 05D mostra a fase 15 na rota com Dinorah viva. Na rota de morte, a cabine fica vazia, os comandos preparados por Damião são automáticos e o padre acompanha pelo rádio. Os componentes do epílogo se combinam de modo independente, sem apagar perdas anteriores.

## Produção

As sete pranchas conceituais foram geradas pela ferramenta integrada **image_gen**, com referências visuais locais. Os 14 planos iniciais são capturas existentes da animação integrada, sem nova geração de suas imagens. Os prompts completos ficam em [prompts](prompts/); a [revisão da primeira imagem](prompts/01-igreja-abertura-existente.txt) retira o prólogo alternativo e coloca Damião no pátio. A imagem anterior permanece apenas como histórico, fora do storyboard atual. A composição de texto, paginação e PDF usa ReportLab. O script incorpora cada prancha completa, sem recortar, redesenhar ou retocar suas imagens.

As sete pranchas de campanha são direção de ambiente e encenação, não capturas da ROM, mapas de colisão ou especificação definitiva da câmera. As páginas da abertura usam capturas reais do jogo. Totais de inimigos, objetos, distâncias e tempos são definidos pelas legendas e pelo roteiro. Três alvos na fase 8 e três válvulas na fase 11 permanecem sugestões de balanceamento.

Para recompor o PDF e o documento de leitura, execute `build_storyboard.py` com Python, ReportLab e as fontes Arial do macOS. As imagens precisam estar na pasta `imagens`. A pasta `qa` guarda a conferência de paginação e as renderizações de revisão.
