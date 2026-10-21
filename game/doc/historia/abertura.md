# Abertura — o sonho atendido

## Monólogo aprovado

> Você já ouviu falar que o Diabo dá tudo que a gente quer?

> Mas sempre da maneira mais filha da puta possível?

> Eu sonhava com astronautas, extraterrestres e foguetes.

> Eu consertava essas máquinas, achando que um dia iam me deixar subir.

> As naves que levavam os meus sonhos…

> hoje voltam trazendo ovos.

> De quem foi nelas, nem sinal.

> Só aquelas merdas saíram de dentro. Patas, asas e zumbido.
> Pra mim, é tudo barata.

> Já perdi um braço. Quase perdi uma perna.

> Mas esse povo ainda precisa de mim.

> Minha mãe sempre mandava eu levar uma reza.
> Eu levo. No bolso da munição.

**Comando, pelo rádio:** “Damião… Damião, tá me ouvindo? Aqui é o padre. Ainda tem gente aqui dentro. A gente tá tirando todo mundo pelos fundos, mas eles já chegaram no pátio. Segura eles mais um pouco.”

**Damião:** “Tô ouvindo. Hoje ninguém vai pro céu antes da hora.”

## Encenação e montagem na ROM

O [storyboard aprovado em 21/10/2026](storyboard-abertura-v2.md) foi integrado com 14 planos, 18 cartelas e 101 segundos de exibição. O sonho vem seguido do trabalho; o retorno das naves revela os ovos e a ausência dos tripulantes. A prótese esquerda mostra o custo pessoal, e as pessoas abrigadas concretizam por quem Damião continua lutando. A mãe permanece apenas na fala no passado. O rádio prepara a retirada dos civis para a esquerda e a decisão final de proteger a passagem.

O Diabo permanece na provocação inicial, sem entidade ou pacto em quadro. Os planos 08, 11, 12 e 13 mudam apenas a legenda, conservando imagem, partículas e música. Os recortes do terço e do padre excluem as margens das pranchas originais.

A [abertura integrada](../../art/intro-monologo-v2/README.md) usa enquadramento fixo, fade visual de 0,4s, poeira/brasa/fuligem e texto branco centralizado sobre preto, em até 36 colunas por quatro linhas. As falas são apresentadas em texto. A [trilha contínua](../../art/audio-abertura-v3/README.md) começa no logo Plaguefall; os 4s do logo antecedem os 101s do monólogo, com 3s de sustentação reservados para as cargas. As mudanças de imagem ou cartela não reiniciam nem silenciam a música.

## Fluxo e controles

FinalQuest → APRESENTA → logo Plaguefall → monólogo ilustrado → menu. A sequência toca uma vez por boot. A/B/C não completam legendas nem avançam planos; somente START pula tudo, também em APRESENTA ou no logo. Segurar START não inicia a partida no menu. Voltar ao menu pela pausa não repete a abertura.

Antes de `N_1`, a cena `abertura` de `levels/story.c` conserva as duas falas curtas de missão, sem repetir o monólogo:

1. Comando: “DAMIAO, AQUI E O PADRE. SEGURE O PATIO. TEM GENTE FUGINDO PELO FUNDO.”
2. Damião: “TO INDO. HOJE NINGUEM VAI PRO CEU ANTES DA HORA.”

As cenas da campanha mantêm seus próprios controles: A completa e avança; START pula a conversa.

## Voz

Damião fala com raiva, intimidade e humor seco. Chama os invasores de “baratas”, como apelido, sem mudar a identidade das famílias de inimigos. O palavrão tem alvo: a promessa que o explorou. Evitar transformar toda fala em piada ou escrever sotaque fonético. Comando é um padre que fala de pessoas, caminhos e tempo; Escorpião fala de corpos e posse. A religiosidade aparece no vocabulário cotidiano, no cuidado e no conflito, sem exigir uma explicação sobrenatural.
