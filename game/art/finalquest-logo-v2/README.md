# FinalQuest — logo reconstruído

![Logo no Mega Drive](../intro-monologo-v1/emulator-ntsc/logo.png)

O controle inclinado, a cruz direcional e o ponto de exclamação laranja preservam a identidade do logo original. A marca foi redesenhada com traços mais fortes e letras claras diretamente sobre preto, sem a antiga placa branca atrás do nome. A grafia estilizada **F!nalQuest** mantém o acento laranja da referência.

Arte reconstruída com **image_gen integrado**, a partir da [referência original](../../src/img/finalquest.png). O splash usa a [arte com o controle branco](originals/finalquest-menu-white-v2.png) e seu [prompt](prompt-menu-white-v2.txt). O crédito pequeno do menu tem uma adaptação própria para leitura na resolução nativa, descrita abaixo. O [prompt anterior](prompt.txt) e a [primeira reconstrução](originals/finalquest.png) continuam preservados. A fonte atual mede1536×1024; o [exportador](export_logo.py) recorta pelo alfa, compõe sobre preto e quantiza para uma paleta fixa de16 cores do Mega Drive.

- [PNG nativo192×128](logo-native.png) e [ampliado3×](logo-3x.png).
- [Dimensões e hashes](export.json).
- [Abertura completa gravada no emulador](../intro-monologo-v1/abertura.mp4).
- [ROM](../../out/release/rom.bin).

O desenho ocupa168×120 dentro de uma moldura192×128, centralizada em320×224. São384 tiles temporários, em PAL2. O splash usa0,2s para entrar,1s de exibição e0,2s para sair, em50/60Hz, além da carga da arte. A/B/C/START continuam permitindo pular; não fica um fade pendente para a próxima tela.

O cabeçalho `src/system/video/sprites/logo_data.h` é consumido pelo splash existente. Tanto este exportador quanto `art/title-caatinga-v1/export_title.py` geram o mesmo logo; o comando antigo não repõe a redução de baixa resolução. A versão histórica anterior continua no Git e em `title-caatinga-v1/legacy/`.

```sh
python3 game/art/finalquest-logo-v2/export_logo.py
python3 game/art/finalquest-logo-v2/export_logo.py --check
```

A [comparação com capturas PAL/NTSC](../intro-monologo-v1/pixel-validation.json) confere todos os pixels do logo e sua centralização, além da abertura e do menu.

## Crédito no menu inicial

![FinalQuest no canto inferior direito](../menu-logo-v1/menu-3x.png)

O menu mantém a marca em **56×40 pixels**, em x256/y176, com margem externa de 8 pixels e a redução de 30% solicitada. O desenho recupera o controle inclinado original, seu corpo branco, direcional com quatro pontos, botões, aros e exclamação laranja. O nome usa a versão com mais definição aprovada pelo usuário: F!nalQuest com letras de 7 pixels na grade nativa, branco sólido, exclamação laranja de 2 pixels de largura e contorno escuro de 1 pixel. O fundo externo é transparente; as áreas pretas internas continuam opacas.

A nova [arte de menu](originals/finalquest-menu-faithful-v4.png) foi recriada com **image_gen integrado**, tomando a marca original e a reconstrução de corpo branco como referências. O [prompt](prompt-menu-faithful-v4.txt) especifica o destino de 56×40 pixels, as proporções e os contornos da marca. O controle mantém os pixels da arte aprovada. O exportador substitui apenas a área do nome pelo letreiro nativo de 7 pixels, restaurado a pedido do usuário. A fonte da abertura permanece a versão aprovada de corpo branco.

O [exportador](export_menu_logo.py) converte a arte diretamente para o arquivo nativo de 56×40, usando uma moldura interna de 50×36 pixels. São **30 tiles únicos / 960 bytes**, nos índices 1341..1370, após o título PLAGUEFALL e antes da fonte em 1440. A marca usa PAL0 e preserva o branco do texto no índice 15. A saída do menu restaura a paleta do jogo; ajuda, galeria e partida recarregam o crédito ao retornar.

[Imagem nativa](menu-credit-native.png) e [metadados de exportação](menu-credit-export.json). A compilação isolada e dez capturas reais PAL/NTSC conferiram os logos após reprodução, pulo da abertura e retorno de partida, galeria e ajuda.

```sh
python3 game/art/finalquest-logo-v2/export_menu_logo.py --check
python3 game/art/finalquest-logo-v2/verify_menu_pixels.py
```
