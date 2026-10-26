# Fase 6 integrada

6A e 6B usam a montagem A+B+B+B+B+C, com 3.072×320 pixels. [Revisão visual e resultados](review.html).

- Cenário: 456 posições de cache; até 437 padrões visíveis, sem aproximação de pixels.
- 6B: 112 tiles de portão vertical + 65 de válvula; total de 637/640 tiles residentes, incluindo quatro da barra da válvula. A 6A usa 568/640 tiles e dois portões sem válvulas ou vapor.
- O portão usa as seis poses originais de `../references/gate-vertical-*.png`; as duas variantes usam o mesmo banco de portão vertical.
- `6A/native` e `6B/native` são as fontes exatas; o build copia esses dados para os recursos da ROM.
- O cenário estático da 6B contém os apoios de alvenaria, com válvulas e folhas de portão desenhadas dinamicamente pelo jogo.
- A geometria é alinhada à grade de 8 px; os pontos da escolta foram recalculados para bases de 16×16 com margem adicional.
- A barra da válvula usa os tiles 1421–1424; a vida da Dinorah mantém 1436–1439. A operação mostra ABRINDO no HUD, conserva o trabalho ao interromper e foi testada após pausa.
- O portão destrutível mostra A + mira e quatro marcas de acerto. Na 6B, a referência só aparece após a pressão ser liberada. O botão desaparece ao quarto impacto e as quatro marcas somem ao terminar a queda. São 45 tiles de marcadores (1.440 bytes) na reserva própria de 45 posições; 21 tiles/672 bytes a mais carregados que antes, sem ampliar a reserva do cenário.
- O HUD do mecanismo tem prioridade nas proximidades; a sinalização aponta o próximo conjunto de pressão.

`delivery.json` distingue aprovação funcional, memória e desempenho. A carga não mantém 60/50 FPS fixos em todos os trechos. A escolta completa foi percorrida com combate isolado; mecanismos e defesa natural foram ensaiados separadamente. `validation/gate-shoot-hint-v3/ntsc` e `validation/gate-shoot-hint-v3/pal` são os relatórios da ROM entregue. Outros relatórios são diagnósticos identificados pelo hash da ROM.

Reprodução, a partir da raiz do projeto:

```sh
python3 game/art/phase06-three-segments-v1/export-integration.py --check
python3 game/tools/build_campaign_routes.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase06_stream_emulator.py --output /private/tmp/phase06-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase06_stream_emulator.py --pal --output /private/tmp/phase06-pal
```
