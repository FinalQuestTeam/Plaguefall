# Desempenho e hitbox — arte por tamanho

A memória e as caixas foram corrigidas e verificadas, mas o gargalo com quinze inimigos ainda existe.

| Inimigos | Célula uniforme 32×48 | Tamanho nativo, HUD antigo | Tamanho nativo, HUD 10 Hz | CPU final média |
|---:|---:|---:|---:|---:|
| 3 | 60 FPS | 60 FPS | 60 FPS | 53.91% |
| 8 | 40.5 FPS | 51.75 FPS | 60 FPS | 78.64% |
| 15 | 30 FPS | 30 FPS | 31.75 FPS | 121.01% |
| 16 | 30 FPS | 30 FPS | 30 FPS | 125.82% |

O caso de quinze ficou em 31,75 FPS; a redução de sprites/transferências não foi suficiente para 60 FPS com toda a lógica. A melhora com oito resulta tanto dos sprites menores quanto da retirada dos textos redundantes: não é atribuída apenas à economia de memória. O teste isolado com dezesseis inimigos de 32×32 manteve 60 FPS.

Método: Genesis Plus GX libretro instalado, 120 VBlanks de aquecimento e 240 por caso. O contador de quadros do jogo é comparado ao vtimer, com carga média/p95 do SGDK. Posições, HP e temporizadores são restabelecidos na RAM volátil para manter a amostra comparável; as animações continuam mudando. O teste completo usa Batedores e executa lógica, terreno e HUD; o isolado congela a lógica. O contador do vídeo do emulador sozinho não mede os quadros perdidos pelo jogo. Carga acima de 100% significa trabalho excedendo um intervalo de quadro.

A tabela preserva etapas intermediárias com seus próprios hashes. Os resultados finais e as provas de colisão têm o hash da ROM atual. Combate natural, todos os comportamentos misturados, muita sobreposição e console físico não são garantidos por esta amostra.

- [Uniforme antes desta etapa](../../../cangaco-insects-iso60-v2/validation/performance/reduced-gameplay.json).
- [Tamanho nativo antes do ajuste do HUD](../gameplay.json).
- [Jogo completo final](../gameplay-final.json).
- [Renderização isolada 32×32](../render32.json).
- [600 casos reais de colisão e 120 geometrias SAT](../emulator-combat.json).
- [Teste funcional de 1159 VBlanks](../emulator/report.json).

Comandos de reprodução, na raiz da worktree:

```sh
arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-iso60-v2/tests/smoke_emulator.py --benchmark --gameplay --counts 1,3,8,15,16 --output game/art/cangaco-insects-sized-v3/validation/gameplay-final.json
arch -x86_64 /usr/bin/python3 game/art/cangaco-insects-iso60-v2/tests/smoke_emulator.py --combat --output game/art/cangaco-insects-sized-v3/validation/emulator-combat.json
```

SHA-256 atual: `b3281bf4fa08aa695882547305607524e148a9988b5c4c224bebc7a69014d241`.
