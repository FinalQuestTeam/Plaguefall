# História de RedRex

RedRex se passa num Brasil futuro em que a promessa de conquistar o espaço trouxe uma ocupação alienígena para dentro de casa. Rex, um trabalhador com implantes e sonhos de astronauta, abre caminho para uma resistência humana no sertão industrial. O humor da abertura é a maneira dele de falar do desastre; o que sustenta a campanha é a decisão de ficar e defender outras pessoas.

## Leitura

- [Abertura](abertura.md): monólogo, encenação e adaptação para a tela atual.
- [Universo e personagens](universo.md): premissa, conflito, religião, cangaço e regras de continuidade.
- [Campanha](campanha.md): função narrativa dos 20 nós, quatro bifurcações e desfecho.
- [Roteiro executável](../../src/levels/story.c): falas que o jogo apresenta.
- [Sistema de história](../plano-historia.md): formato, controles e limites técnicos.

## O que cada material representa

A abertura e os diálogos foram adaptados ao motor existente. Lugares, organizações e passado dos personagens definidos nestes documentos formam a nova proposta narrativa. As falas dão contexto às arenas atuais; os documentos não significam que fachadas, foguetes, multidões ou novas missões já estejam desenhados ou programados.

O jogo mantém Rex humano, os insetos cibernéticos, Nossa Senhora Aparecida como objetivo estático, a Lacraia e as condições atuais das rotas. [Rex, Comando (padre) e parceira já têm retratos de conversa baseados nos concepts](../../art/dialogue-portraits-v1/README.md). Lacraia mantém o retrato provisório. Rex chama os invasores de “baratas”. A parceira participa por rádio antes da fase 7; seu ator na arena ainda não foi integrado. Não há sistema de pacto, reputação religiosa, resgate de civis, piloto de foguete ou finais condicionais.

As premissas antigas de treinamento militar, mech vermelho e colônia espacial deixam de orientar o roteiro. Os estudos de arte anteriores continuam preservados.

## Prévia e verificação

[ROM atual — 512 KiB](../../out/release/rom.bin). A compilação completa com o SGDK terminou com sucesso numa cópia temporária do projeto. O [relatório](../../art/dialogue-portraits-v1/build-validation.json) registra memória estática de 6165 bytes e 12 avisos nos arquivos preexistentes de cabeçalho/recursos; o roteiro e os retratos compilaram sem avisos.

Foram conferidos os 22 registros de cena, os 20 nós, os retratos disponíveis e as 52 falas pela mesma regra de quebra de palavras da caixa de 26×4. Todas cabem sem corte; a abertura documentada corresponde às falas do código. Rex, o padre Comando e a parceira foram conferidos no Genesis Plus GX; [capturas e relatório](../../art/dialogue-portraits-v1/README.md).
