# Tela de seleção — caatinga e resistência

![Splash art original](originals/title-caatinga.png)

Nova arte do menu principal de RedRex: Rex, Dinorah e o padre Comando na caatinga, com mandacarus, vegetação seca, capela, torres de comunicação e insetos biomecânicos. O padre mantém a cabeça descoberta. A área escura à esquerda recebe as opções existentes do jogo; o nome e as opções são texto do VDP, separados da imagem.

Criada com **image_gen integrado**, usando os concepts aprovados dos três personagens e dos serra-paus como referência de identidade e materiais. O [prompt completo](prompt.txt) registra a composição e as referências. A fonte tem 1499×1049 pixels, com fundo opaco.

## No Mega Drive

- [Imagem nativa 320×224](title-native.png) / [prévia ampliada 3×](title-3x.png).
- [Menu capturado no emulador](emulator/menu-2x.png).
- [Logo menor capturado no emulador](emulator/logo-2x.png).
- [ROM atual](../../out/release/rom.bin).

O menu continua oferecendo **NOVO JOGO / COMO JOGAR / PERSONAGENS / FASE TESTE**. Todo o texto fica à esquerda em branco, incluindo o título e o cursor `>` que identifica a opção selecionada. A arte usa PAL1 e PAL2, com uma paleta de 16 cores por tile e 23 cores RGB efetivamente presentes nesta exportação. O texto usa PAL0; a seleção é indicada pelo cursor, sem trocar a cor das letras. As paletas do jogo são restauradas ao sair do menu.

A tela continua usando 1120 tiles / 35840 bytes temporários de VRAM, o mesmo espaço do fundo anterior. A conversão agrupa tiles entre duas paletas e aproxima as cores aos oito níveis RGB do hardware. Redimensionamento e quantização são técnicos; o script não desenha personagens, cactos ou insetos.

## Logo FinalQuest

O logo original foi reduzido proporcionalmente para **75%**: de 192×176 para **144×132**, centralizado numa moldura de **144×136** alinhada aos tiles. Mantém desenho e paleta, com os mesmos fades e controles para pular a abertura.

O uso temporário passa de 528 para 306 tiles, uma redução de 7104 bytes de VRAM durante a abertura. O char-map anterior está preservado em `legacy/logo_data.h`; a geração do logo reduzido parte desse arquivo, sem substituir a identidade da marca.

## Reprodução e validação

```sh
python3 game/art/title-caatinga-v1/export_title.py
python3 game/art/title-caatinga-v1/export_title.py --check
```

O exportador usa Pillow e NumPy e gera `logo_data.h` / `titlebg_data.h`. O [relatório de assets](validation.json) registra paletas, dimensões e hashes; o [relatório da ROM](build-validation.json) registra a compilação e memória; o [teste do Genesis Plus GX](emulator/report.json) registra a navegação.

A conferência inclui a abertura, as quatro opções, ajuda, galeria, sandbox e início da campanha. O teste compara os pixels da arte ao retornar ao menu. A entrada da tela restaura o backdrop preto, evitando que o fundo cinza da galeria altere as áreas transparentes da imagem.
