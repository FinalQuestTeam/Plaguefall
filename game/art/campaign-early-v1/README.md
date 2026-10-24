# Campanha — igreja, rua e galpão

Implementação das fases 1, 2A, 2B, 3, 4 e 5 segundo o tratamento da história.
O código deste grupo está em `src/levels/campaign_early.c/.h`, nos includes
`campaign_early_*.inc` e nas seis definições de fase correspondentes.

| Fase | Objetivo | Mundo | Atlas | Inimigos simultâneos | Tiros por lado |
|---|---|---:|---:|---:|---:|
| 1 | Sobreviver 90 s, apenas perseguidor básico | 512×384 | 640 | 4 | 6 |
| 2A | Eliminar 15, introduzir atirador | mesmo pátio | 640 | 4 | 6 |
| 2B | Eliminar 15 entre destroços sólidos | mesmo pátio | 622 | 4 | 6 |
| 3 | Alcançar o galpão | 2560×320 | 599 | 4 | 6 |
| 4 | Eliminar 20 no galpão seco | 512×384 | 372 | 4 | 6 |
| 5 | Proteger a Santa por 120 s; 180 HP | 384×384 | 606 | 3 | 6 |

[Prévias e playtests](review.html) · [Metadados e geometria](manifest.json) ·
[NTSC](validation/ntsc/report.json) · [PAL](validation/pal/report.json).

## Arte e coerência

- 1 e 2A usam literalmente o pátio aprovado, mantendo o mesmo mundo. A troca
  visual após bomba continua no mecanismo já existente do pátio.
- 2B preserva o pátio danificado e acrescenta três montes de telhas/pedras;
  as bases de 40×16 bloqueiam pés, mas deixam tiros passarem acima.
- 3 remonta módulos urbanos aprovados, sem repetir salas inteiras. Os marcos
  incluem a capela, reservas vazias, portões azuis e a chegada ao galpão.
- 4 usa a estrutura azul, redes, farmácia e reserva de água do abrigo anterior.
  A lava e a Santa antecipada foram removidas. Duas pilhas altas de carga
  bloqueiam pés e tiros pelas bases visíveis.
- 5 substitui a capela de fundo pela mesma estrutura industrial; preserva a
  Santa nativa, seu pedestal, cabo, restauração do piso e brilho da coroa.
- Não há tiles aproximados para caber no orçamento. O empacotamento mantém
  exatamente cada tile final de 8×8. Módulos industriais foram convertidos
  para a paleta de cada cenário antes da deduplicação.

O novo monte de entulho foi criado pelo **skill imagegen**, ferramenta integrada
`image_gen.imagegen`, com fundo realmente transparente. Fonte preservada em
[source/rubble.png](source/rubble.png), redução única em
[source/rubble-native.png](source/rubble-native.png), prompt e registro em
[prompts.json](prompts.json). A normalização de tamanho/paleta e a composição
nos mapas são passos de exportação, sem desenho de pixels procedurais.

## Verificação e limites

O exportador testa todas as posições caminháveis na grade de 8 pixels com
corpo de 16×16. Os caminhos livres de cada fase formam uma única região, sem
ilhas nem saídas inacessíveis. Os relatórios do emulador conferem limites,
colisão dos quatro lados, atlas efetivo na VRAM e retorno da câmera, além de
carga com o teto declarado de inimigos e seis tiros de cada lado.

As partidas automáticas usam apenas o controle após a preparação do estado:
vida, dano, mortes, itens e objetivos seguem a lógica normal. Resultados de
vitória e derrota são amostras de um controlador automático; não equivalem a
uma avaliação humana definitiva de dificuldade. Os ensaios isolados de carga,
colisão e abandono da Santa usam escritas explícitas na RAM para preparar
situações, separadas das partidas.

A versão inicial apresentou um pico de custo e pressão na defesa da Santa.
O teto foi reduzido de quatro para três inimigos, e os inimigos de investida
foram retirados das fases 4/5 para evitar sua introdução prematura. Os números
finais estão nos relatórios. A aprovação dos checks significa correção desses
contratos; não significa 60/50 FPS fixos sob toda carga, nem vitória do bot em
cada tentativa. Não houve teste em console físico.

A ROM isolada em `/tmp/plaguefall-early-build/game/out/release` testa este
conjunto e não substitui a ROM integrada. Para evitar dependências transitórias
nos agentes paralelos, os módulos de missão dos demais grupos foram excluídos
apenas do snapshot temporário e as definições 6/6B/12 ali usam a versão HEAD.
O checkout compartilhado conserva todas as mudanças dos demais grupos.

## Reprodução

Na raiz do repositório:

```sh
python3 game/art/campaign-early-v1/build.py
arch -x86_64 /usr/bin/python3 game/art/campaign-early-v1/test_emulator.py --build-dir game/out/release --matches 2 --movie
arch -x86_64 /usr/bin/python3 game/art/campaign-early-v1/test_emulator.py --build-dir game/out/release --matches 2 --pal
```

O Makefile aceita `OUT_DIR`, porém a etapa `padROM` também escreve
`out/rom.bin`, e o rescomp publica cabeçalhos em `res/`. Para builds paralelos,
use uma cópia própria do diretório `game` com `GDK` apontando para o SGDK do
checkout. Para compilar apenas o núcleo da ROM dessa cópia sem dependências
editoriais do empacotador:

```sh
make -C /tmp/plaguefall-early-build/game GDK=/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/SGDK -j4 out/release/rom.bin out/release/symbol.txt
```
