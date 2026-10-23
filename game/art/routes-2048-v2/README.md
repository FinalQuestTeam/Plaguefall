# Percursos contínuos de 2048 pixels

Composição própria para a travessia da fase 4 e a escolta de Dinorah na 6B,
substituindo a repetição de salas de 512 pixels. As rotas, colisões dos buracos,
músicas e regras dos objetivos permanecem nos dados existentes. A distribuição
de lama da travessia foi ampliada depois desta entrega: veja a
[revisão de lama](../reach-mud-v1/README.md), com três passagens de altura inteira.

- [Túneis de manutenção — 2048 × 288](mapa-04.png): entrada, casa de bombas,
  tubulação avariada e portão de serviço.
- [Retirada por terra — 2048 × 320](mapa-06b.png): posto de evacuação,
  transporte com bagagens, acampamento abandonado e saída terrestre.

A arquitetura usa uma parede contínua com equipamentos distribuídos em
posições próprias, sem repetir os pilares e as extremidades da sala original.
Os marcos novos foram criados com ImageGen integrado; fontes e recortes com
transparência ficam em `source/`, e os prompts estão em [prompts.json](prompts.json).
Cada recorte recebe uma única redução para um módulo nativo de até 80 × 64,
é convertido para a paleta existente de 16 cores e composto fora da área de
circulação. Outros quatro módulos de chão por fase, de até 64×32, mostram
grelhas niveladas, marcas de passagem, rastros de bagagem e tecido abandonado;
são detalhes planos e transitáveis que aparecem na janela real da câmera.
O piso recebe desgaste discreto; os buracos mantêm a faixa de
segurança e os perigos usam os mesmos módulos conectados do jogo.

O exportador remove padrões não referenciados e preserva exatamente os tiles
finais de 8 × 8. Não substitui tiles por aproximações para caber na VRAM.
O limite permanece em 640 tiles por cenário. [Dados e orçamento](export.json).

| Cenário | Tiles | Padrões na VRAM | Paleta |
|---|---:|---:|---:|
| Travessia — 4 | 448 / 640 | 14.336 bytes | 16 cores |
| Escolta — 6B | 357 / 640 | 11.424 bytes | 16 cores |

A [correção de cortes e música](../route-presentation-fix-v1/README.md) removeu
os fragmentos retangulares incompletos da arena antiga e sincronizou rolagem/DMA.
Os mapas e orçamentos acima refletem essa revisão; as capturas e os relatórios
abaixo são registros da primeira integração.

[Capturas da ROM](revisao.png) · [Validação consolidada](validation.json) ·
[NTSC](validation/ntsc.json) · [PAL](validation/pal.json).
As duas regiões passaram pela travessia e escolta completas, pausa/retomada,
colisões, resultados, retry, câmera depois de 1536 pixels e comparação do
atlas e do mapa exportados com a VRAM real nos oito marcos/detalhes de cada fase.
Uma build de controle com o mesmo código e a arte anterior apresentou o mesmo
desempenho de simulação no ensaio de carga: 52,5 FPS NTSC e 44,67 FPS PAL.
Esses valores medem a simulação sob carga; não representam 60/50 FPS constantes.

Regenerar e conferir na raiz do repositório:

```sh
python3 game/tools/build_route_stages.py
python3 game/tools/build_route_stages.py --check
```

Os recursos ativos são `res/routes/04/`, `res/routes/06b/` e os cenários em
`src/levels/route_stages.c`. As prévias antigas em
`objetivos-travessia-escolta-v1/integracao-2048/` também são atualizadas pelo
mesmo exportador, para que a revisão existente mostre a composição corrente.
