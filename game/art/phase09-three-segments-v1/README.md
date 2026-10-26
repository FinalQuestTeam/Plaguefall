# Fase 9 — Rua industrial em três trechos

[Composição completa, caminho do jogador, câmera, capturas e ROM](review.html).

Fundo A → B → B → B → C, com módulos512×320 e mundo2560×320. A marca a chegada à zona de oficinas; B repete três vezes os materiais do perímetro industrial e da rua; C recebe a porta original da fábrica. Oficinas, galpões largos e três caminhões preservam suas silhuetas e variam de posição sobre essas bases. Só as extremidades absolutas têm limitadores laterais.

A rota alterna por cima da oficina sul, por baixo do galpão norte e por cima do armazém sul. Remove as divisórias verticais artificiais. Passagens principais64px; pés16×16 mais8px de margem. As5.611 posições livres estão conectadas e não há uma linha horizontal livre de ponta a ponta. [Rota marcada](pathing.png). A sequência autoral tem2.576px.

827 padrões exatos /26.464bytes na ROM; mapa25.600bytes. Cache448tiles /14.336bytes, contra630tiles /20.160bytes anteriores. Janela conservadora máxima410; heap5.238bytes, liberado na pausa. Sem aproximação de tiles. O banco da rua é alinhado a32bytes e usa o mesmo cache das fases3/6. A porta mantém todos os RGB do recurso das salas10/11; os dados dessas salas não mudaram.

Base de perímetro criada com ImageGen integrado, usando as fases3 e9 como referências de estilo e de objetos existentes. [Imagem gerada](source/industrial-street-base.png), [prompt exato](prompts/industrial-street-base.txt) e [decisões da montagem](source/README.md). A textura de piso gerada foi rejeitada na revisão; o asfalto final reutiliza a fase7. `export.py` realiza apenas montagem, normalização da paleta e empacotamento nativo, preservando as silhuetas existentes.

Reprodução:

```sh
python3 game/art/phase09-three-segments-v1/export.py --check
python3 game/tools/build_campaign_factory.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase09_stream_emulator.py --output /private/tmp/phase09-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase09_stream_emulator.py --pal --output /private/tmp/phase09-pal
```

Testes funcionais NTSC/PAL passaram:109 câmeras por região, colisões, limites, pausa e travessia completa por controle após isolamento de combate. Carga de3inimigos e4+4tiros por20s em4trechos manteve60/50FPS. Combate natural é medido separadamente e não certifica dificuldade humana. [Relatório e limitações](delivery.json).

ROM verificada: `37bf6f1866028c5affc90b43f93ec09099cb76eb8cd20cd33b5c778b23b78635`.

O terceiro caminhão reutiliza o mesmo sprite em[2256,176],96×64px. A colisão é gerada pela mesma posição. A rota principal e a chegada continuam livres;827 padrões de origem e448tiles residentes permanecem iguais. A revisão corrente e os relatórios estão em `validation/final-truck-v2/`; evidências anteriores foram preservadas no histórico.
