# Capítulos 2 a 6 — aprovados e integrados

[Abrir revisão interativa](revisao.html). As sete telas dos cinco capítulos foram aprovadas em21/10/2026 e integradas à campanha principal, incluindo2A/2B e6A/6B. [ROM principal](../../out/release/Plaguefall.bin).

| Fase | Cenário | Mundo | Tiles | Música existente |
|---|---|---|---|---|
| 02A | Rua de serviço — igreja preservada | 512×320 | 443 / 640 | Ladainha de Ferro |
| 02B | Desvio — custo da explosão | 512×320 | 603 / 640 | Entardecer |
| 03 | Abrigo de manutenção | 384×384 | 538 / 640 | Entardecer |
| 04 | Túneis de manutenção | 512×288 | 537 / 640 | Breu |
| 05 | Plataforma do sinalizador | 384×384 | 551 / 640 | Ladainha de Ferro |
| 06A | Resgate confirmado | 512×320 | 508 / 640 | Entardecer |
| 06B | Retirada por terra | 512×320 | 500 / 640 | Breu |

A galeria inclui mapa nativo em 1×/2×, câmera ajustável de 320×224, área de movimento, perigos, objetivo, passagem e pistas ambientais numeradas. Os links de cada tela levam ao atlas, aos módulos, à fonte, ao projeto Tiled e aos binários. A câmera é uma ferramenta de revisão visual; não simula combate ou mede performance. [Validação consolidada](validation.json).

Os relatórios de exportação verificam640 tiles,16 cores, reconstrução exata e passagem seca para base16×16. A instalação reordena os tiles sem alterar a imagem e reserva padrões exclusivos à lava: um brilho lento atualiza até128 bytes por quadro, sem mudar paletas, paredes, HUD ou personagens.

[Partidas e ensaios NTSC](validation/ntsc/report.json) · [Partidas e ensaios PAL](validation/pal/report.json). As partidas não permitem alterações em RAM; os ensaios isolados preparam carga/posições para conferir colisões, dano e recuperação, câmera, pausa, VRAM e FPS. Na fase5, a Santa usa a arte do mapa e um alvo lógico40×40; os inimigos conseguem atacá-la pelos quatro lados. As duas rotas de saída foram verificadas.

Os relatórios `validation/emulator-*.json` dentro das pastas individuais e [a consolidação anterior](validation/isolated-before-integration.json) são históricos de builds isolados. Os relatórios acima usam a ROM principal.

## Regenerar

Execute, na raiz do repositório:

```sh
python3 game/tools/build_stage_review.py
```

O gerador relê `design.json`, `export.json` e os relatórios da campanha em `validation/ntsc` e `validation/pal`. Escreve apenas esta galeria, README e [manifest.json](manifest.json). A página lê dados JSON embutidos e imagens locais por `Image`, sem `fetch`, dependências externas ou servidor.
