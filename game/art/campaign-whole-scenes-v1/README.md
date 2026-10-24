# Cenários completos — revisão de arte e composição

A revisão cobre 3,4,6A,6B,7,8,9,10,11,12,13A,13B,14,15 e 16. As fases 1,2A/2B e 5 foram preservadas; hashes dos arquivos aprovados estão em `preserved.json`.

## Processo

1. ImageGen nativo criou imagens completas para cada ambiente: rua, galpão, esgotos, favela, fábrica, sindicato e estaleiro. Lugares reutilizados pela história compartilham a arquitetura, com estados próprios quando necessário.
2. As imagens completas foram inspecionadas antes dos recortes. Os diretórios `source` preservam as fontes; os prompts estão em `prompts-root.json`, `routes/prompts`, `launch/prompts.json` e nos registros da fábrica.
3. Módulos arquitetônicos inteiros foram recortados dessas imagens: fachadas, pórticos, paredes, caldeiras, esteiras, bancos e motores. Pisos foram simplificados como material para evitar ruído e emendas.
4. Cada composição inteira foi convertida para a paleta RGB333 e separada em tiles 8×8. Somente padrões idênticos, inclusive espelhados, compartilham espaço. Não há substituição de um tile por outro parecido.
5. A reconstrução dos binários é comparada pixel a pixel à composição nativa. Bounds, sólidos, posições de interação e rotas foram alinhados às construções. As capturas e vídeos do emulador são uma etapa separada da imagem de referência.

A igreja da fase 3 copia os 288 tiles originais da primeira fase, nas versões inteira e destruída. O galpão agora tem fachada interna contínua, prateleiras, janelas e portão; a entrada foi movida para que essa arquitetura apareça no enquadramento inicial. As ruas e escoltas têm construções ao longo do percurso e edifícios de chegada. O estaleiro tem versões pareadas normal/em chamas, com troca completa durante a ignição.

## Limite gráfico

O banco possui 640 tiles para cenário e objetivos. A compactação exata dos seis quadros dos mecanismos libera espaço para as construções: ninho 140, gerador 79, carga 76, válvula 61, portão 112 e rádio 64 tiles. As animações e os pixels originais foram preservados; objetivos móveis continuam no atlas contíguo.

As fontes completas têm mais detalhe que a versão do console. A imagem **nativa reconstruída** no painel é a referência do que entra na ROM. Os recortes arquitetônicos podem se repetir para caber na memória gráfica; não se promete reprodução integral da ilustração de origem.

## Revisão e testes

- [Painel da revisão](review.html): imagem inteira, cenário nativo, recortes e captura/playtest.
- [Dados por fase](review-data.json): cada teste informa se o hash corresponde à ROM atual.
- `python3 game/art/campaign-whole-scenes-v1/validate_early.py`: reconstrução, igreja, preservação e conectividade.
- `python3 game/tools/pack_campaign_ground_art.py --check`: reconstrução exata das seis poses.
- `python3 game/tools/check.py`: recursos e testes nativos.
- `python3 game/tools/test_campaign_emulator_suite.py --movie`: dez baterias NTSC/PAL, incluindo carga, limites, colisão e objetivos.

Os testes preparados em RAM isolam colisão, objetivos e saturação. Vídeos de combate são amostras automáticas; as escoltas completas usam combate isolado. Isso não substitui uma campanha humana completa para balancear dificuldade. Não houve teste em hardware físico.
