# Oito missões experimentais

As novas missões ficam em **FASE TESTE → salas 11–18**. Nenhum nó, objetivo,
diálogo ou caminho da campanha foi substituído. A integração narrativa depende
do playtest do autor.

START abre a pausa: configurar, reiniciar ou trocar a sala. A configuração
permite pausar os reforços, usar a cadência normal ou pressão contínua, escolher
1–5 projéteis iniciais, velocidade de +0 a +100% e ligar/desligar a proteção
contra derrota de Damião. Essa proteção não torna o rádio indestrutível nem
evita a falha da missão. Aplicar configurações reinicia a sala.

| Sala | Missão | Como vencer e regra particular |
|---|---|---|
| 11 | Demolição dos ninhos | Pare ao sul dos ninhos 1, 2 e 3, sem atirar, por 2 s cada. Eles explodem e deixam destroços. O progresso é preservado ao recuar. A primeira carga abre um atalho; a segunda reduz reforços; a terceira inicia 25 s para alcançar a saída. As cargas não consomem bombas do inventário. |
| 12 | Religar a subestação | Ative os geradores 1 e 2 por 1,5 s cada, na ordem desejada. A ordem determina o corredor eletrificado. Depois ative o painel 3 por 2 s. Há 2 s de tolerância após cada gerador antes do dano. A energia continua pulsando nos equipamentos ligados, inclusive após concluir a sala. |
| 13 | Recuperar carregamento | Aproxime-se de um baú para abri-lo; depois recolha a sacola que aparece ao lado. Leve uma sacola por vez ao depósito D, a oeste. Carregar reduz a velocidade em 20%, mantendo o tiro. Duas entregas liberam a saída; a terceira concede 15 HP e 3 s de escudo. O baú permanece vazio após a coleta. |
| 14 | Caçar transmissores | Elimine os três Torreões marcados. Eles recuam quando Damião chega perto e mantêm o ataque original. Cada alvo eliminado desacelera os reforços. Tiros, itens e bombas usam os caminhos normais de dano. |
| 15 | Sangrar a pressão | Abra as três válvulas por 1,5 s cada e alcance a saída. As faixas térmicas alternam, com aviso de 1,5 s antes do calor; cada válvula reduz a janela quente. A última desliga o perigo. |
| 16 | Corredor de evacuação | Versão estendida da escolta de Dinorah, reutilizando personagem, animações, combate e espera por cobertura. A rota faz zigue-zague por três portas em alturas diferentes, quatro acertos por porta. Ela espera nos obstáculos e quando Damião se distancia. Abra as portas e chegue com Dinorah viva à saída. A morte dela falha a missão. |
| 17 | Atrair o enxame | Entre pela abertura oeste da câmara e atraia insetos sem atirar. O campo puxa cada um para dentro e o mantém preso; as luzes pulsam e o HUD mostra a ocupação. Com dois ou mais retidos, permaneça 1 s no painel C, a sudoeste. O processamento termina após 1,5 s. Processe seis ao todo. Há resfriamento de 2 s; estar dentro durante a descarga causa 40 de dano. Reposição continua com reforços pausados, respeitando quatro insetos simultâneos. |
| 18 | Segurar e abandonar | Proteja o rádio R, com 60 HP, por 25 s. Contato inimigo tira 6 HP, com intervalo de 1 s e recuo. Após a autorização, abandone o posto e alcance a saída a oeste. O rádio cair antes da autorização falha a missão. |

O inventário conserva A para atirar, B para usar e C para selecionar. A interação
por proximidade e permanência evita acrescentar um botão ao controle de três
botões. O indicador de progresso aparece junto ao ponto em uso.

## Gráficos e geometria

As oito plantas têm 512×384 pixels, câmera e obstáculos próprios. O gerador
`tools/build_operations.py` reutiliza exatamente o atlas e a paleta industriais
das salas de teste existentes; os retângulos usados para desenhar os obstáculos
também geram a colisão. As grades e o atalho têm colisão dinâmica para corpos e
projéteis. A câmera conserva o sistema de mapa circular da produção.

O pacote contém **dez folhas próprias e 60 quadros de animação**, gerados
com ImageGen e convertidos para a paleta de produção: ninho, gerador, caixa,
transmissor, válvula, grade, armadilha, rádio, câmara de contenção e civil. O
civil anterior fica preservado como arte de arquivo; a sala 16 usa Dinorah.
Explosões, vapor,
eletrificação, abertura, queda e chegada segura acompanham as ações. Os
recursos, fontes, prompts e capturas estão no [pacote de arte](../art/objective-sprites-v1/README.md).

