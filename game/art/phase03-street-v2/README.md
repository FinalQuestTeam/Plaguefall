# Fase 3 — rua até o galpão, revisão 2

A igreja usa os mesmos 288 tiles da fachada original da fase 1, sem redimensionar ou redesenhar. O estado preservado/destruído acompanha a decisão da primeira fase. A rua mantém 2560×320 pixels e o objetivo de chegar ao galpão.

## Cenário e transposição

- Calçadas contínuas, meio-fio, pavimentação escura, fachadas de casas e postes.
- Quinze veículos abandonados e cinco barricadas: 20 obstáculos com colisões reais. Os quatro engavetamentos principais alternam os lados da rua e exigem desvios. Há um carro já no primeiro enquadramento.
- Veículos bloqueiam o movimento e os disparos; barreiras baixas bloqueiam os pés. As aberturas continuam acessíveis ao corpo 16×16.
- 615/640 tiles, uma paleta compartilhada com a igreja e 5668 posições livres conectadas. Nenhum tile foi substituído por aproximação para caber na VRAM.

## Testes

ROM: `3ef99e13ae4af490144c91b00b415943433072ff2e8a7832f3bb9f019dd73390`.

| Região | Colisões por controle | Carga forçada | Partida por controle |
|---|---:|---:|---|
| NTSC | 58 sondas | 53.2 FPS | completed, 22.87 s lógicos, 100 HP |
| PAL | 58 sondas | 47.75 FPS | completed, 27.36 s lógicos, 100 HP |

Entrada, atlas/câmera, sólidos, travessia completa, tetos de carga e as duas igrejas passaram no Genesis Plus GX. A preparação de cada prova usa RAM e está identificada no JSON; as tentativas por controle não escrevem RAM enquanto jogam. Carga injeta quatro insetos e seis tiros por lado continuamente. A vitória automática não substitui avaliação humana de dificuldade.

## Fontes e reprodução

`source/street-kit.png` foi criado e ajustado pelo ImageGen para este projeto. A conversão faz recorte de alpha, redução por vizinho mais próximo e mapeamento à paleta original da igreja. O piso usa somente dois tons escuros dessa paleta para preservar a leitura dos personagens.

1. `python3 game/art/campaign-early-v1/build.py`
2. `python3 game/art/phase03-street-v2/validate.py`
3. `make -C game -j4`
4. `arch -x86_64 /usr/bin/python3 game/art/campaign-early-v1/test_emulator.py --build-dir game/out/release --nodes 4 --matches 1 --movie --output game/art/phase03-street-v2/validation/ntsc`
5. Repita com `--pal` e saída `validation/pal`; execute `python3 game/art/phase03-street-v2/build_review.py`.

[Revisão e vídeo](review.html) · [Dados de geometria](layout.json) · [Resumo dos ensaios](summary.json)
