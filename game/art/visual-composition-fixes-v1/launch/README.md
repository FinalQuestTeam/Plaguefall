Candidato visual launch: revisão manual e testes

ROM isolada `4b6ddf2fb375b22fd3c9ab8ccd35917317268421e2705f501430718df9ebecd6` (2365956 bytes). A ROM central ainda tem build e testes próprios. Todos os processos NTSC/PAL deste grupo terminaram com exit0.

A imagem completa foi gerada antes da quantização/cortes. Os tiles são reconstruídos pixel a pixel, com deduplicação H/V exata; não houve substituição aproximada de tiles. Paleta0 preta, coresRGB333, grade de colisão8px e teto640tiles incluindo objetivos.

- Fase14: 60.0FPS sob carga, 4 inimigos e pools completos de tiros (NTSC).
- Fase15: 59.0FPS sob carga, 3 inimigos e pools completos de tiros (NTSC).
- Fase16: 60.0FPS sob carga, 4 inimigos e pools completos de tiros (NTSC).
- Fase14: 50.0FPS sob carga, 4 inimigos e pools completos de tiros (PAL).
- Fase15: 50.0FPS sob carga, 3 inimigos e pools completos de tiros (PAL).
- Fase16: 50.0FPS sob carga, 4 inimigos e pools completos de tiros (PAL).

Capturas, vídeosMP4 e relatóriosJSON ficam em `cycle-2/ntsc` e `cycle-2/pal`. `phase-reviews.json` separa julgamento visual de verificações técnicas. `../resistance-launch-summary.json` reúne colisões, limites, FPS e amostras de dificuldade. As amostras automáticas de20–25s não equivalem à validação humana de dificuldade.

A apresentação da ignição acrescenta aproximadamente1s de tempo de parede aos120s ativos. O teste mantém1inimigo e2projéteis ativos; todos os estados de combate ficam estáveis. Só o cache visual `FShot.renderPose` pode ser preenchido pelo render. A coleta de pixels do rádio espera uma pose estável para respeitar a filaDMA do VBlank, mantendo comparação exata dos pixels. A fase16 conserva o hashRGB original.
