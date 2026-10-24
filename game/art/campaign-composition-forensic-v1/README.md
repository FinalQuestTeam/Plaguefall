# Reavaliação integral de composição visual

Este parecer substitui as aprovações visuais anteriores. Foram produzidos os 19 cenários completos antes da avaliação: 3 aceitáveis nesta revisão, 6 precisam de ajustes e 10 reprovados. Não houve alteração de arte, C, recursos binários ou ROM.

[Revisão visual por fase](review.html) ·[Todas as imagens completas](overview.png) ·[Relatório integral](report.json) ·[Manifesto de origem e geometria](manifest.json).

Os panoramas são reconstruções do mapa nativo e objetivos nas coordenadas do runtime. Há255 novas amostras NTSC de câmera nas faixas superior, central e inferior, mais38 entradas NTSC/PAL da mesma ROM. A varredura prepara nós, suspende combate/progresso e posiciona o personagem via RAM; não é um playthrough nem calibração de dificuldade. Os10 ninhos são mostrados juntos no panorama; no jogo existem7 slots simultâneos. O boss no panorama é uma pose representativa no spawn; atores móveis são avaliados nas capturas reais.

`prepare.py` congela mapas e estados; `capture.py --build-dir game/out/release` captura a câmera real com o núcleo libretro, via Python Intel; `build_review.py` publica pareceres previamente inspecionados e pranchas. Nenhum deles compila ou modifica o jogo. As decisões são humanas/visuais; o script não concede aprovação por testes verdes.

Os relatórios independentes estão em `reviews/`. As suspeitas permanecem separadas dos defeitos comprovados. Capturas e mapas sem marcações são preservados ao lado das cópias anotadas. Pranchas completas e pranchas de câmera estão em `boards/`.

ROM de produção SHA256: `ea9caca81c9baa64cd07d011f7b8ae234cb883b50a81c791fdcea179f23a558f`.
