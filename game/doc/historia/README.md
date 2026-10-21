# História de Plaguefall

Plaguefall se passa num Brasil futuro em que a promessa de conquistar o espaço trouxe uma ocupação alienígena para dentro de casa. Damião, um trabalhador com implantes e sonhos de astronauta, abre caminho para uma resistência humana no sertão industrial. O humor da abertura é a maneira dele de falar do desastre; o que sustenta a campanha é a decisão de ficar e defender outras pessoas.

## Leitura

- [Abertura](abertura.md): monólogo, encenação e adaptação para a tela atual.
- [Storyboard do monólogo](storyboard-abertura.md): 12 planos ilustrados, falas, som, cortes e tempo de referência.
- [Abertura animada](../../art/intro-monologo-v1/README.md): monólogo antes do menu, vídeo da ROM e controles para avançar/pular.
- [Universo e personagens](universo.md): premissa, conflito, religião, cangaço e regras de continuidade.
- [Campanha](campanha.md): função narrativa dos 20 nós, quatro bifurcações e desfecho.
- [Roteiro executável](../../src/levels/story.c): falas que o jogo apresenta.
- [Sistema de história](../plano-historia.md): formato, controles e limites técnicos.

## O que cada material representa

A abertura e os diálogos foram adaptados ao motor existente. Lugares, organizações e passado dos personagens definidos nestes documentos formam a nova proposta narrativa. O monólogo já tem imagens animadas no boot; essas ilustrações dão contexto ao mundo, sem mudar as arenas ou acrescentar novas missões e sistemas de resgate.

O jogo mantém Damião humano, os insetos cibernéticos, Nossa Senhora Aparecida como objetivo estático, a Lacraia e as condições atuais das rotas. [Damião, Comando (padre) e Dinorah já têm retratos de conversa baseados nos concepts](../../art/dialogue-portraits-v1/README.md). Lacraia mantém o retrato provisório. Damião chama os invasores de “baratas”. Dinorah participa por rádio antes da fase 7; seu ator na arena ainda não foi integrado. Não há sistema de pacto, reputação religiosa, resgate de civis, piloto de foguete ou finais condicionais.

As premissas antigas de treinamento militar, mech vermelho e colônia espacial deixam de orientar o roteiro. Os estudos de arte anteriores continuam preservados.

## Prévia e verificação

[ROM atual — 768 KiB](../../out/release/rom.bin). A compilação completa com o SGDK terminou com sucesso numa cópia temporária do projeto. O [relatório da abertura animada](../../art/intro-monologo-v1/build-validation.json) registra memória estática de6159 bytes. A animação foi conferida integralmente no Genesis Plus GX em50/60Hz, incluindo A/START, retorno ao menu, galeria e início da fase 1.

Os 22 registros de cena e os 20 nós continuam no roteiro da campanha, agora com47 falas: as cinco caixas resumidas do monólogo deram lugar aos 12 planos completos antes do menu. As duas falas de missão antes da fase 1 foram preservadas. Os retratos de Damião, do padre Comando e de Dinorah mantêm a [verificação anterior](../../art/dialogue-portraits-v1/README.md); a nova abertura tem [capturas e comparação de pixels próprias](../../art/intro-monologo-v1/README.md).
