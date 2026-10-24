# Fases 9, 10 e 11 — composição atual

A origem atual é `source/street-cycle1-complete.png` para a fase9 e `source/factory-cycle1-complete.png` para as fases10/11. As duas imagens completas foram geradas antes da extração de fachadas, máquinas, tubulações e barreiras. As fontes `*-flat-complete.png` e os módulos em `previous-pre-audit/` documentam a versão anterior e não entram na ROM atual.

| Fase | Mapa | Tiles de cenário | Total com objetivo |
|---|---|---:|---:|
| 9 | 2560×320 | 627 | 627/640 |
| 10 | 768×384 | 476 | 476 + 150 = 626/640 |
| 11 | 768×384 | 476 | 476 + 65 = 541/640 |

`street-native.png` e `factory-native.png` são reconstruções exatas dos tiles da produção. Os recortes `*-2x.png` mostram câmeras de320×224. A composição usa resolução nativa, RGB333 com índice0 preto e seleção RGB exata. Apenas tiles idênticos e espelhos H/V exatos são reutilizados. Não há substituição de tiles por outros parecidos. O piso vem de material calmo da imagem integral; a arquitetura mantém contornos completos. O miolo repetitivo das esteiras foi estendido sem repetir suas molduras.

A rua progride por oficinas de tijolo, docas e tanques até o portão da fábrica. Quatro barreiras visíveis possuem bases sólidas80×32; todas interceptam a trajetória reta y192. O percurso por controle alterna desvios y216/y168. A fábrica mantém estruturas no perímetro inferior para que a câmera baixa continue parecendo um interior fabril. Três gabinetes se conectam às válvulas por tubulações contínuas. Ao liberar uma válvula, a roda muda de estado e o gabinete mostra energia. Dez ninhos conservam estados independentes; agora a silhueta tem três ovos claros.

Limites de caminhada: fábrica y112..319; rua y152..271. As esteiras têm bases160×24, e quatro pilares fecham a borda inferior. O flood com pegada16×16 alcança todos os ovos, válvulas e saída. `../../campaign-factory-v1/geometry.json` registra sólidos e pontos dos desvios.

A build isolada passou em NTSC/PAL com `passed:true` e `exitcode:0`, incluindo objetivos, bomba, pausa, quatro obstáculos reais, limites de caminhada e comparação exata entre ROM/VRAM (atlas e células H/V). Carga máxima configurada:60FPS NTSC /50FPS PAL. Pico CPU NTSC nas fases9/10/11:64,94% /86,23% /73,58%; PAL38,82% /60,21% /47,61%. Esses números pertencem à build isolada SHA5173cbbc5d29dae81f1aea1e240eb6aebe41310bc61cadd0ac154c710b3265d9; a release central será medida separadamente.

Amostras de dificuldade usam20s de patrulha e disparos automáticos. Vida final NTSC:100/64/44; PAL35/55/7. Elas medem pressão sobre esse bot, não uma vitória ou avaliação humana de equilíbrio. Os testes de objetivos isolam combate e preparam posição em RAM; as tentativas usam controle com bloqueio de escrita. A carga máxima repõe formações e pools por RAM a cada frame; FPS mede simulação por VBlank, não velocidade do computador.

[Revisão visual, crítica por ciclo e vídeos](../../visual-composition-fixes-v1/factory/review.html). Os relatórios NTSC/PAL ficam em `../../visual-composition-fixes-v1/factory/cycle-2/`.

```sh
python3 game/tools/build_campaign_factory.py
python3 game/tools/build_campaign_factory.py --check
arch -x86_64 /usr/bin/python3 game/tools/test_campaign_factory_emulator.py --movie --build-dir /private/tmp/campaign-factory-build/out/release --output game/art/visual-composition-fixes-v1/factory/cycle-2/ntsc
```

`export.json` registra os hashes das fontes, recortes e orçamento. O gerador e os recursos C foram congelados para integração central após o ciclo2.
