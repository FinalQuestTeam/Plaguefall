# Escorpião — leques completos

A fase 16 mantém quatro tiros simultâneos para Damião e passa a permitir dez tiros inimigos, por um limite independente em `LevelDef.enemyShotCap`. As outras fases usam o limite anterior quando esse campo é zero. O teto global dos pools permanece em dezesseis.

O chefe verifica cinco vagas livres antes de disparar. Se não houver espaço para o leque inteiro, aguarda com o disparo pronto e tenta novamente nas atualizações seguintes. Não apaga projéteis vivos e não dispara apenas um lado do leque. Cada bala mantém o dano 13, a direção e a arte existentes; a cadência após um disparo completo continua em 1,2 segundo.

[Relatório da ROM](delivery.json) · [NTSC](validation/ntsc/report.json) · [PAL](validation/pal/report.json).

Os ensaios na ROM real conferem cinco velocidades distintas e simétricas, dano e estilo, duas rajadas no pool, espera com apenas quatro vagas, disparo assim que cinco vagas abrem e preservação dos tiros anteriores. A primeira rajada é imobilizada por RAM no ensaio de coexistência para impedir que suas balas externas colidam com a sala antes da próxima. Outros ensaios preparam ocupação e temporizadores por RAM; a IA de produção gera os disparos. O limite de Damião é conferido por autofire com potência cinco, mantendo no máximo quatro tiros.

A mesma suíte confere 28 câmeras, cenário e equipamentos em VRAM, travessia, colisões, pausa, derrota/reinício e vitória por controle contra o chefe original. O ensaio de vitória aumenta vida e proteção do jogador uma vez; não altera a vida do chefe. Hardware físico não testado.

```sh
arch -x86_64 /usr/bin/python3 game/tools/test_phase16_shipyard_emulator.py --output game/art/boss-shots-v1/validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase16_shipyard_emulator.py --pal --output game/art/boss-shots-v1/validation/pal
python3 game/tools/check.py
```

Este pacote registra a correção inicial dos disparos. A segunda fase foi implementada posteriormente em [boss-phase2-v1](../boss-phase2-v1/README.md), com sua própria ROM e validação.