Na sala 16, os portões acompanham o eixo norte–sul dos muros. Cada vão tem
dois batentes permanentes de 16×8 e uma folha central de 16×48. Somente a
folha deixa de bloquear a passagem ao cair para leste; os batentes continuam
sólidos. O desenho e a colisão usam as mesmas coordenadas geradas para o mapa.

As portas da escolta ficam em `(160,168)`, `(288,256)` e `(416,144)`. A rota de
Dinorah passa pelas três alturas usando o sistema da escolta básica da sala 8.
A extensão permanece na sala 16 antes da validação para a história.

A sacola de carregamento usa o desenho do bornal de couro, com colisão própria
de coleta. Ela não chama a recuperação de equipamentos após derrota. O baú
abre primeiro, e a sacola aparece antes de poder ser recolhida.

Na contenção, a câmara comunica entrada livre, insetos retidos e processamento.
O painel em `(216,240)` mantém a câmara visível ao acioná-lo. As paredes norte,
sul e leste são sólidas; a abertura oeste permite entrar e sair. O campo move
os capturados para pontos internos, liberando a entrada para os demais.

Ninhos, geradores e válvulas são operados pelo lado sul, sem atirar, para que
Damião não cubra o objeto com seu próprio corpo. A conclusão congela o objetivo,
mas a última animação termina; a pausa congela também as animações. Cada sala
reinicia com os recursos e estados visuais próprios. As grades preservam sua
colisão dinâmica; os novos transmissores mantêm a IA e a colisão dos alvos.

## Desempenho e dificuldade

O limite é **4 insetos e 6 tiros por lado**, com **3 insetos na escolta** para
acomodar Dinorah e seus dois tiros aliados. O disparo de
cinco projéteis continua disponível, com a política de reciclagem já existente.
Pressão contínua mantém o mesmo teto, mas tenta repor dois insetos a cada segundo;
a cadência normal tenta um a cada três segundos, com os modificadores de cada
missão. O HUD mostra FPS medido contra VBlanks, uso de CPU, pico de CPU, insetos
ativos e picos de tiros do jogador/inimigos.

Os testes distinguem:

- conclusão por controle com reforços pausados e sem derrota, mantendo as regras
  dos objetivos e os inimigos obrigatórios;
- condições de falha, bloqueios e saídas antecipadas com preparação explícita
  de RAM em cenários isolados;
- 30 s por sala e região na cadência normal, com tiro por controle;
- 30 s por sala e região com o teto de inimigos resistentes (três na escolta,
  quatro nas demais), seis tiros de cada
  lado continuamente repostos e equipamento máximo, por preparação de RAM;
- uma tentativa de percurso por bot na cadência normal, com vida normal e sem
  preparação de RAM. Ele não usa itens nem esquiva com a competência humana;
  vitórias, derrotas, dano e duração servem para comparar pressão, sem atribuir
  uma dificuldade humana definitiva.

O alvo estrito é 60 FPS NTSC / 50 FPS PAL. Cada relatório preserva FPS real,
VBlanks perdidos e `target_met`, que só é verdadeiro com **zero** perdas. O
limiar de aceitação dos protótipos é 98% da cadência normal e 95% no estresse
permanente; aprovação desse limiar não significa atingir o alvo estrito.

As primeiras experiências com 10 insetos e 16 tiros por lado excederam o
orçamento do 68000. A formatação do painel foi distribuída em pequenos campos
e os objetos fixos passaram ao cenário antes da calibração dos limites atuais.
As cargas maiores não são oferecidas nessas missões.

Resultados, capturas e identificação da ROM:
[pacote atual de arte e validação](../art/objective-sprites-v1/README.md).

## Reproduzir

```sh
python3 game/tools/build_operations.py --check
arch -x86_64 /usr/bin/python3 game/tools/test_operations_emulator.py \
  --seconds 30 --output game/art/operations-v1/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_operations_emulator.py \
  --pal --seconds 30 --output game/art/operations-v1/validation/pal
```

`--quick` mantém navegação, configuração, pausa, conclusão e limites dos
objetivos; omite os ensaios de dificuldade e desempenho. `--rooms 11,15`
restringe a bateria às salas indicadas.
