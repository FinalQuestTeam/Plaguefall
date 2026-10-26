# História de Plaguefall

Plaguefall se passa num Brasil futuro em que a promessa de conquistar o espaço trouxe uma ocupação alienígena para dentro de casa. Damião, um trabalhador com implantes e sonhos de astronauta, abre caminho para uma resistência humana no sertão industrial. O humor da abertura é a maneira dele de falar do desastre; o que sustenta a campanha é a decisão de ficar e defender outras pessoas.

## Leitura

- [Concept art dos cenários](../../art/concepts/fases-v1/README.md): 20 fases e um epílogo com estudos de elementos e narrativa ambiental.
- [Auditoria de fases e saídas (21/10/2026)](auditoria-fases.md): registro da campanha anterior, com 20 nós e suas condições de saída.
- [História completa e impactos das rotas](tratamento-proposto.md): roteiro de 23/10/2026, com as 16 fases por partida, diálogos, três bifurcações, participação final de Dinorah e oito combinações de encerramento.
- [Storyboard visual da campanha](storyboard-campanha.md): começa com os 14 planos da animação existente e segue com sete pranchas de campanha, 28 quadros, falas e impactos; inclui PDF de 21 páginas.
- [Guia de produção visual das fases](guia-producao-visual-fases.md): 19 fichas, inventário de recursos existentes e cinco kits com 30 famílias de elementos para aprovação antes da produção.
- [Guia das imagens da fase 3](guia-imagens-fase03.md): início na igreja, rua repetível e chegada ao galpão; medidas, encaixes, objetos, memória e revisão antes de criar as imagens.
- [Guia dos três blocos da fase 6](guia-imagens-fase06.md): entrada dos esgotos, galeria repetida quatro vezes e saída para o abrigo; composição compartilhada de 6A e 6B, escolta, mecanismos e orçamento de memória.
- [Abertura](abertura.md): monólogo, encenação e adaptação para a tela atual.
- [Storyboard do monólogo](storyboard-abertura-v2.md): 14 planos e 18 cartelas, falas, som, cortes e tempo de referência.
- [Abertura animada](../../art/intro-monologo-v2/README.md): monólogo antes do menu, vídeo da ROM e música contínua desde o logo Plaguefall e somente START para pular.
- [Universo e personagens](universo.md): premissa, conflito, religião, cangaço e regras de continuidade.
- [Campanha proposta](campanha.md): resumo dos 19 nós propostos, objetivos, consequências persistentes e adaptação necessária ao jogo.
- [Roteiro executável](../../src/levels/story.c): falas que o jogo apresenta.
- [Sistema de história](../plano-historia.md): formato, controles e limites técnicos.

## O que cada material representa

A abertura animada e os diálogos em `src/levels/story.c` representam o roteiro integrado ao motor. A [revisão de 23/10/2026](tratamento-proposto.md) organiza a campanha em retirada, recuperação de recursos e ataque aos foguetes. O uso de bomba altera a igreja; a defesa da santa determina as perdas civis; a escolta da fase 12 determina a sobrevivência de Dinorah.

Dinorah permanece na operação depois de qualquer resultado do resgate. Se sobreviver à fase 12, participa das conversas das fases 14, 15 e 16, conduz a ignição e chega ao epílogo. Se morrer, Damião e o padre conduzem a etapa final. Os três resultados independentes compõem oito combinações de encerramento.

A história completa e o resumo da campanha são a referência da nova continuidade. Sua integração à ROM permanece pendente. As missões experimentais já oferecem referências de mecânicas, mas não representam a aplicação deste roteiro à campanha. A auditoria de 21/10/2026 documenta a versão anterior.

O jogo mantém Damião humano, os insetos cibernéticos, Nossa Senhora Aparecida e Escorpião. [Damião, Comando e Dinorah têm retratos de conversa baseados nos concepts](../../art/dialogue-portraits-v1/README.md); Escorpião mantém o retrato provisório. A nova campanha exige adaptar objetivos, percursos, cenas e seleção de diálogos por resultado.

As premissas antigas de treinamento militar, mech vermelho e colônia espacial deixam de orientar o roteiro. Os estudos de arte anteriores continuam preservados.

## Prévia e verificação

[ROM atual — 1152 KiB](../../out/release/Plaguefall.bin). A ROM foi recompilada com o SGDK após a integração dos 14 planos e 18 cartelas em 21/10/2026. O [relatório consolidado atual](../build-validation.json) registra memória estática e hash. A animação foi conferida integralmente no Genesis Plus GX em50/60Hz, incluindo A/B/C ignorados no boot, START, retorno ao menu, galeria e início da fase 1.

Os 22 registros de cena e os 20 nós continuam no roteiro da campanha, com 47 falas. O monólogo aprovado tem 14 planos e 18 cartelas antes do menu. As duas falas de missão antes da fase 1 foram preservadas. Os retratos de Damião, do padre Comando e de Dinorah mantêm a [verificação anterior](../../art/dialogue-portraits-v1/README.md); a nova abertura tem [capturas e comparação de pixels próprias](../../art/intro-monologo-v2/README.md).
