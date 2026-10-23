# Preparação e guia da missão

Implementação da proposta visual aprovada em `proposta.png`, criada com a
ferramenta integrada de geração de imagens a partir da preparação original da
fase 7 e dos sprites do serra-pau roxo. A ROM usa os gráficos nativos do jogo.

A preparação apresenta nome da fase, objetivo, uma ameaça principal identificada
por nome, comportamento e orientação de combate, e uma dica curta. As informações
de rota continuam visíveis na preparação quando a fase tem uma consequência
específica. O guia também apresenta a orientação completa da missão.

- **A** na preparação: começar.
- **B** na preparação: abrir o guia da fase.
- **Esquerda/direita ou A** no guia: folhear, com retorno circular.
- **B ou START** no guia: voltar à preparação.

O guia contém a missão, os controles e uma ficha para cada inseto distinto do
roster real da fase. Consultá-lo não inicia a fase nem atualiza a simulação.

## Fontes

- Layout e navegação: `src/system/video/screens/mission.c`.
- Nomes, comportamento, tática e ameaça destacada: `mission_guide.h` na mesma pasta.
- Texto da missão: `art/interface-ux-v2/conteudo-aprovado.json`; executar seu
  `exportar.py` para atualizar `mission_copy.h`.
- Retratos: `python3 tools/build_mission_portraits.py`. O gerador amplia o atlas
  existente com vizinho mais próximo para 32×32, mantendo a paleta original.
  A preparação carrega 16 tiles por retrato; o novo atlas ocupa 7.680 bytes de ROM.
- Moldura e fundo preservados; seis tiles decorativos e o retrato usam a reserva
  reversível de VRAM já oferecida pelo painel.

## Validação

Build de produção e `python3 tools/check.py` passaram. Os relatórios em
`validation/ntsc/report.json` e `validation/pal/report.json` registram as 20
preparações em cada região e o SHA-256 da ROM validada. Capturas têm resolução
nativa de 320×224; `prep-7.png` corresponde à fase da proposta.

O teste verifica objetivo e dica sem cortes, retrato pertencente à fase,
retratos do guia iguais ao atlas, todas as páginas e retornos circulares,
simulação congelada, restauração exata da preparação e entrada no combate.
Também verifica pausa, ajuda, confirmação de saída e restauração da VRAM.
RAM acelera a seleção de fase e a derrota de preparação dos cenários; a navegação
das interfaces ocorre só pelo controle, com bloqueio de escritas de RAM no teste.

Na raiz do repositório:

```sh
make -C game -j4 OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_interface_emulator.py --output game/art/mission-ux-v1/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_interface_emulator.py --pal --output game/art/mission-ux-v1/validation/pal
```
