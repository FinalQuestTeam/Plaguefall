# Fase5 — Plataforma do sinalizador

## Estado atual — campanha integrada

Pacote aprovado explicitamente e aplicado à fase 05. A campanha carrega o mapa próprio, os limites, a câmera, os obstáculos e os perigos desta planta; a música existente permanece **Ladainha de Ferro**.

A validação integrada foi concluída em NTSC e PAL. A bateria dos sete mapas reuniu 42 partidas novas e 12 partidas de regressão da fase 1; os 28 ensaios de carga mantiveram 60 FPS NTSC e 50 FPS PAL. Os resultados da campanha estão em [NTSC](../phases02-06-v1/validation/ntsc/report.json) e [PAL](../phases02-06-v1/validation/pal/report.json). Os ensaios isolados abaixo são registros anteriores e não substituem esses resultados.


Cenário aprovado explicitamente e integrado à campanha.

A Santa ocupa o centro de uma plataforma reaproveitada, com pedestal técnico, cabo de sinal e marcas de pouso. Bagagens e cobertores sob a lona mostram a expectativa dos refugiados. A câmera elevada de60° e a escala seguem a primeira fase aprovada.

Mapa quadrado384×384, área caminhável352×272, sem lama ou calor; circulação ampla ao redor do objetivo. O objetivo existente é proteger por30 segundos. Sucesso leva à6A; falha leva à6B. Música: Ladainha de Ferro. A Santa permanece desenhada no cenário e a entidade lógica protegida usa uma área de contato de 40×40 em (176,200), centrada em (196,220). O sprite legado de 24×24 não é desenhado por cima; um indicador de sinal de 8×8 pisca em (192,200).

Fonte raster gerada com image_gen.imagegen integrado em source/layout.png; prompt e proveniência em source/prompts.json. design.json declara os módulos, planta e narrativa. A exportação organiza os módulos da fonte em tiles8×8 sem substituição aproximada; os arquivos hardware/ são a origem dos recursos ativos desta fase.

O pedestal tem uma base física explícita de 40×16 em (176,208), declarada na planta. Essa base bloqueia os pés e deixa passar os tiros. A área lógica de contato se estende acima e abaixo da pedra, e o encosto exato nas bordas laterais também causa dano; inimigos não precisam entrar na pedra para atingir a Santa. Cabos de chão e marcas de pouso são decoração sem colisão. A entrada e a saída têm passagem conectada ao redor dessa base. O conjunto usa551 tiles/17.632 bytes de padrões.

A Santa integrada recebe 12 pontos de dano por contato e tem 2,5 segundos de invulnerabilidade após cada acerto, com recuo dos inimigos e onda de choque preservados. Assim a defesa de 30 segundos admite sucesso ou falha. A piscada de dano oculta apenas o indicador, mantendo a Santa no cenário e a vida no HUD; o flash continua sinalizando o impacto. NPCs dos cenários legados conservam sprite 24×24 e invulnerabilidade de 5 segundos.

## Ensaio de carga isolado — histórico anterior à integração

[NTSC](validation/emulator-ntsc.json) · [PAL](validation/emulator-pal.json). Os testes reais no Genesis Plus GX mantiveram60/50 quadros por segundo nos três casos medidos por região: repouso, rolagem horizontal e rolagem vertical. A carga de movimento usa4 inimigos e6 tiros por grupo. O atlas exportado foi comparado à VRAM real; os limites da câmera foram percorridos.

Estes relatórios anteriores usaram ROMs temporárias da renderização existente, com o cenário substituído para medição. Estes ensaios não simulam os objetivos/perigos das novas fases nem representam partidas completas. Naquele ensaio, a ROM, as fontes e os recursos de produção foram preservados por hash; isso descreve a revisão isolada anterior à integração atual.
