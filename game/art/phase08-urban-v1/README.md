# Fase 8 — Feira urbana comprometida

[Composição completa, capturas e ROM](review.html). Reutiliza o cenário nativo atual da fase 7, incluindo a tenda superior em y136, com o mesmo mapa, paleta, geometria, câmera e banco compartilhados. Mundo768×544px; campo304px. Três emissores nas posições[[232, 216], [440, 432], [664, 280]]; objetivo e cadência de reforços preservados.

Cache560 + emissores76 = **636/640tiles**. Os seis quadros dos emissores são divididos em faixas8×16 com deduplicação exata; nenhuma troca de tiles durante a animação. A montagem dos sprites é conferida na SAT do emulador, além do banco completo. Nenhuma imagem foi repintada.

`export.py` gera o include compartilhado, as âncoras e o banco de faixas. `game/tools/build_campaign_resistance.py` inclui a fase8 após a fase7. `game/tools/review_campaign_resistance_launch_v2.py` mantém também a composição histórica de acesso rápido atualizada.

Reprodução:

```sh
python3 game/art/phase08-urban-v1/export.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase08_urban_emulator.py --output /private/tmp/phase08-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase08_urban_emulator.py --pal --output /private/tmp/phase08-pal
```

Todos os testes funcionais passaram; carga máxima:46,4–60FPS NTSC,50FPS PAL. Há quedas em NTSC. Combate natural e limites em [delivery.json](delivery.json); dificuldade humana e hardware físico não certificados.

ROM:5f443b87a621026298538b705b59051d6cfce2bc71c9904db61c5ac45b5280be.
