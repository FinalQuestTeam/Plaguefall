# Inimigos Darkspace — câmera elevada a 60° — v2

Reinterpretação dos mesmos 15 inimigos com a câmera solicitada: **60° acima do
chão**, olhando para baixo. Projeção ortográfica; orientação artística da câmera
em 45° no plano; personagens voltados para a diagonal inferior direita da tela.
Os originais laterais de `../darkspace-v1/` foram preservados.

O objetivo é mostrar mais os topos de capacetes, ombreiras, caldeiras e armas,
com tronco e pernas encurtados pela vista de cima. A ferramenta `image_gen`
redesenhou a geometria das poses com referências de identidade e de câmera;
não foi aplicada rotação ou deformação ao desenho lateral para simular a vista.

## Arquivos

- `gfx/`: 15 PNGs indexados de 4 bits, **192×96**, células **32×48**, alfa binário.
- Linha 0: quatro poses de repouso e duas células completamente transparentes.
- Linha 1: seis poses de corrida voltadas para a diagonal inferior direita.
- Paleta idêntica de **15 cores visíveis + índice 0 transparente** em todas as folhas.
- `palette.json` / `palette.gpl`: índices RGB e palavras de cor VDP.
- `enemies.res`: declarações reais de recursos SGDK, separadas das imagens.
- `previews/`: folhas ampliadas 6× e catálogo/GIFs ampliados 4×, por vizinho mais próximo.
- `originals/`: cópias intactas das imagens geradas, acima da resolução de exportação.
- `manifest.json`: câmera, descrições dos inimigos, referências e prompts utilizados.
- `validation/`: relatório técnico, log do ResComp e prévias de divisão em peças VDP.

Inimigos: **Torreão, Batedor, Baluarte, Aríete, Fuzileiro, Caçador, Escudeiro,
Adaga, Artilheiro, Alcateia, Fortaleza, Meteoro, Dummy, Alvo e Lacraia**.

Vermelho identifica atiradores, amarelo perseguidores, roxo blindados e laranja
unidades de investida; os alvos de treinamento usam cinza. Aço e latão são comuns
a todas as famílias.

## Critério de câmera para o jogo

A exigência de **60° acima do chão** vale para o conjunto do jogo. Chão, jogador,
paredes, antena, itens, projéteis e efeitos devem usar o mesmo enquadramento e
ponto de contato no piso. As folhas desta entrega cobrem os inimigos na direção
inferior direita, seguindo a estrutura de dez poses do pedido original.

Para implementar essa direção visual no runtime:

1. Separar a posição no piso da altura visual e da origem do sprite nos pés.
2. Projetar chão, objetos, trajetórias e efeitos com a mesma transformação.
3. Ordenar sobreposições pela profundidade do ponto de apoio no piso.
4. Desenhar vistas adicionais para as outras direções de movimento/tiro.
   Espelhamento horizontal pode fornecer o par inferior esquerdo. **Espelhamento
   vertical e rotação plana não geram vistas de costas corretas** nessa câmera.
5. Adaptar os sprites atuais quadrados/rotacionados para as novas células 32×48,
   considerando divisão de peças, paletas e consumo total por linha.

O código atual de `enemygfx.c`/`spritelist.c`, o chão e a ROM não foram alterados
nesta etapa de arte. O pacote não equivale à migração do jogo completo para a nova
perspectiva, nem inclui as oito direções de cada inimigo.

## Exportação e limites

O gerador produz imagens maiores que a resolução pedida. A exportação técnica
extrai as poses, usa uma escala uniforme por personagem e **vizinho mais próximo**,
registra a base dos pés em `y=46` no repouso e fixa paleta/índice transparente.
Não há suavização ou alfa intermediário nos PNGs de `gfx/`.

**60° é o alvo da direção artística**, não uma medição certificada de um modelo
3D. A geração 2D pode variar no encurtamento entre personagens e frames; conferir
os volumes, articulações e contato dos pés no editor de pixel art antes da arte
de produção. A compilação de recursos verifica formato, paleta, número de frames
e peças de hardware; não certifica geometria de câmera nem continuidade anatômica.

## SGDK

```text
SPRITE enemy_torreao "gfx/torreao.png" 4 6 FAST 6 NONE BALANCED FAST
```

As outras 14 declarações estão em `enemies.res`. O modelo literal do pedido é:

Validação desta versão: **15 folhas / 150 frames**, com **4 + 6 poses** por
inimigo, paleta compartilhada e transparência no índice 0. O **ResComp 4.02**
compilou os arquivos finais com sucesso, usando **1 a 3 peças VDP por frame**.
Não houve teste de cena completa ou integração na ROM.

```text
SPRITE heroi "gfx/heroi.png" 4 6 FAST 6 NONE BALANCED FAST
```

`heroi.png` é um nome de exemplo; os arquivos entregues têm os nomes dos inimigos.

Na raiz do repositório, reproduzir exportação e validação com:

```sh
python3 game/art/darkspace-iso60-v2/export_sheets.py
python3 game/art/darkspace-iso60-v2/validate_sheets.py
```

O pacote ZIP contém as artes nativas, paleta, recursos, documentação, prompts,
prévia e relatório. Os originais e scripts ficam também nesta pasta do projeto.
