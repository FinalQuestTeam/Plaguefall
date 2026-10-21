# Sistema de história — diálogos entre fases

O motor já está implementado. Este arquivo documenta o contrato técnico; a [pasta de história](historia/README.md) contém a abertura, o universo e a campanha. As falas que entram na ROM vivem em `src/levels/story.c`.

## Conteúdo atual

O roteiro tem **22 cenas**: uma chegada para cada um dos 20 nós, a aproximação do chefe depois da fase 15 e o final depois da 16. Cada percurso atravessa 16 fases e apresenta 18 cenas. A abertura tem sete falas; as demais, duas ou três. Toda cena pode ser pulada.

Rex é humano com implantes; Comando é o padre que coordena a resistência pelo rádio; Lacraia é a matriz local do enxame. [Rex, Comando e parceira têm retratos 48×48 derivados dos concepts](../art/dialogue-portraits-v1/README.md). A parceira fala por rádio antes da fase 7; não há ator aliado na arena. Lacraia mantém o retrato provisório. Rex chama os invasores de BARATAS nas suas falas.

O roteiro substitui a demonstração de sete cenas que descrevia um piloto de mech numa colônia. Não modifica objetivos, inimigos, itens, terrenos ou critérios das rotas.

## Registro das cenas

A história é vinculada ao **nó do grafo**, não ao número aparente da fase. Cada nó pode ter uma cena de `ANTES` e outra de `DEPOIS`.

```c
CENA(capela)
    DIREITA(P_COMANDO, "O RADIO FICA NA BASE DA SANTA. PROTEJA O PONTO POR TRINTA SEGUNDOS.")
    DIREITA(P_COMANDO, "PRECISAMOS DESSE TEMPO PARA TRANSMITIR AOS ABRIGOS.")
    ESQUERDA(P_REX, "MINHA MAE MANDOU LEVAR UMA REZA. HOJE EU FACO A ESCOLTA.")
FIM

// Na tabela STORY:
QUANDO(N_5, ANTES, capela),
```

- `ESQUERDA(retrato, texto)` usa o canto superior esquerdo.
- `DIREITA(retrato, texto)` usa o canto inferior direito.
- A ordem das entradas define a conversa; um falante pode continuar por várias entradas.
- `P_REX`, `P_COMANDO`, `P_LACRAIA` e `P_PARCEIRA` são os retratos registrados.
- Cada par nó/momento deve aparecer no máximo uma vez: `STORY_find` retorna a primeira correspondência.

`StoryLine` guarda lado, retrato e texto; `StoryEntry` guarda nó, momento, lista de falas e contagem. As estruturas vivem em `levels/story.h`.

## Texto e controles

A caixa tem **26 colunas por 4 linhas**. O motor quebra por palavra e **descarta sem aviso o que não cabe**. Contar caracteres não basta: espaços e palavras próximas da borda podem exigir uma quinta linha. Validar a quebra real ao mudar o roteiro.

Usar MAIÚSCULA SEM ACENTO e pontuação ASCII. Escrever as versões longas com acentos nos documentos; adaptar as falas para a ROM em entradas curtas. Não inserir uma sequência de barra e `n` para forçar linha: o motor não interpreta esse escape como paginação.

O texto aparece a duas letras por quadro, com `sfxItemPickup` como blip de voz. A durante a escrita completa a fala; A depois da escrita avança. START encerra a cena inteira. O indicador de continuação é `>` piscando. As duas caixas de texto são limpas a cada fala, enquanto os retratos carregados permanecem na tela.

## Fluxo e memória da partida

`core/flow.c` usa `ST_STORY` entre as telas existentes:

- Novo jogo → história de chegada ao nó 1 → preparação.
- Conclusão → história DEPOIS, se houver → mapa → história ANTES do destino → preparação.
- Chefe derrotado → história DEPOIS da 16 → tela de fim.

Uma máscara de 32 bits por momento registra cenas vistas, com bit por nó. É zerada no novo jogo; morrer e tentar a mesma fase não repete a cena. O sandbox não recebe cenas. Os 20 nós atuais cabem na máscara.

As condições ficam em `levels/graph.c`: bomba na 1, falha do objetivo na 5, dano na 9 e tempo na 12. Não há seleção independente de falas por inventário, fé, reputação ou histórico completo das rotas.

A falha do objetivo na 5 também alcança o fluxo DEPOIS antes de seguir a 6B. Por isso o resultado da proteção aparece somente nas chegadas a 6A e 6B. Cenas em nós de convergência não podem presumir qual dessas rotas foi percorrida.

## Retratos e recursos

A arte está em `system/video/sprites/portraits_data.h`: quatro char-maps 48×48, cada um com paleta de 16 cores. O exportador em `art/dialogue-portraits-v1/export_portraits.py` gera o cabeçalho e preserva o retrato legado da Lacraia. A ordem deve acompanhar os `P_*` e `PORTRAIT_NAME`.

Dois retratos custam 72 tiles temporários, emprestados da região do chefe `BOSS_ROT_BASE`. O esquerdo usa PAL2; o direito, PAL3. Ao encerrar, `ENEMYGFX_dropBoss()` invalida o cache. A preparação da partida restaura as paletas. A biblioteca acrescenta o retrato da parceira na ROM e substitui os de Rex e Comando. A quantidade simultânea continua sendo dois, sem reserva adicional de VRAM ou buffers de RAM.

## Verificação ao editar

Conferir que cada fala cabe pela mesma quebra de palavras do motor, que usa caracteres suportados e retrato existente, e que o par nó/momento é único. Compilar com o SDK do projeto. Na revisão visual, conferir a abertura, A completando e avançando, START pulando e as duas saídas da proteção. Uma compilação bem-sucedida não comprova a aparência no emulador.
