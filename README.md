# Plaguefall

Shooter de arena para **Sega Mega Drive / Genesis**, escrito em C com o SGDK. Damião, um trabalhador com prótese cibernética, protege uma comunidade do sertão industrial dos insetos trazidos por foguetes. A direção mistura cangaço, cyberpunk brasileiro e religiosidade popular.

![Menu de Plaguefall](game/art/menu-logo-v1/menu-3x.png)

[Baixar Plaguefall.bin](game/out/release/Plaguefall.bin) · [Ver a abertura](game/art/intro-monologo-v2/emulator-ntsc/abertura.mp4) · [GDD](game/doc/GDD.md)

## Estado atual

- **Escorpião com segunda fase:** aos 12 de vida, transição com brilho e som, duas investidas avisadas, recuperação vulnerável de 1,2 s e leques alternados de cinco tiros. Sem blindagem periódica na segunda metade e até dois Caçadores vivos. Acertos reais, pausa, reinício, vitória por controle e carga de 30 s passaram em NTSC/PAL; carga observada de 59,37/49,83 FPS. [Revisão e ROM](game/art/boss-phase2-v1/review.html) · [Validação](game/art/boss-phase2-v1/delivery.json).
- **Disparos do Escorpião corrigidos:** leques completos de cinco tiros; limite independente de dez projéteis inimigos na fase 16, preservando quatro para Damião. O chefe aguarda cinco vagas livres, sem apagar tiros existentes nem cortar a rajada. [Validação NTSC/PAL](game/art/boss-shots-v1/README.md).
- **Fase 16 no mesmo estaleiro:** [sala e janelas nativas](game/art/phase16-shipyard-v2/review.html), mesmo mapa de 512×576, piso, limites, rádio compacto, bateria, conexões, cinco geradores ligados e colisões da 15. Apenas os interiores das duas janelas superiores mudam, com módulo de 144×80 em 16 cores. 578/640 tiles; 28 câmeras por região, travessia, pausa, reinício e vitória contra o Escorpião passaram em NTSC/PAL. [Relatórios e ROM](game/art/phase16-shipyard-v2/delivery.json).
- **Fase 15 modular:** [núcleo de rádio compacto](game/art/phase15-shipyard-v2/review.html) de 48×64 com seis estados. Somente a base de 32×16 bloqueia passagem e recebe dano; mastro livre, barra local de integridade e reação ao dano. Mesma sala de 512×576 da 14, piso rebitado, limites repetíveis, bateria/conexões e cinco geradores nativos ligados. Defesa de 120s, ignição, pausa, colisões, derrota/reinício e 28 câmeras passaram em NTSC/PAL. 578/640 tiles. Carga: 54,15–57,05 FPS NTSC / 47,75–48,95 PAL. [Relatórios e ROM](game/art/phase15-shipyard-v2/delivery.json).
- **Fase 14 modular:** [topo, base e console como prop independente](game/art/phase14-shipyard-v2/review.html), mapa512×576, cinco geradores novos48×48com seis estados, rede de conexões até bateria/console e limitadores repetíveis. Piso de placas de ferro com rebites. Barras individuais:10spara ativar, perda de10%a cada1safastado. Cache480 + gerador53 + barras20 =553/640tiles; pixels nativos,28câmeras, operação, colisões, pausa e resultados passaramNTSC/PAL. Carga artificial:57,3FPSNTSC/49,5PAL. [Relatórios e ROM](game/art/phase14-shipyard-v2/delivery.json).
- **Câmera estável integrada:** nas fases 1–13 e variantes A/B, segue apenas o corpo de Damião, sem reenquadramento automático de fachadas, Santa ou Dinorah em repouso. A validação das fases 1–12 está no [relatório da câmera](game/art/camera-follow-v2/main-release/report.json); a extensão às 13A/13B passou por 52 ensaios de movimento e 12 de estabilidade em [NTSC/PAL](game/art/phase13-union-v2/delivery.json).
- **Cenários da campanha:** 19 variações em 16 etapas, compostas por áreas superior/inferior, limites laterais e elementos próprios de cada objetivo. A fase 3 usa os [três trechos de igreja, rua e galpão](game/art/phase03-three-segments-v1/integration-v1/review.html). A fase 9 usa a [rua industrial em três trechos, com rota de contorno](game/art/phase09-three-segments-v1/review.html#path). O corredor 12 usa os [três blocos até o sindicato](game/art/phase12-three-segments-v1/review.html), A+B+B+B+B+C, com cenário inteiro, percurso e vídeo de travessia. A Santa mantém seu desenho, colisão e efeitos de proteção.
- **Fase 12 local:** [saída da fábrica, corredor repetível e sindicato](game/art/phase12-three-segments-v1/review.html), três bases de512×320px,11props, anexo/oficina com telhado metálico corrugado e618/640tiles estáticos, com o prédio STE no destino. Escolta completa, morte13B, contatos, pausa, cinco emendas, fachadas/logo STE e36câmeras passaramNTSC/PAL. Carga configurada:59,85–59,90FPSNTSC/50PAL em4setores.
- **Fases 13A/13B ampliadas:** [salão do sindicato STE e câmera corrigida](game/art/phase13-union-v2/review.html), mundo 512×576 px, altura de combate 136→328 px (+141,2%) e três bancos redistribuídos e limpos, sem resíduos do piso original nos recortes. Mesma câmera estável das fases 1–12: 52 ensaios de movimento e 12 de estabilidade sem desvio/cortes em NTSC/PAL. Cache 640 tiles, pico conservador 543; objetivos 30/45, travessia, colisões, pausa, reinício e resultados passaram. Carga controlada:58,80–59,05 FPS NTSC e 49,70 PAL.
- **Fase 11 local:** [reativar a fábrica](game/art/phase11-factory-v2/review.html), mesmo cenário da10 com tijolos azuis por troca de paleta, seis válvulas distribuídas, barra de operação de2,5s, cinco inimigos simultâneos e reforços a cada2s. Testes funcionais NTSC/PAL e regressões9/10 passaram. Carga máxima:48,5–60FPS NTSC e49,85–50PAL; há queda no setor central.389/640tiles usados.
- **Fase 10 local:** [fábrica detalhada e ovos distribuídos](game/art/phase10-factory-v2/review.html), seis grupos de obstáculos,352px de campo vertical e470/640tiles. Dez alvos por controle, persistência, bomba, pausa e colisões passaram em NTSC/PAL. Carga:56,25–60FPS NTSC e49,55–50FPS PAL.
- **Fase 9 modular:** [cenário e caminho do jogador](game/art/phase09-three-segments-v1/review.html#path), com oficinas e três caminhões, A+B+B+B+C, passagens de64px e448tiles residentes (antes630). Travessia por controle, pixels e contatos passaram em NTSC/PAL. Carga de3inimigos e4+4tiros em4trechos manteve60/50FPS.
- **Fase 8 urbana:** [base comprometida](game/art/phase08-urban-v1/review.html), mesmo cenário atual da fase 7 e três emissores;636/640 tiles. Testes funcionais e regressões NTSC/PAL passaram. Carga máxima:46,4–60 FPS NTSC,50 FPS PAL; há quedas em NTSC.
- **Fase 7 urbana:** [feira do Último Chão](game/art/phase07-urban-v2/review.html), com asfalto, bueiro aberto de saída dos esgotos, comércio e quatro barracas de lona branca. Mantém 304 px de altura útil e cinco cargas, com 634/640 tiles reservados. Saída, transporte, colisão, câmera e pausa validados em NTSC/PAL; carga medida de 55,1–59,85 FPS NTSC e 49,95–50 PAL.
- **Fase 6 integrada:** [esgotos com entrada, galeria repetível e acesso ao abrigo](game/art/phase06-three-segments-v1/integration-v1/review.html). A 6A tem dois portões que recebem quatro tiros, sem válvulas. A 6B combina pressão, barra de operação sobre a válvula e portões. A barra é independente da vida da Dinorah. Os portões mostram A + mira e quatro marcas que preenchem a cada acerto; na 6B, a referência aparece após liberar a pressão. Uso da reserva: 568/640 tiles na 6A e 637/640 na 6B. Os relatórios registram as quedas sob carga.
- **Acesso rápido:** em **FASE TESTE**, esquerda/direita alternam entre as 19 fases da campanha e os oito finais. A reproduz o final escolhido, que volta ao seletor ao terminar ou pular com START. A pausa permite reiniciar e trocar a fase escolhida. [Guia do seletor](game/art/test-selector-v1/README.md).
- **Damião** é o protagonista jogável, com oito direções e animações de repouso e movimento. **Dinorah** participa da escolta e das conversas. Os dois têm [animação de morte em quatro poses](game/art/actor-deaths-v1/README.md), exibida antes do resultado da tentativa.
- **Mecânicas da campanha:** as antigas salas experimentais **11–18** validaram demolição, subestação, carregamento, caça aos transmissores, válvulas, evacuação, armadilha e defesa com retirada. Os objetivos agora têm [dez folhas próprias com 60 quadros](game/art/objective-sprites-v1/README.md): explosões dos ninhos, vapor das válvulas, energia pulsante, baús com sacolas, grades caindo, escolta de Dinorah e uma câmara que retém os insetos. [Guia e validação](game/doc/fases-experimentais.md). Essas mecânicas também compõem a campanha atual.
- **Campanha:** 16 etapas por partida, 19 versões de fase e três decisões persistentes. Igreja, resgate e Dinorah produzem oito encerramentos. Inclui escolta, transporte, alvos prioritários, ovos, válvulas, energia, defesa de rádio e Escorpião. [Playtests e resultados](game/doc/campanha-implementada.md).
- **Encerramento ilustrado:** depois do Escorpião, três slides automáticos em 25 segundos mostram a igreja, a população e Dinorah conforme as escolhas da campanha. Seis quadros do storyboard formam os oito finais, com fades, legendas e 12 partículas como na abertura. START pula até a tela de vitória. [Vídeo dos oito finais](game/art/ending-slides-v1/videos/todos-os-finais.mp4) · [Arte, roteiro e validação NTSC/PAL](game/art/ending-slides-v1/README.md).
- **Abertura:** FinalQuest → APRESENTA → logo Plaguefall → monólogo ilustrado em14 planos e18 cartelas, com101 segundos → menu. A música **O Sonho Atendido** começa no logo Plaguefall e segue continuamente pelas imagens. Somente **START** pula; A, B e C não completam textos nem avançam cenas. A abertura toca uma vez por boot.
- **Continuação sem SRAM:** **Sinal do Último Chão**, seis símbolos de 32×32, incluindo o sindicato STE. Fotografe/anote o código na entrada da fase ou consulte **Sinal de continuação** na pausa. **Sintonizar** retoma o início da fase com as decisões e melhorias anteriores, vida cheia, duas bombas e inventário vazio. Códigos incorretos ou incompatíveis são recusados. [Sprites e validação](game/art/sinal-ultimo-chao-v1/native/).
- **Menu inicial:** Novo Jogo, Como Jogar, Sintonizar e Fase Teste.
- **Áudio:** síntese PSG em tempo real, com ritmo e acentos de combate ligados à ameaça. As versões nordestina industrial, melancólica, sombria e de inspiração em igreja permanecem preservadas.
- **Arte:** personagens32×48, inimigos16/24/32 pixels e chefe48×48, oito direções e perspectiva elevada. Tiles, paletas e mapas da campanha são compilados na ROM; as fontes e os guias de produção estão em `game/art/`.
- **Interfaces:** diálogos em [console de holodeck](game/art/dialogue-holodeck-v1/README.md), com monitor preto, títulos dourados, descrições em cinza claro e dois retratos nos monitores inferiores. Quem fala mantém as cores originais; quem escuta fica escurecido. Objetivo, guia da fase e contagem usam o monitor único do rádio. Dez inimigos menores têm retratos de 32×32 extraídos das mesmas fontes originais corrigidas dos sprites de combate, sem reinterpretar os personagens; a paleta e os sprites de combate permanecem iguais. As trocas conversa → objetivo → contagem e a navegação do guia preservam o fundo, com o próximo conteúdo preparado antes da troca em VBlank. Há uma única contagem 3/2/1, em dourado; o controle é liberado ao entrar na arena. [Validação das cores em NTSC/PAL](game/art/radio-text-colors-v1/validation/report.json). [Retratos das dicas e validação atual](game/art/mission-portraits-v3/validation/report.json).
- **Textos em português:** abertura, rádio, menus, guia, preparação, pausa, HUD, rotas e resultados usam maiúsculas com acentos. Os 12 caracteres `ÀÁÂÃÉÊÍÓÔÕÚÇ` reutilizam posições de minúsculas na fonte de 96 tiles, sem ampliar a reserva de VRAM. [Validação NTSC/PAL](game/art/texto-acentuado-v1/validation/report.json).
- **ROM principal:** 3.014.656 bytes; SHA256 `84569b175095220ff4710717f616c31102185b3373e73d3d51057bd8626d7f6d`. As [fases 4 e 5](game/art/phase45-vertical-v1/review.html) têm 288 px de altura útil para combate (+80%), mapas de 448 px de altura e obstáculos reposicionados. Mesmos tiles na VRAM; rolagem, colisões, pausa, contato da Santa e relógio de dois minutos validados em NTSC/PAL. A carga com patrulha vertical manteve 60/50 FPS por 20 s por fase/região. [Relatório consolidado](game/doc/build-validation.json).

O [roteiro da campanha](game/doc/historia/campanha.md) e o [guidebook](game/doc/historia/README.md) registram história, decisões e consequências, incluindo a participação de Dinorah nas últimas etapas quando sobrevive.

## Controles

| Botão | Partida | Outras telas |
|---|---|---|
| Direcional | Move em oito direções | Navega nos menus |
| A | Atira; segurar ativa autofire | Confirma opções; inicia a fase; completa/avança diálogos |
| B | Usa o item selecionado | Retoma na pausa; cancela a confirmação de saída |
| C | Troca o item selecionado | Avança páginas no seletor de fases |
| START | Pausa/retoma | Confirma no menu/final; repete na derrota; cancela na confirmação; pula abertura/conversas |

**Mira diagonal:** ao soltar o direcional depois de andar na diagonal, Damião conserva a mira e pode disparar parado com A. Uma tolerância de80ms entre soltar os dois eixos evita virar involuntariamente para uma direção reta. Segurar apenas um eixo confirma a mudança; um novo toque após parar muda a mira imediatamente.

**Durante o boot, somente START tem ação.**

## Itens

| Item | Efeito |
|---|---|
| Marmita do abrigo | Recupera15 pontos de vida |
| Divisor de disparo | Adiciona projéteis, até cinco por disparo |
| Servo de passada | Aumenta a velocidade |
| Carga de desmonte | Explosão de área |
| Capacitor de proteção | Invencibilidade temporária |
| Bobina de subestação | Tiros com reação em cadeia |
| Refil de arrefecimento | Congela inimigos |
| Refil de maçarico | Aplica queimadura |
| Bornal de recuperação | Sempre após derrota: recupera o equipamento anterior conforme a etapa |

**Resultados:** a derrota repete a mesma fase com vida cheia e equipamento básico, deixando sempre um **bornal de couro** perto da queda, em chão seguro e sem prazo para desaparecer. Ao recolher, nas etapas **1–5** recupera todo o equipamento anterior; nas **6–11**, recupera com uma melhoria de tiro e de velocidade a menos, sem o piso 3, e um item a menos (último espaço ocupado; depois, uma carga de bomba). Nas **12–16**, recupera no máximo **+1 projétil e +20% de velocidade**, de forma independente e apenas se possuía cada melhoria antes da morte; itens, bombas e efeitos não voltam. A bolsa usa uma fotografia do equipamento na hora da morte, preserva as novas coletas dentro dos tetos e guarda itens sem espaço para uma coleta posterior. Outra morte substitui a bolsa com os valores da queda mais recente, mesmo se a anterior não foi recolhida. As rotas A/B usam a mesma regra de sua etapa; as páginas 7/8 e 8/8 do **Como jogar** explicam a recuperação. Sair ao título exige confirmação. Conclusões e mudanças de rota aguardam uma nova pressão de A/START; o final aguarda a escolha. As trocas de resultado e mapa mantêm o fade; conversa, objetivo e contagem preservam a moldura do rádio, e botões segurados durante a carga não confirmam a próxima tela. A entrada de cada fase da campanha usa uma única contagem **3/2/1**, durante a preparação dos recursos, no monitor do rádio, com moldura metálica e letras amarelas. A música continua e a fase começa assim que a preparação e os três segundos terminam, sem segunda contagem dentro da arena. Jogar novamente limpa rotas, cenas e estatísticas e começa na fase 1. Atalhos de depuração exigem `DEV_SHORTCUTS` e estão desativados na ROM principal.

Marmita, divisor, servo e bornal aplicam seu efeito na coleta; os demais usam o inventário. C seleciona e B ativa. A vida persiste entre fases. A opção **Fase Teste** oferece as **19 versões da campanha** e os **oito finais**, em abas alternadas por esquerda/direita. Cima/baixo escolhem a fase e C avança páginas; A entra e B/START voltam. Na pausa de uma fase aberta pelo seletor, use **Reiniciar fase** ou **Trocar fase**. As salas técnicas de validação foram retiradas do seletor.

O [HUD da resistência](game/art/hud-resistencia-v1/integracao/README.md) está integrado: faixa de 24 px, objetivo, quatro espaços de itens, modo de tiro e vida com número e barra.

[Lava e lama modulares](game/art/terrain-modules-v1/README.md) possuem cantos, bordas e miolos conectáveis, com lava animada e transparência sobre qualquer piso. Estão aplicadas à sala de perigos, à travessia e à escolta; a mesma definição posiciona a arte e os efeitos de jogabilidade.

## Compilar e conferir

Requisitos: SGDK, `m68k-elf-gcc`, Make, Java e Python3. No macOS deste projeto:

```sh
git submodule update --init SGDK
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
make -C game -j4 OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/tools/check.py
```

O build gera **`game/out/release/Plaguefall.bin`** para abrir no emulador, acompanhado de `Plaguefall.png` para a capa da biblioteca e `Plaguefall.json` com identificação e hashes. `Plaguefall.bin` é a única ROM versionada; `rom.bin` permanece como saída interna local do SGDK, com conteúdo idêntico. Os testes nativos usam uma pasta temporária e verificam partituras, PAL/NTSC, envelopes, prioridade dos efeitos, as quatro faixas e a continuidade da abertura. [Configuração, emulador e testes de integração](game/doc/desenvolvimento.md).

## Organização

```text
game/
├── src/                 # código do jogo, telas, áudio e renderização
├── res/                 # recursos usados pelo SGDK
├── art/                 # fontes, exports, prévias e relatórios de arte/áudio
├── doc/                 # design, história e desenvolvimento
├── tests/audio/         # testes nativos mantidos
├── tools/               # geradores e validação
│   └── music-bench/     # bancada opcional; compartilha o áudio de produção
└── out/release/Plaguefall.bin  # ROM principal; rom.bin é saída local do SGDK
SGDK/                    # submódulo do SDK
```

Compilações experimentais, objetos, dependências e arquivos de sistema foram retirados do versionamento. As músicas preservadas e as artes de referência continuam em `game/art/`; relatórios históricos descrevem suas respectivas revisões.

## Documentação

- [GDD](game/doc/GDD.md) · [Desenvolvimento e validação](game/doc/desenvolvimento.md).
- [História e campanha](game/doc/historia/README.md) · [Storyboard](game/doc/historia/storyboard-abertura-v2.md).
- [Direção sonora e partituras](game/doc/musica.md) · [Abertura com música contínua](game/art/audio-abertura-v3/README.md).
- [Arquivo da antiga galeria musical](game/art/gallery-v1/README.md) · [Inventário de sprites](game/art/INVENTARIO-SPRITES.md).
- [Itens e ícones atuais](game/art/cangaco-itens-v2/README.md) · [Arte do projeto](game/art/README.md).
- [Guia SGDK em português](game/doc/sgdk-guia.html).
