# Fase 10 — O berçário da fábrica

[Composição completa, ovos, capturas, ROM e limitações](review.html).

Sala768×544, com352px úteis de altura (antes160). Seis grupos de props: esteira/bancada, bomba com tanque, compressor, palete de caixas, barris e suprimentos. Dez conjuntos de ovos em posições variadas, com aproximações de tiro verificadas. Todos os3.277 pontos livres da malha estão conectados; no máximo6dos7slots são solicitados pelas câmeras.

A [imagem completa](source/factory-whole.png) foi criada com ImageGen integrado a partir da identidade industrial anterior e da fase9. [Prompt exato](prompts/whole-factory.txt). `export.py` extrai conjuntos completos, remove o concreto conectado ao exterior das silhuetas e monta materiais repetíveis em grade nativa1px e paleta16cores. Pisos sem linhas artificiais repetidas; paredes não repetem painéis/armários inteiros a cada coluna.

1.147 padrões exatos /36.704bytes na ROM, mapa13.056bytes. Cache320 + ovos150 =470/640tiles /15.040bytes residentes; heap4.854bytes. Sem aproximação de tiles. Resolução de saída320×224 preservada.

A fase10 usa `CF_FACTORY_NEST` e âncoras geradas em `phase10_layout.h`. A fase11 agora compartilha este cenário, com seis válvulas e barra de operação; veja a [revisão própria](../phase11-factory-v2/review.html). `build_campaign_factory.py` preserva a exportação histórica e aponta a composição ativa da10 para esta pasta. O teste compartilhado delega9,10e11 às suítes nativas.

Os dez ovos foram destruídos por controle após isolamento da pressão inimiga. Pixels de cenário/ovos, contatos, limites, slots, bomba, pausa e persistência passaram NTSC/PAL. Carga com quatro inimigos e6+6tiros:56,25–60FPS NTSC;49,55–50FPS PAL. Há quedas no trecho central. Dificuldade humana e hardware físico não certificados.

```sh
python3 game/art/phase10-factory-v2/export.py --check
python3 game/tools/build_campaign_factory.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase10_factory_emulator.py --output /private/tmp/phase10-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase10_factory_emulator.py --pal --output /private/tmp/phase10-pal
```

ROM da revisão original da fase10: `f7716cb329bee0dee223e2249cfac3ff5fb54e9d6bcb1b8bedd6b798f388beed`. GitHub atualizado até a fase9 em5ad7f971; as revisões da10/11 não foram enviadas. A ROM atual e suas regressões estão no [relatório da fase11](../phase11-factory-v2/delivery.json).
