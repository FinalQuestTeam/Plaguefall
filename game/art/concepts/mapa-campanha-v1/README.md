# São Jerônimo — mapa da campanha / concept v1

Pré-produção visual. Nenhum arquivo do jogo, recurso de ROM ou comportamento foi alterado.

## Direção

Um atlas regional visto de cima: a comunidade ocupa a terra ocre à esquerda; cabos, antenas e dutos conduzem à base à direita; resina e ovos progressivamente substituem a arquitetura humana. A geografia reúne os lugares do roteiro em uma composição conceitual, sem pretender definir distâncias reais. O interior da base aparece em corte para que o percurso continue legível.

O mapa completo é uma prancha para revisão. Na futura tela de 320 × 224, a proposta é aproximar o trecho da jornada em uso e manter uma faixa de contexto. Os 20 nomes não devem disputar espaço na mesma tela pequena. A imagem ilustrada é um conceito, ainda sem conversão para tiles ou paleta do Mega Drive.

## Onde o jogador está

- **Damião / AGORA:** ponteiro preenchido com contorno claro no último local concluído. Permanece visível; só o halo pulsa. Número e nome aparecem também no painel.
- **PRÓXIMA:** círculo duplo vazado e seta no trecho que será percorrido. O marcador tem uma forma diferente do de Damião.
- **Percorrido:** linha contínua clara, com nós preenchidos. Somente as ligações realmente atravessadas recebem esse estado.
- **À frente:** linha tracejada fria e nós vazados. Ramos não usados ficam discretos; não recebem cadeado, pois a rota decorre dos acontecimentos.
- A passagem proposta dura cerca de 1,5–2 segundos: enquadrar origem e destino, desenhar a ligação e deslocar o ponteiro ao confirmar. Quando chegar, o painel muda de “PRÓXIMA” para “AGORA”. A confirmação pode pular a animação.

O exemplo da tela mostra a fase 9 concluída sem dano e o destino 10A. Até a confirmação, Damião permanece na alfândega. Não chamar 10A de posição atual antes da viagem. O mapa entre fases comunica o caminho resolvido pelo jogo; não apresenta uma escolha manual entre A e B.

O quadro geral com todos os locais serve à revisão. Para o jogador, revelar detalhes dos ninhos conforme a aproximação, mantendo a silhueta distante da base. Não mostrar o chefe como um monstro gigante no mapa.

## Bifurcações preservadas

| Saída | Rota A | Rota B | Reencontro |
|---|---|---|---|
| 1 | Sem usar bomba → 2A, rua de serviço | Usou bomba → 2B, baixio da igreja danificada | 3 |
| 5 | Sinalizador protegido → 6A, resgate | Objetivo falhou → 6B, retirada por terra | 7 |
| 9 | Sem sofrer dano → 10A, acesso dos técnicos | Sofreu dano → 10B, dreno térmico | 11 |
| 12 | Menos de 60 s → 13A, linha quente | 60 s ou mais → 13B, decantação | 14 |

O percurso tem 20 locais possíveis e 16 fases por partida. As quatro bifurcações convergem novamente. Dano à igreja e resultado do resgate permanecem independentes. O epílogo retorna à comunidade, mas não é uma fase 17 nem uma ligação nova no grafo.

## Fontes e produção

- Grafo e condições: `game/src/levels/graph.c`.
- Narrativa: `game/doc/historia/campanha.md` e `game/art/concepts/fases-v1/guia-cenarios.md`.
- Referências visuais: conceitos existentes do pátio da igreja, antenas e câmara do Escorpião.
- Arte de paisagem: ferramenta integrada **image_gen**, prompt integral em `prompt-paisagem.txt`.
- Composição: rótulos, ligações e painéis sobrepostos de forma determinística para preservar o grafo exato. O script `compor.py` apenas gera os arquivos desta pasta.

Os estados e a animação descritos aqui são propostas para aprovação, sem implementação no jogo.
