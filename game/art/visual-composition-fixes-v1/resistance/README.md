Candidato visual resistance: revisão manual e testes

ROM isolada `4b6ddf2fb375b22fd3c9ab8ccd35917317268421e2705f501430718df9ebecd6` (2365956 bytes). A ROM central ainda tem build e testes próprios. Todos os processos NTSC/PAL deste grupo terminaram com exit0.

A imagem completa foi gerada antes da quantização/cortes. Os tiles são reconstruídos pixel a pixel, com deduplicação H/V exata; não houve substituição aproximada de tiles. Paleta0 preta, coresRGB333, grade de colisão8px e teto640tiles incluindo objetivos.

- Fase7: 60.0FPS sob carga, None inimigos e pools completos de tiros (NTSC).
- Fase8: 60.0FPS sob carga, None inimigos e pools completos de tiros (NTSC).
- Fase13A: 60.0FPS sob carga, None inimigos e pools completos de tiros (NTSC).
- Fase13B: 60.0FPS sob carga, None inimigos e pools completos de tiros (NTSC).
- Fase7: 50.0FPS sob carga, None inimigos e pools completos de tiros (PAL).
- Fase8: 50.0FPS sob carga, None inimigos e pools completos de tiros (PAL).
- Fase13A: 50.0FPS sob carga, None inimigos e pools completos de tiros (PAL).
- Fase13B: 50.0FPS sob carga, None inimigos e pools completos de tiros (PAL).

Capturas, vídeosMP4 e relatóriosJSON ficam em `cycle-2/ntsc` e `cycle-2/pal`. `phase-reviews.json` separa julgamento visual de verificações técnicas. `../resistance-launch-summary.json` reúne colisões, limites, FPS e amostras de dificuldade. As amostras automáticas de20–25s não equivalem à validação humana de dificuldade.

13A conserva o hashRGB original.13B usa o mesmo guichê e colisões, com entrada280,176 para enquadrar o retrato. O sólido do depósito fica unido ao limite oeste; sua colisão foi testada pela frente sul, pois o lado oeste não é acessível.
