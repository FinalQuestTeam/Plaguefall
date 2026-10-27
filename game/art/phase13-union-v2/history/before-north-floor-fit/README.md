# Interior do sindicato STE — fases 13A/13B

[Revisão visual](review.html) · [Entrega e testes](delivery.json) · [ROM validada](../../out/phase13-bench-fit/Plaguefall.bin).

Os três bancos agora se assentam sobre o piso quadriculado contínuo. O recorte antigo carregava restos de piso e sombra, principalmente na lateral direita e sob o assento. A composição nova aplica primeiro o piso, depois a sombra projetada e a sombra de contato nos pés, e por último a silhueta limpa dos móveis. A sombra escurece os ladrilhos existentes em um nível de cinza, mantendo as juntas e o quadriculado.

Madeira e armação do assento preservam seus pixels. O suporte direito usa o suporte esquerdo espelhado para remover o material de fundo misturado ao recorte original. Posições, colisões, paleta, paredes, personagens, câmera e metas 30/45 permanecem iguais. As duas variantes compartilham o mesmo fundo.

A [auditoria de pixels](validation/bench-floor-fit/pixel-audit.json) confirma que as alterações se limitam aos três recortes de 128×48px. Os pixels fora das silhuetas correspondem exatamente ao piso contínuo e às novas máscaras de sombra. Os testes completos de [NTSC](validation/bench-floor-fit/ntsc/report.json) e [PAL](validation/bench-floor-fit/pal/report.json) passaram: 24 enquadramentos por variante/região, pixels exatos na VRAM, navegação, colisões, pausa, personagens, combate, vitória/derrota e avanço para 14.

Fonte: 1259 tiles; cache de 640 tiles/20480 bytes de VRAM. Máximo conservador: 553 padrões, 87 livres. Nenhuma reserva adicional de VRAM. O módulo de piso continua com 64×64px e ladrilhos de 32×32px.

Carga controlada de 20s com cinco inimigos e 6+6 tiros, IA e câmera em movimento:

- NTSC: 13A 58.7 FPS, 13B 58.8 FPS.
- PAL: 13A 49.7 FPS, 13B 49.7 FPS.

Vida protegida e reposição de slots inativos de tiros; hardware físico e dificuldade humana não certificados.

```sh
python3 game/tools/build_phase13_union.py --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game -j4 OUT_DIR=out/phase13-bench-fit
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --build-dir game/out/phase13-bench-fit --output game/art/phase13-union-v2/validation/bench-floor-fit/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --build-dir game/out/phase13-bench-fit --pal --output game/art/phase13-union-v2/validation/bench-floor-fit/pal
```

ROM validada: 2752512 bytes; SHA256 `33151bb0e25db3027f78473ef64ef5f22a36152d03a2864e95b93b6d190d2682`. Acesso: **FASE TESTE → Campanha → 13A/13B**.

[Relatório da revisão anterior](history/before-bench-floor-fit/delivery.json).
