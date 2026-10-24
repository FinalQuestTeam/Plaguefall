> A arte e a geometria desta primeira revisão foram substituídas. Veja `../campaign-whole-scenes-v1/routes/README.md`. Os relatórios abaixo documentam apenas a ROM antiga.

# Escoltas da campanha — 6A,6B e12

As três rotas têm3072×320px,384colunas de mapa e saída em(2992,184,48,48).
A entrada usa Damião e Dinorah em(48,208); o objetivo exige chegada dos dois.
A câmera e o HUD seguem o motor de escolta existente.

| Fase | Montagem | Tiles cenário | Insetos simultâneos | Tiros por grupo | Intervalo |
|---|---|---:|---:|---:|---:|
|6A|túnel seco,cinco canais/recessos,duas pausas|380|3|4|3s|
|6B|ramal alternativo,duas válvulas,dois portões,bolsos seguros|105|3|4|3s|
|12|corredor de serviço,cinco recessos,três pausas|370|3|4|2s|

## Arte e rastreabilidade

- `tools/build_campaign_routes.py` monta módulos dos tiles nativos aprovados de `res/stages/04` e das rotas2048 existentes.
- Marcos completos reutilizam `art/routes-2048-v2/source/tunnel-cutouts.png` pelo compositor já aprovado; os pixels finais do tile atlas são exatos,sem aproximação entre padrões.
- Canais/recessos reutilizam por montagem9-slice a borda de segurança nativa e o interior dos poços da rota04. A colisão acompanha o retângulo interno; a faixa externa é somente pintura.
- Não há sprites de personagens novos nem raster gerado proceduralmente nesta entrega. Os PNGs são decodificações dos mapas4bpp enviados à ROM.
- `export.json` guarda geometria,pontos de rota,amostras de varredura16×16,orçamentos e hashes dos atlases.
- A6B reserva480tiles para as seis poses de portão+válvula. Somados ao cenário105,usa585dos640tiles disponíveis.

## Operação da6B

Cada composto tem uma válvula no lado oeste e uma folha de portão.
Damião opera a válvula pelo lado sul,parado por1,5s sem atirar(A).
O progresso fica preservado se recuar. Depois de aliviar a pressão,quatro tiros abrem a folha.
Antes disso,os tiros são absorvidos. Probes de visibilidade dos inimigos não danificam os portões.
Os batentes e as paredes continuam sólidos após a abertura.

O bocal junto ao portão avisa por1s antes da fase quente de2s. O bolso de trabalho fica fora do dano.
Dinorah espera pela cobertura e pela passagem livre; cada válvula/portão tem estado próprio.
O HUD local mostra válvula/portão na aproximação e volta à escolta ao sair.

## História e dificuldade

6A e6B reiniciam se Dinorah morrer. Na12,a morte dela com Damião vivo segue para13B;
se Damião morrer também,a derrota do jogador tem prioridade. Essa transição vive no fluxo central.
A12 aumenta pressão usando intervalo2s e inimigo roxo; o teto continua3.

O percurso sem combate levou aproximadamente84s(6A),90s(6B com portas abertas) e86s(12).
Isso valida a circulação,a espera e a chegada; não equivale a completar uma escolta em combate.
O ensaio de defesa parado mede dificuldade/carga e deliberadamente não demonstra uma vitória humana.

## Validação reproduzível

```sh
python3 tools/build_campaign_routes.py --check
python3 tools/test_campaign_route_ops.py
make OUT_DIR=out/campaign-escort-v1 -j4 release
arch -x86_64 /usr/bin/python3 tools/test_campaign_escorts_emulator.py --build-dir out/campaign-escort-v1
arch -x86_64 /usr/bin/python3 tools/test_campaign_escorts_emulator.py --build-dir out/campaign-escort-v1 --pal
```

Os relatórios `validation/ntsc/report.json` e `validation/pal/report.json` registram o hash da ROM usada,
os resultados funcionais,as capturas,os ensaios ordinários e o stress com3/4/8/16insetos.
Stress acima dos tetos de produção é configurado por RAM a cada quadro e deve ser lido separadamente.
FPS é calculado por quadros da simulação/VBlanks emulados; velocidade do computador não é usada.

O teto3insetos+4tiros por grupo reduz o custo,mas os primeiros ensaios NTSC ainda mediram cerca de57FPS
na6A e56FPS na6B sob stress; o motor requer otimização global para garantir60FPS nessa situação.
A falha de abertura da pausa6B detectada no primeiro ensaio foi corrigida no motor central: a máscara de
colisão passou a usar uma reserva plana com stride por mundo. As duas regiões agora abrem a pausa e
preservam as válvulas e os portões. A prioridade de derrota de Damião também foi reforçada no fluxo central.

## Resultado final desta integração

| Fase | Rota sem combate NTSC/PAL(s) | Stress3insetos+4/4tiros NTSC/PAL(FPS) | Defesa parada NTSC/PAL(FPS) |
|---|---:|---:|---:|
|06a|83.58/83.98|57.0/47.33|57.52/45.09|
|06b|89.85/90.4|55.33/47.33|51.7/44.2|
|12|86.27/85.12|57.0/47.33|52.21/45.23|

Ambos os relatórios finais têm `passed=true`. Os checks funcionais passaram; essa flag não promete
60/50FPS sob stress. As quedas de desempenho continuam explicitamente medidas na tabela.
