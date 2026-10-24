# QA integrado — escoltas6A,6B e12

ROM: `bb9955bf90a25dab36aa280281909f5d08d98a0d9b313d8508849d68aa382a16`,2.359.296bytes. NTSC e PAL terminaram com exitcode0 e24checks aprovados por região. As capturas e os vídeos desta pasta pertencem a esse SHA.

Os três percursos completos passaram em controle real,com combate desativado para isolar circulação e chegada. A6B também teve as duas válvulas operadas e os portões abertos por tirosA reais. A pausa preservou seus estados. A morte de Dinorah reinicia6A/6B; na12 continua13B,com prioridade de derrota se Damião morrer.

O atlas e os mapas foram comparados comVRAM; as seis poses de portão e válvula foram comparadas pixel a pixel aos originais,independentemente da deduplicação. Em cada fase e região,2.432pixels efetivamente exibidos do piso seco apresentaram zero pretos inesperados. A inspeção visual confirmou a correção da paleta de índice0.

| Fase | Rota isolada NTSC/PAL(s) | Stress3insetos+4/4tiros NTSC/PAL(FPS) | Stress16insetos+6/6tiros NTSC/PAL(FPS) | Defesa parada NTSC/PAL(FPS) |
|---|---:|---:|---:|---:|
|06a|83.58/83.98|57.33/47.33|29.67/24.33|59.47/49.51|
|06b|86.2/86.92|55.67/47.33|23.0/24.67|59.38/49.6|
|12|86.27/85.12|57.33/47.33|29.33/24.33|55.52/46.43|

Os limites medidos daSAT foram até12sprites e208pixels por linha,abaixo do teto20/320. O teto de produção é3insetos e4tiros por grupo. Stress acima desse teto usa configuraçãoRAM explícita por quadro e não representa uma partida ordinária.

Persistem quedas de desempenho sob stress. A defesa parada não comprova vitória humana em combate:6A/6B permaneceram ativas por45s; na12 o ensaioNTSC terminou com a morte de Damião e oPAL com a perda de Dinorah. Não foi declarada conclusão completa das três escoltas sob combate.

[Contato visualNTSC](ntsc/review-contact.png) · [Contato visualPAL](pal/review-contact.png) · [RelatórioNTSC](ntsc/report.json) · [RelatórioPAL](pal/report.json)

VídeosNTSC640×448,H.264,sem áudio: `06a-traversal.mp4`,`06b-traversal.mp4`,`12-traversal.mp4` e os três `*-combat.mp4`,verificados comffprobe.

O diagnóstico do primeiroSHA,com a transparência incorreta,não faz parte desta galeria e foi preservado em `art/campaign-whole-scenes-v1/routes/diagnostic-before-palette-fix/`.
