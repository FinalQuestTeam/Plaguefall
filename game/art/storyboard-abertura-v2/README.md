# Abertura — storyboard aprovado e integrado

Proposta de 21/10/2026 baseada no texto integral enviado pelo usuário, incluindo a provocação sobre o Diabo. Aprovado pelo usuário e integrado à ROM em 21/10/2026. [Vídeo e testes da integração](../intro-monologo-v2/README.md).

- [Prévia com reprodução e navegação por plano](revisao.html), sem áudio.
- [Prancha 1 — planos 01–08](prancha-01.png).
- [Prancha 2 — planos 09–14](prancha-02.png).
- [Roteiro completo: falas, enquadramentos, direção e tempos](../../doc/historia/storyboard-abertura-v2.md).
- [Fonte das falas e dos tempos](storyboard.json).
- [Conferência de leitura e preservação do jogo](validation.json).

São **14 planos, 18 cartelas e 101 segundos**, com fades incluídos nas durações. Os planos 08, 11, 12 e 13 têm duas cartelas sobre uma mesma imagem; as trocas de legenda não reiniciam a imagem nem a música.

## Arte

Dez ilustrações anteriores foram reorganizadas e reenquadradas a partir das [pranchas originais](../storyboard-abertura-v1/README.md). O card 06 mostra os ovos na carga; o 09 foi refeito com a prótese esquerda no centro; o 10 mostra as pessoas abrigadas na capela; o 13 mostra a retirada pelos fundos. As novas artes foram produzidas com **image_gen integrado**, com as pranchas existentes como referência. Os [prompts iniciais](prompts.json) e os [prompts da revisão dos cards 09 e 10](prompts-revisao-09-10.json) ficam nesta pasta.

- `novos-cards-fonte.png`: fonte gerada com dois estudos; o superior é usado no card dos ovos. O estudo inferior foi substituído na montagem por uma composição própria em formato de tela.
- `retirada-fonte-v2.png`: arte escolhida para a retirada, com todos os civis saindo para a esquerda. A versão anterior permanece em `retirada-fonte.png`.
- [Prompt da correção de saída no plano 13](prompt-revisao-saida-13.json), feita com image_gen integrado.
- `braco-fonte-v2.png`: novo close da prótese esquerda para o plano 09.
- `abrigo-fonte-v3.png`: comunidade dentro da capela para o plano 10, com os três homens diferenciados por idade, rosto, cabelo, porte e roupas. A versão anterior permanece em `abrigo-fonte-v2.png`.
- [Prompt da revisão dos homens no plano 10](prompt-revisao-pessoas-10.json), feita com image_gen integrado.
- [Revisão dos planos 09 e 10 lado a lado](revisao-09-10.png).
- `quadros/`: recortes da proposta, em 640×352, para a prévia e as pranchas. A versão quantizada para o VDP está em `../intro-monologo-v2/`.

Não há nova dublagem. As indicações de chiado, efeitos e interpretação são direção para a próxima etapa. A partitura foi estendida e reorganizada para uma reserva de 108 segundos, incluindo 4s de logo, 101s de monólogo e 3s de sustentação.

## Reprodução da revisão

Na raiz do projeto:

```sh
python3 game/art/storyboard-abertura-v2/build_review.py
```

O script usa Pillow e fontes locais do macOS. Gera somente o roteiro desta revisão, as pranchas e a prévia HTML. Os hashes da fase de revisão continuam preservados. Após a aprovação, a validação da ROM e dos recursos passa a ser a da pasta `intro-monologo-v2`.

O exportador de produção em `../intro-monologo-v2/export_intro.py` lê `storyboard.json`. A montagem anterior permanece preservada em `intro-monologo-v1` como histórico.
