# História de Plaguefall

Plaguefall se passa num Brasil futuro em que a promessa de conquistar o espaço trouxe uma ocupação alienígena para dentro de casa. Damião, um trabalhador com implantes e sonhos de astronauta, abre caminho para uma resistência humana no sertão industrial. O humor da abertura é a maneira dele de falar do desastre; o que sustenta a campanha é a decisão de ficar e defender outras pessoas.

## Leitura

- [Concept art dos cenários](../../art/concepts/fases-v1/README.md): 20 fases e um epílogo com estudos de elementos e narrativa ambiental.
- [Auditoria de fases e saídas (21/10/2026)](auditoria-fases.md): objetivos dos 20 nós, condições reais e bloqueio da rota de falha na proteção.
- [Fluxo proposto da história](tratamento-proposto.md): fuga da igreja, resgate, ruptura com Dinorah na rota de falha e demolição dos ninhos, com cenas e diálogos por fase.
- [Abertura](abertura.md): monólogo, encenação e adaptação para a tela atual.
- [Storyboard do monólogo](storyboard-abertura-v2.md): 14 planos e 18 cartelas, falas, som, cortes e tempo de referência.
- [Abertura animada](../../art/intro-monologo-v2/README.md): monólogo antes do menu, vídeo da ROM e música contínua desde o logo Plaguefall e somente START para pular.
- [Universo e personagens](universo.md): premissa, conflito, religião, cangaço e regras de continuidade.
- [Campanha proposta](campanha.md): resumo dos 20 nós, consequências que persistem entre fases e adaptação necessária ao jogo.
- [Roteiro executável](../../src/levels/story.c): falas que o jogo apresenta.
- [Sistema de história](../plano-historia.md): formato, controles e limites técnicos.

## O que cada material representa

A abertura animada e os diálogos em `src/levels/story.c` representam a versão já integrada ao motor. O [novo tratamento](tratamento-proposto.md) refaz a campanha a partir da fuga da igreja: uma bomba pode danificá-la, proteger o sinalizador na santa permite o resgate, e a falha leva à discussão e à partida de Dinorah. O confronto com o Escorpião abre caminho para instalar cargas e destruir os ninhos. O final confirma a região livre, com o restante do planeta ainda infestado.

O tratamento, a campanha proposta e as seções correspondentes do universo descrevem essa revisão narrativa. A nova continuidade ainda não foi aplicada à ROM. Em especial, diálogos após as convergências precisarão respeitar os resultados da igreja e do resgate; a participação atual de Dinorah na fase 7 é incondicional.

O jogo mantém Damião humano, os insetos cibernéticos, Nossa Senhora Aparecida como objetivo estático e Escorpião. [Damião, Comando e Dinorah têm retratos de conversa baseados nos concepts](../../art/dialogue-portraits-v1/README.md); Escorpião mantém o retrato provisório. Não há ator aliado na arena, sistema jogável de resgate ou colocação de cargas. Esses acontecimentos podem ser apresentados nas cenas da revisão.

As premissas antigas de treinamento militar, mech vermelho e colônia espacial deixam de orientar o roteiro. Os estudos de arte anteriores continuam preservados.

## Prévia e verificação

[ROM atual — 1152 KiB](../../out/release/Plaguefall.bin). A ROM foi recompilada com o SGDK após a integração dos 14 planos e 18 cartelas em 21/10/2026. O [relatório consolidado atual](../build-validation.json) registra memória estática e hash. A animação foi conferida integralmente no Genesis Plus GX em50/60Hz, incluindo A/B/C ignorados no boot, START, retorno ao menu, galeria e início da fase 1.

Os 22 registros de cena e os 20 nós continuam no roteiro da campanha, com 47 falas. O monólogo aprovado tem 14 planos e 18 cartelas antes do menu. As duas falas de missão antes da fase 1 foram preservadas. Os retratos de Damião, do padre Comando e de Dinorah mantêm a [verificação anterior](../../art/dialogue-portraits-v1/README.md); a nova abertura tem [capturas e comparação de pixels próprias](../../art/intro-monologo-v2/README.md).
