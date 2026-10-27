# Interior do sindicato STE — fases 13A/13B

[Revisão visual](review.html) · [Entrega e testes](delivery.json) · [ROM validada](../../out/phase13-checker/Plaguefall.bin).

O salão agora usa piso quadriculado cinza, com ladrilhos de 32×32px, juntas de um pixel e desgaste discreto. O módulo [64×64px](modules/floor-checker-64x64.png) repete sem emendas e usa apenas os cinzas originais da sala. A aplicação respeita o piso livre conectado: paredes, armários, púlpito, emblema STE, bancos e suas sombras conservam os pixels anteriores. A 13A e a 13B compartilham o mesmo fundo.

Geometria preservada: sala de 512×576px, limites de combate 24/160–487/487, três bancos, câmera estável e metas de 30/45 inimigos. Dinorah e seu adereço continuam usando os sprites e a PAL2 originais.

A [auditoria de pixels](validation/checker-floor/pixel-audit.json) confirmou que as alterações se limitam ao piso e que paleta, móveis, sombras e colisões permanecem iguais. Os testes completos em [NTSC](validation/checker-floor/ntsc/report.json) e [PAL](validation/checker-floor/pal/report.json) passaram: 24 enquadramentos por variante/região com gráficos exatos na VRAM, navegação por controle, colisões, pausa/restauração do cache, personagens, combate, metas, vitória/derrota e avanço para a fase 14. `game/tools/check.py` passou.

Fonte: 1231 tiles; cache de 640 tiles/20480 bytes de VRAM, sem reserva adicional. Máximo conservador: 553 padrões simultâneos (87 livres). Mapas: 18432 bytes; cache: 7582 bytes de heap. O piso acrescentou 48 padrões de origem e 1536 bytes de gráficos em relação ao piso liso.

Carga controlada de 20s com cinco inimigos e 6+6 tiros, IA e câmera em movimento:
- NTSC: 13A 58.3 FPS, 13B 58.6 FPS.
- PAL: 13A 49.7 FPS, 13B 49.7 FPS.

Vida protegida e slots de tiros inativos repostos. Hardware físico e dificuldade humana não certificados.

```sh
python3 game/tools/build_phase13_union.py --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --build-dir game/out/phase13-checker --output game/art/phase13-union-v2/validation/checker-floor/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --build-dir game/out/phase13-checker --pal --output game/art/phase13-union-v2/validation/checker-floor/pal
```

ROM validada: 2752512 bytes; SHA256 `1db99280f68527045781180de59e882638d7a24b5f1581e0d75260060e60aa85`. Acesso: **FASE TESTE → Campanha → 13A/13B**. A cópia em `out/phase13-checker` preserva a compilação validada enquanto outras tarefas atualizam `out/release`.

[Relatório da revisão anterior](history/before-checker-floor/delivery.json).
