# Fase 12 — Três blocos até o sindicato STE

[Revisão, cenário completo, percurso, vídeo e capturas atuais](review.html#union).

Corredor de 3.072×320 px, formado por A+B+B+B+B+C. As três bases têm 512×320 px: saída da fábrica, corredor industrial repetível e chegada ao sindicato. As quatro cópias de B são idênticas; 11 props independentes variam os desvios. A escolta de Dinorah e seus desfechos 13A/13B permanecem iguais.

## Prédio STE integrado

A [referência aprovada](source/union-ste-building-v4.png), criada com ImageGen integrado ([prompt](prompts/union-ste-building-v4.txt)), substitui a composição anterior de telhado e parede. O [asset nativo completo](modules/union-ste-building.png) mede 304×176 px e ocupa a mesma posição e colisão no fim do corredor. A cobertura usa os materiais metálicos compartilhados com a oficina e os anexos. Os dois vãos completos de janela são simétricos e compartilham padrões espelhados; a entrada central permanece inteira. O [emblema original STE](../space-workers-union-logo-v1/logo-ste.png) foi aplicado acima da porta em 56×56 px.

O exportador reduz a fonte proporcionalmente para 304 px antes de extrair a fachada de 48 px, mantém transparência binária com limiar 184 e usa a paleta nativa de 16 cores. A altura da cobertura é composta por materiais repetíveis, sem deformar o prédio inteiro. Deduplicação exata H/V; reconstrução do mapa pixel a pixel; nenhuma substituição aproximada de tiles.

## Memória e validação

618/640 tiles estáticos: 19.776 bytes de gráficos residentes e 22 tiles livres. Mapa de 30.720 bytes e paleta de 32 bytes na ROM. Reserva de VRAM mantida, sem heap/cache dinâmico do cenário. ROM alinhada de 2.752.512 bytes; RAM estática do build atual de 20.052 bytes.

Geometria preservada: 6.109 posições livres conectadas, rota de 2.984 px e 2.997 amostras com margem extra de 8 px. Colisões, limites, cinco emendas, pausa e 36 enquadramentos passaram em NTSC/PAL. A câmera atual acompanha o corpo do jogador; telhados podem sair parcialmente do enquadramento. O teste de composição verifica fachadas completas, emblema STE inteiro e corpo do jogador protegido abaixo do HUD nas aproximações. A antiga exigência de seis telhados inteiros dependia da câmera anterior e foi substituída explicitamente, sem mudar o código de câmera nesta integração.

Travessia por controle: 82,87 s NTSC / 81,34 s PAL, Dinorah com 100 HP, combate isolado antes de começar e sem escrita de posição/progresso durante o percurso. Morte da escolta e prioridade da derrota de Damião passaram. Carga configurada de 3 inimigos e 4+4 tiros, IA ativa e patrulha do jogador: 59,85–59,90 FPS NTSC / 50 FPS PAL por 20 s em quatro setores, com vida protegida e Dinorah pausada. Sem garantia de 60 FPS fixos. Defesa estacionária com vida normal não conclui a escolta; dificuldade humana e hardware físico não certificados.

Relatórios atuais: `validation/ste-building-v4/{ntsc,pal,composition-ntsc,composition-pal}/report.json`. [Entrega consolidada](delivery.json). Relatórios `house-v2` e `union-v3` são históricos.

## Fluxo reproduzível

```sh
python3 game/art/phase12-three-segments-v1/export.py
python3 game/tools/build_campaign_routes.py
make -C game -j4 OUT_DIR_LIB="$PWD/SGDK/out/release"
python3 game/art/phase12-three-segments-v1/export.py --check
python3 game/tools/build_campaign_routes.py --check
python3 game/tools/verify_campaign_route_scenes.py
python3 game/tools/check.py
CAMPAIGN_TEST_ESCORT_KEYS=12 arch -x86_64 /usr/bin/python3 game/tools/test_campaign_escorts_emulator.py --output /private/tmp/phase12-ntsc --movie
CAMPAIGN_TEST_ESCORT_KEYS=12 arch -x86_64 /usr/bin/python3 game/tools/test_campaign_escorts_emulator.py --pal --output /private/tmp/phase12-pal --movie
arch -x86_64 /usr/bin/python3 game/tools/test_phase12_composition_emulator.py --output /private/tmp/phase12-composition-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase12_composition_emulator.py --pal --output /private/tmp/phase12-composition-pal
```

ROM local: `42c959eed7284b967c03ba14f4c7e8c96da4a4e516b4868ba9e4bbb58690ccd8`.
Acesso: **FASE TESTE → Campanha → 12**. Sem nova publicação no GitHub.

## Conferência dos objetivos

Sete verificações adicionais por região passaram em NTSC/PAL na mesma ROM: Damião chegando sozinho; Dinorah na saída com Damião afastado; ambos fora da área; interrupção e reinício da permanência de chegada; conclusão viva até a rota 13A; morte por contato real até a rota 13B com estado persistente; prioridade de derrota de Damião. A chegada exige Dinorah na área diante do sindicato, distância aproximada de até 64 px entre os dois e permanência de 24/20 quadros de jogo em NTSC/PAL. Abates não concluem a escolta. As etapas seguintes exigem 30/45 insetos conforme a rota. Relatórios em `validation/ste-building-v4/objectives-{ntsc,pal}/report.json`; repetir com `game/tools/test_phase12_objectives_emulator.py`, usando `--pal` para PAL. Sem alteração de lógica ou ROM nesta conferência.
