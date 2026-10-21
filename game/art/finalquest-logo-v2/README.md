# FinalQuest — logo reconstruído

![Logo no Mega Drive](../intro-monologo-v1/emulator-ntsc/logo.png)

O controle inclinado, a cruz direcional e o ponto de exclamação laranja preservam a identidade do logo original. A marca foi redesenhada com traços mais fortes e letras claras diretamente sobre preto, sem a antiga placa branca atrás do nome. A grafia estilizada **F!nalQuest** mantém o acento laranja da referência.

Arte criada com **image_gen integrado**, a partir de [finalquest.png](../../src/img/finalquest.png). O [prompt completo](prompt.txt) e o [original gerado](originals/finalquest.png) estão preservados. A fonte gerada mede1536×1024; o [exportador](export_logo.py) recorta a margem preta e quantiza o desenho para uma paleta fixa de16 cores do Mega Drive.

- [PNG nativo192×128](logo-native.png) e [ampliado3×](logo-3x.png).
- [Dimensões e hashes](export.json).
- [Abertura completa gravada no emulador](../intro-monologo-v1/abertura.mp4).
- [ROM](../../out/release/rom.bin).

O desenho ocupa165×120 dentro de uma moldura192×128, centralizada em320×224. São384 tiles temporários, em PAL2. O splash usa0,2s para entrar,1s de exibição e0,2s para sair, em50/60Hz, além da carga da arte. A/B/C/START continuam permitindo pular; não fica um fade pendente para a próxima tela.

O cabeçalho `src/system/video/sprites/logo_data.h` é consumido pelo splash existente. Tanto este exportador quanto `art/title-caatinga-v1/export_title.py` geram o mesmo logo; o comando antigo não repõe a redução de baixa resolução. A versão histórica anterior continua no Git e em `title-caatinga-v1/legacy/`.

```sh
python3 game/art/finalquest-logo-v2/export_logo.py
python3 game/art/finalquest-logo-v2/export_logo.py --check
```

A [comparação com capturas PAL/NTSC](../intro-monologo-v1/pixel-validation.json) confere todos os pixels do logo e sua centralização, além da abertura e do menu.
