# Abertura aprovada — 14 planos e 18 cartelas

O [storyboard revisado](../../doc/historia/storyboard-abertura-v2.md) foi aprovado e integrado à ROM em **21/10/2026**. O boot segue **FinalQuest → APRESENTA → logo Plaguefall → monólogo → menu**.

- [ROM principal](../../out/release/Plaguefall.bin).
- [Vídeo da reprodução real no Genesis Plus GX](emulator-ntsc/abertura.mp4).
- [Montagem na paleta do Mega Drive](contact-sheet.png).
- [Exportação: textos, quebras, tempos, fontes e hashes](export.json).
- [Validação NTSC](emulator-ntsc/report.json), [PAL](emulator-pal/report.json), [pixels](pixel-validation.json) e [compilação](build-validation.json).
- [Trilha contínua estendida](../audio-abertura-v3/README.md).

São **101 segundos de exibição**, incluindo fades, em **14 imagens e 18 cartelas**. Os planos 08, 11, 12 e 13 trocam apenas a legenda; a imagem permanece carregada, a poeira continua se movendo e a música segue no mesmo relógio. As falas são apresentadas em texto, sem nova dublagem.

A montagem inclui as revisões aprovadas: a provocação sobre o Diabo, o ofício imediatamente após o sonho, os ovos na carga, o close da prótese esquerda, os civis com aparências diferentes, a reza no bolso da munição, os recortes limpos do terço e do padre e a saída dos civis para a esquerda.

## Conversão e reprodução

O exportador lê `art/storyboard-abertura-v2/storyboard.json` e usa os mesmos arquivos de origem e recortes da prévia. A área visível mantém a proporção aprovada de **320×176**; os oito pixels invisíveis de cada lado são preenchimento, sem cortar mais a composição. O campo armazenado é de **336×176**, com **924 tiles / 29568 bytes** e duas paletas por imagem. Somente uma imagem ocupa a VRAM por vez.

O texto usa até **36 colunas × 4 linhas**, branco centralizado sobre preto, com digitação a 36 caracteres por segundo. A troca de cartela limpa toda a área de legenda antes do novo texto. A parte inferior da arte conserva a transição suave para preto; a câmera permanece fixa, com 12 partículas de poeira, brasa e fuligem.

**Somente START pula** a sequência inteira. A/B/C não avançam nem completam legendas. Segurar START não inicia uma partida no menu. A abertura toca uma vez por boot; voltar ao menu pela pausa não a repete. A conversa curta de missão antes da fase 1 permanece independente.

## Reprodução dos testes

Na raiz do projeto:

```sh
python3 game/art/intro-monologo-v2/export_intro.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/art/intro-monologo-v2/verify_emulator.py \
  --rom game/out/release/rom.bin --symbols game/out/release/rom.out \
  --output game/art/intro-monologo-v2/emulator-ntsc \
  --opening-audio game/art/intro-monologo-v2/emulator-ntsc/opening.wav --movie
arch -x86_64 /usr/bin/python3 game/art/intro-monologo-v2/verify_emulator.py \
  --rom game/out/release/rom.bin --symbols game/out/release/rom.out \
  --output game/art/intro-monologo-v2/emulator-pal \
  --opening-audio game/art/intro-monologo-v2/emulator-pal/opening.wav --pal
python3 game/art/intro-monologo-v2/verify_pixels.py
```

Os testes enviam entradas de controle e leem o estado do emulador, sem escrever na RAM do jogo. Conferem todos os 14 planos e as 18 cartelas nas duas regiões, a continuidade do relógio musical, a limpeza das legendas, as partículas, START, A/B/C, menu, galeria, missão, início da fase 1 e retorno ao menu. A comparação de pixels verifica 56 fundos e 36 capturas de cartela, permitindo diferenças somente nos sprites de partículas, inclusive no quadro em que reaparecem na borda.

As artes e capturas da [versão anterior](../intro-monologo-v1/README.md) ficam preservadas como histórico. O exportador atual é o desta pasta.
