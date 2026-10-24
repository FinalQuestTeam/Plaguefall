> Arte substituída pela revisão de imagens completas em `../campaign-whole-scenes-v1/factory/`. Os resultados abaixo documentam a versão anterior; a nova arte aguarda a build conjunta.

# Fábrica — fases 9, 10 e 11

Implementação nativa com mapas, colisões, objetivos e limites próprios.

| Fase | Objetivo | Mapa | Insetos | Tiros jogador/inimigo |
|---|---|---|---:|---:|
| 9 | Chegar à fábrica | 2560×320 | 3 | 4/4 |
| 10 | Destruir dez ninhos, três acertos por ninho | 768×384 | 4 | 6/6 |
| 11 | Liberar três válvulas; 1,5 s perto sem A | 768×384 | 3 | 6/6 |

A fase 10 guarda dez estados lógicos e apresenta até sete objetos de animação reutilizáveis conforme a câmera. Mudar a câmera ou pausar preserva ovos destruídos. Bomba destrói somente ovos dentro do enquadramento. Mortes comuns não contam. A fase 11 reaproveita a fábrica, sem recriar ovos.

## Arte e geometria

Kit industrial criado com ImageGen, salvo em `source/industrial-kit.png`; quatro silhuetas completas em `assets/`. O exportador apenas recorta o alpha, reduz por nearest-neighbor, converte a paleta e monta tiles. Piso de pedra existente com a conversão de contraste baixa usada na campanha. Atlas nativo: 121 tiles; com ninho de seis poses, 337; com válvula, 217. Reserva máxima: 640.

`geometry.json` registra o flood de pegada 16×16: 3.113 posições acessíveis na fábrica e 7.713 na rua. Todas as dez aproximações de ovos, três válvulas e saída da rua são acessíveis. Os sólidos têm sondas adicionais no emulador, com controle empurrando Damião contra cada borda.

## Testes realizados

Build isolada do checkout compartilhado, com hooks CF em uma cópia em `/private/tmp/campaign-factory-build`. Nenhum arquivo comum do checkout foi alterado pelo agente. A ROM precisa ser novamente validada após integração central.

ROM SHA-256: `b9e17f5df137e204162b283e9720ebea91b34a55ba3952f3716d3983d4c39474`.

| Fase | Carga máxima NTSC | CPU pico NTSC | Carga máxima PAL | CPU pico PAL | Vida bot NTSC/PAL |
|---|---:|---:|---:|---:|---:|
| 9 | 60.00 FPS | 64.21% | 50.00 FPS | 38.28% | 85/85 |
| 10 | 60.00 FPS | 85.60% | 50.00 FPS | 59.62% | 100/79 |
| 11 | 60.00 FPS | 73.14% | 50.00 FPS | 47.17% | 100/85 |

Todos os testes funcionais passaram nas duas regiões: corredor por controle, dez ninhos atingidos com A, contador comum ignorado, bomba restrita à câmera, três válvulas operadas sem disparo, disparo bloqueando a interação, pausa preservando o estado e colisões. A saturação por spawns reais chegou aos tetos previstos.

Carga máxima é uma formação preparada na RAM a cada frame, com todos os insetos visíveis e os dois pools de tiros preenchidos. FPS mede frames de simulação por VBlank emulado. Não representa medição em console físico. A amostra de dificuldade usa vinte segundos de movimento e disparo automáticos, sem alterações na RAM depois do início; não prova vitória em combate nem substitui avaliação humana. Os testes de objetivo isolam o combate com atraso de spawn e posicionam o personagem antes de cada tentativa; execução usa somente controle com bloqueio de escrita na RAM.

A entrada do harness espera o mapa real de 1→2A acabar antes de trocar `pendingLevel` na preparação. Alterar esse valor durante a montagem do mapa causava um vazamento artificial de 7.908 bytes e impedia a pausa; isso foi corrigido no harness, sem modificar o jogo.

## Reproduzir

```sh
python3 game/tools/build_campaign_factory.py
arch -x86_64 /usr/bin/python3 game/tools/test_campaign_factory_emulator.py --build-dir game/out/campaign-factory-v1 --movie
arch -x86_64 /usr/bin/python3 game/tools/test_campaign_factory_emulator.py --build-dir game/out/campaign-factory-v1 --pal --movie
```

Abrir `review.html` via servidor local. Há vídeos NTSC/PAL das três fases, screenshots dos objetivos e relatórios completos em `validation/`.

Hooks centrais necessários: `CF_start`, `CF_update`, `CF_draw`, `CF_drawHUD`, `CF_forceHUD`, `CF_prepText`, `CF_shotHit(sx+4,sy-VIDEO_HEIGHT_OFFSET+4)` antes de testar inimigos e `CF_bomb` após gastar uma carga. Os cabeçalhos documentam as assinaturas.
