# Logo PLAGUEFALL no menu inicial

![Menu capturado na ROM](menu-3x.png)

O texto simples PLAGUEFALL foi substituído pelo **logo B — Ex-voto de metal**, com coração, cruz e nome estilizado. A versão compacta mede 128×88 e fica em x8/y0, acima das opções. O índice zero é transparente, preservando a arte da caatinga atrás do emblema.

A [nova arte](originals/plaguefall-menu-native-v2.png) foi recriada com **image_gen integrado** a partir do [concept aprovado](../concepts/titulo-v1/b-ex-voto.png), preservando coração, cruz, circuitos e a tipografia. O [prompt](prompt-menu-native-v2.txt) planeja a leitura no destino de 128×88: letras com hastes e espaços mais claros, contornos escuros opacos, metal com áreas maiores de cor e menos microtextura. O logo de abertura FinalQuest mantém a versão de corpo branco. O [exportador](export_logo.py) faz redimensionamento, quantização para uma paleta e empacotamento em 4bpp. [PNG nativo transparente](logo-native.png), [metadados](export.json).

A carga acompanha o fundo do menu, com display desligado: 122 tiles únicos/3904 bytes após os tiles do fundo, em PAL3. Na configuração atual ocupa os índices 1219..1340, antes da fonte SGDK em1440. Não usa sprites nem altera as duas paletas do cenário. O empacotamento compartilha tiles repetidos, preservando espaço para a [marca FinalQuest no canto inferior direito](../finalquest-logo-v2/README.md#crédito-no-menu-inicial). A saída do menu já regenera a PAL3 e os tiles do chão; voltar de ajuda/personagens recarrega o logo.

[ROM atualizada](../../out/rom.bin). Compilação isolada e conferência de pixels em PAL/NTSC realizadas com sucesso. A ROM foi exercitada no Genesis Plus GX em PAL e NTSC, com reprodução completa da abertura, navegação, ajuda, galeria e partida. Dez capturas de menu correspondem exatamente ao logo sobre o fundo original. As verificações da cartela de abertura e do monólogo também passaram.

```sh
python3 game/art/menu-logo-v1/export_logo.py --check
python3 game/art/menu-logo-v1/verify_pixels.py
```
