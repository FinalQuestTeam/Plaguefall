# Interior do sindicato STE — fases 13A/13B

[Revisão visual](review.html) · [Entrega e testes](delivery.json) · [ROM atual](../../out/release/Plaguefall.bin).

A limpeza dos bancos removeu os resíduos do piso original carregados pelos recortes. Os três móveis preservam seus pixels dentro da silhueta e usam uma sombra de contato uniforme; colisões e posições permanecem iguais. A ROM atual passou novamente pelo teste completo de13A/13B emNTSC/PAL e por `game/tools/check.py`. [Auditoria de pixels](validation/bench-cleanup/pixel-audit.json), [NTSC](validation/bench-cleanup/ntsc/report.json) e [PAL](validation/bench-cleanup/pal/report.json).

O salão passou de512×384 para512×576px. Os limites de combate agora são24/160–487/487:328px de altura, antes136px (+141,2%). Os três bancos foram redistribuídos, com suas colisões na base, e a parede sul/porta foram deslocadas192px. Armários, púlpito, emblema STE, pixels e paleta originais da Dinorah e do adereço da13B foram preservados.

A13A e a13B estavam fora da condição de câmera estável aplicada às fases1–12. Agora usam a mesma posição calculada a partir do corpo de Damião e dos limites do mapa. A câmera antiga tinha37px de desvio no nascimento; a nova tem zero desvio em movimento, entrada, parada e retorno da pausa. Os metadados antigos de enquadramento do salão foram removidos. Exportação de cenário, limites e colisões têm a mesma fonte em `tools/build_phase13_union.py`.

Validação da ampliação anterior emGenesis Plus GX,NTSC/PAL:52ensaios de movimento,12de estabilidade,48enquadramentos de cenário por região, travessia por controle,2154posições livres conectadas,12faces dos bancos e4bordas por variante/região, pausa, reinício pelo seletor, metas30/45, vitória/derrota e avanço para14. Zero cortes do personagem, desvio de câmera ou falhas de cache. `game/tools/check.py` passou.

Fonte1183tiles naROM; cache640tiles/20480bytes naVRAM. Máximo conservador543padrões simultâneos (97livres); mapas18432bytes, cache7486bytes deheap. A expansão reutiliza os mesmos gráficos, sem novos tiles nem VRAM adicional. Dinorah e adereço usam a reserva ePAL2 originais da escolta.

Carga controlada por20s,5inimigos e6+6tiros com IA e câmera em movimento:13A59,05FPS/13B58,80FPS emNTSC;49,70FPS nas duas emPAL. Vida protegida e slots de tiros inativos repostos. Hardware físico e dificuldade humana não certificados.

```sh
python3 game/tools/build_campaign_resistance.py
python3 game/tools/build_phase13_union.py --check
make -C game -j4 OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase13_union_emulator.py --output /private/tmp/phase13-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_camera_motion_emulator.py --nodes 15,16 --assert-framing --assert-centered --output /private/tmp/phase13-motion-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_camera_idle_emulator.py --nodes 15,16 --output /private/tmp/phase13-idle-ntsc
```

Repetir os testes de emulador com `--pal` e outra saída. Relatórios atuais: `validation/bench-cleanup/{ntsc,pal}`. A câmera foi validada na revisão anterior em `validation/spacious-*`; seu código permanece igual. Reprodução da falha anterior em `validation/spacious-before-ntsc/report.json`.

ROM2752512bytes; SHA256`cb7321abe8d139df3ba3a63d91139f812fdb398b96e61447b9b510881e43f7e1`. Acesso: **FASE TESTE → Campanha →13A/13B**.
