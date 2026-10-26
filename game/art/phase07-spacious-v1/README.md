> Versão anterior do cenário. A [feira urbana da fase 7](../phase07-urban-v2/review.html) é a versão ativa no jogo; seus dados, testes e exportador ficam na pasta `phase07-urban-v2`.

# Fase 7 — O Último Chão

[Revisão completa e ROM](review.html). Somente a fase 7 recebeu cenário, geometria e âncoras novos. A fase 8 mantém seu mapa e alvos;13A/13B mantêm seus cenários.

O pátio cresceu de 768×384 para 768×544. A altura útil passou de 176 para 304 px (+72,7%). Cinco fontes e o depósito conservam as regras originais:0,5 s para abrir, uma carga por viagem e redução20% da velocidade durante o transporte.

A imagem-mestra foi gerada com a ferramenta integrada ImageGen, usando a igreja original como estilo e a favela anterior como referência de ambiente. [Prompt completo](prompts/whole-scene.txt), [imagem-mestra](source/07-favela-whole.png), [composição nativa completa](complete-with-objectives.png), [fundo sem objetivos](complete-background.png). O processo extrai peças inteiras e materiais repetíveis, preserva silhuetas e usa exatamente a paleta da primeira fase. A composição nativa é o material efetivamente exportado para o jogo; a imagem-mestra é referência.

A primeira conversão preservava todos os detalhes únicos da fileira de casas, mas exigia 788 padrões por janela e excedia a reserva. A composição final repete duas casas e um abrigo completos, além dos materiais. Usa1.048 padrões na ROM e no máximo 515 por janela conservadora; o cache reserva 560. Com74 tiles de cargas, são 634/640 posições (20.288 bytes), seis livres. O controle do cache usa6.576 bytes de heap e é liberado na pausa. O mapa ocupa13.056 bytes; os gráficos33.536 bytes.

Os limites e sólidos partem de [manifest.json](manifest.json). [export.py](export.py) gera o mapa, os bancos, o include de cenário e `phase07_layout.h`, compartilhando os mesmos pontos da arte com abertura, colisão, coleta, entrega e sinalização. O gerador antigo inclui a fase 7 nova e preserva os bancos de 8/13A/13B.

Validação: NTSC/PAL, pixels visíveis do cenário e das cargas, rolagem completa, pausa, limites, colisões e cinco entregas via controle com combate isolado. Carga de 20 s por trecho com quatro inimigos e 6+6 projéteis, IA e trajetórias mantidas. NTSC 57,75–59,9 FPS; PAL 50 FPS. O depósito tem quedas no NTSC. Combate natural automatizado e regressões compartilhadas estão separados em [delivery.json](delivery.json). Hardware físico e dificuldade humana não certificados.

ROM SHA256:`a3a5f6bf18b6fde500edaaca0a8632512c3c275b26d529a1f3a96c0a11e54234`.

```sh
python3 game/art/phase07-spacious-v1/export.py --check
python3 game/tools/check.py
arch -x86_64 /usr/bin/python3 game/tools/test_phase07_spacious_emulator.py --output /private/tmp/phase07-ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_phase07_spacious_emulator.py --pal --output /private/tmp/phase07-pal
```
