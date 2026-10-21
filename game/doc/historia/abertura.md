# Abertura — o sonho atendido

## Monólogo

> Você já ouviu falar que o Diabo dá tudo que a gente quer?
> Mas sempre da maneira mais filha da puta possível?
>
> Eu sonhava com astronautas, extraterrestres e foguetes.
> ... É. agora tô assim.
>
> As naves voltaram. Quem foi nelas, não.
> Aquelas merdas vieram também. Cheio de patas, asas e aquele zumbido.
> Pra mim, é tudo barata.
> E os foguetes pousam de pé, no mesmo lugar de onde saíram.
> A diferença é que agora descarregam ninhos.
>
> Eu consertava essas máquinas. Achava que um dia iam me deixar subir.
> Subi foi na lista de quem eles querem matar.
>
> Já foi um braço e quase uma perna, mas esse povo precisa de mim!
> Minha mãe ainda manda eu levar uma reza.
> Eu levo. Junto com a munição.

**Rádio — Comando, o padre:** “Damião. Aqui é o padre. Tá me ouvindo? Eles chegaram no pátio. Tem gente saindo pelo fundo.”

**Damião:** “Tô ouvindo. Hoje ninguém vai pro céu antes da hora.”

O texto mantém a provocação e o palavrão do conceito original. A volta das naves sem seus ocupantes prepara a chegada dos invasores; os foguetes trazem ninhos, e o braço perdido reforça o custo de proteger a comunidade. Damião não narra a extinção do país: ele está segurando uma passagem para alguém conseguir viver.

## Encenação proposta

O primeiro som seria uma transmissão de pouso interrompida por estática. Uma propaganda antiga promete “ASCENSÃO: O CÉU É PARA TODOS”. A voz de Damião atravessa o anúncio. No corte para o presente, os motores iluminam antenas improvisadas, telhas, reservatórios e uma capela espremida entre instalações industriais. A carga do foguete se mexe por dentro.

“... É. agora tô assim” apresenta o corpo inteiro de Damião: rosto exposto, chapéu metálico, braço esquerdo cibernético, tecido e placas recuperadas. O contraste é entre a promessa de acesso ao espaço e o trabalhador que ficou recolhendo os destroços dela.

O [storyboard em 12 planos](storyboard-abertura.md) já foi integrado à ROM como [abertura animada](../../art/intro-monologo-v1/README.md), entre o logo FinalQuest e o menu. Usa as imagens das pranchas com recortes próprios para 320×176, enquadramento estável, fades e legendas brancas centralizadas sobre preto. A borda inferior da arte escurece gradualmente; poeira, brasa e fuligem se movem sobre a imagem com câmera fixa; não há nome, contador nem instruções na tela. O áudio reaproveita a música existente e um breve chiado de rádio; as falas são apresentadas em texto.

## Versão da ROM

O monólogo completo acima toca uma vez no boot, nos 12 planos, com aproximadamente 1min30s de reprodução automática incluindo as trocas de imagem. A duração de cada plano considera 50 ou 60Hz. A completa o texto em curso; um novo toque avança ao próximo plano com fade. START pula a sequência inteira. Segurar um botão não dispara novos avanços nem inicia a partida no menu.

Antes de `N_1`, a cena `abertura` de `levels/story.c` mantém apenas as duas falas de missão, evitando repetir o monólogo:

1. Comando: “DAMIAO, AQUI E O PADRE. SEGURE O PATIO. TEM GENTE FUGINDO PELO FUNDO.”
2. Damião: “TO INDO. HOJE NINGUEM VAI PRO CEU ANTES DA HORA.”

As outras cenas da campanha mantêm seus retratos e falas. A completa o texto e avança; START pula a cena. Voltar ao menu pela pausa não repete a animação de boot.

## Voz

Damião fala com raiva, intimidade e humor seco. Chama os invasores de “baratas”, como apelido, sem mudar a identidade das famílias de inimigos. O palavrão tem alvo: a promessa que o explorou. Evitar transformar toda fala em piada ou escrever sotaque fonético. Comando é um padre que fala de pessoas, caminhos e tempo; Lacraia fala de corpos e posse. A religiosidade aparece no vocabulário cotidiano, no cuidado e no conflito, sem exigir uma explicação sobrenatural.
