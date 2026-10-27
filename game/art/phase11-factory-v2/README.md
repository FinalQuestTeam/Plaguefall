# Fase 11 — Reativar a fábrica

[Composição completa, percurso e playtest](review.html).

Usa a cena exata da fase10, compartilhando os tiles, mapa e `phase10Solids` na ROM. A `phase11Scene` tem apenas uma paleta própria de 32bytes, com os quatro tons quentes convertidos em azuis; a fase10 mantém a paleta original. Sala768×544,352px de campo vertical, seis grupos de props. Seis válvulas espalhadas e acessíveis; aproximações em `manifest.json`, âncoras geradas em `phase11_layout.h`. Sem ovos nesta etapa.

Inimigos simultâneos3→5, reforços3→2s, operação1,5→2,5s por válvula. Soltar A perto da válvula avança a barra; atirar interrompe. Recuo e pausa preservam o trabalho. HUD e preparação usam6válvulas.

Memória: cache320 + válvulas65 + barra4 =389tiles usados/640 (12.448bytes). O banco de quatro tiles da barra fica no final da reserva, separado dos gráficos de válvula. Heap4.854bytes; nenhum fundo duplicado e nenhum tile aproximado.

Testes NTSC/PAL: seis válvulas por controle, sexta primeiro, progresso/barra, interrupção por tiro, recuo/pausa,36câmeras com pixels exatos, colisões, limites e produção atingindo5inimigos. Regressões9/10 e `check.py` passaram. Carga5inimigos e6+6tiros:48,5–60FPS NTSC,49,85–50PAL; meta fixa não atingida no centro. Combate natural30s:59,267/50FPS. Não certifica dificuldade humana ou hardware físico.

```sh
python3 game/art/phase11-factory-v2/export.py --check
python3 game/tools/build_campaign_factory.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_campaign_factory_emulator.py --output /private/tmp/factory-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_campaign_factory_emulator.py --pal --output /private/tmp/factory-pal
```

ROM local: `f4f7b96e2b2e9c9445f6e01961a7ae053ed21c35f60fef41346bb4f0a7794b21`. GitHub permanece na publicação anterior5ad7f971.

Revisão de paleta: validação azul NTSC/PAL em `validation/blue-ntsc` e `validation/blue-pal`; índices dos pixels idênticos e paletas conferidas na ROM/CRAM. Uso de VRAM e resultados de carga idênticos aos anteriores.
