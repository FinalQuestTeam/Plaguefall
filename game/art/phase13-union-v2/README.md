# Interior do sindicato STE — fases 13A/13B

[Revisão visual](review.html) · [Entrega e testes](delivery.json) · [ROM validada](../../out/phase13-north-fit/Plaguefall.bin).

O piso quadriculado agora chega até a base dos armários e do balcão. As faixas cinzas, marcas e sombras do material antigo foram removidas por uma máscara que acompanha a silhueta dos móveis, em vez de trocar apenas a cor lisa. A origem dos ladrilhos continua em (16,128), mantendo as juntas alinhadas com o restante da sala. As sombras novas escurecem o piso existente em um nível de cinza, com contato de um pixel na base.

A [prévia superior](north-floor-fit-preview.png) mostra a nova composição. Armários, balcão, paredes, personagens, bancos e suas sombras mantêm os pixels anteriores. Paleta, geometria, colisões, câmera e metas 30/45 continuam iguais nas duas variantes.

A [auditoria de pixels](validation/north-floor-fit/pixel-audit.json) confirma que as alterações se limitam à faixa superior (16,112)–(496,156) e que os móveis foram preservados. Os testes completos de [NTSC](validation/north-floor-fit/ntsc/report.json) e [PAL](validation/north-floor-fit/pal/report.json) passaram: 24 enquadramentos por variante/região, gráficos exatos na VRAM, navegação, colisões, pausa, personagens, combate, vitória/derrota e avanço para 14. `game/tools/check.py` passou.

Fonte: 1253 tiles; cache de 640 tiles/20480 bytes de VRAM, sem reserva adicional. Máximo conservador: 549 padrões, 91 livres. Módulo de piso de 64×64px, com ladrilhos de 32×32px.

Carga controlada de 20s com cinco inimigos e 6+6 tiros, IA e câmera em movimento:

- NTSC: 13A 58.7 FPS, 13B 58.8 FPS.
- PAL: 13A 49.7 FPS, 13B 49.7 FPS.

Vida protegida e reposição de slots inativos de tiros; hardware físico e dificuldade humana não certificados.

```sh
python3 game/tools/build_phase13_union.py --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4 OUT_DIR=out/phase13-north-fit
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --build-dir game/out/phase13-north-fit --output game/art/phase13-union-v2/validation/north-floor-fit/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --build-dir game/out/phase13-north-fit --pal --output game/art/phase13-union-v2/validation/north-floor-fit/pal
```

ROM validada: 2752512 bytes; SHA256 `186425287d9f924fdbfeb09797b7e3b8b5f211e4a6e6ae04d5c367a593794ab2`. Acesso: **FASE TESTE → Campanha → 13A/13B**.

[Relatório da revisão anterior](history/before-north-floor-fit/delivery.json).
