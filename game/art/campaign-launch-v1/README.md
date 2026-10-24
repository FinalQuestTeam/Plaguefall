> Revisão anterior: cenários e resultados abaixo foram substituídos pelo fluxo de imagens completas. Consulte [a revisão atual](../campaign-whole-scenes-v1/launch/README.md). Os relatórios antigos não validam os novos mapas.

# Estaleiro espacial — fases 14, 15 e 16

Implementação nativa Mega Drive. Todas as fases usam mapas 512×384, câmera, colisão 16×16 e atlas compartilhado de 250 tiles 4bpp. Cenários e máquinas foram extraídos deterministicamente da referência aprovada `../guia-assets-campanha-v1/imagens/04-fabrica-estaleiro.png`; piso reaproveitado de `FLOOR_STONE_ART`. Nenhuma imagem de referência é desenhada diretamente na ROM.

- 14: ligar cinco máquinas. Aproximar-se pela frente e soltar o botão de tiro durante 0,6 segundo. Progresso persiste ao recuar. Cada painel possui animação e estado ligado; o quinto conclui o objetivo.
- 15: proteger o rádio com 100 HP por 120 segundos. Contato inimigo causa dano real e recuo. Destruição reinicia a tentativa; morte do herói também. Aos 40 segundos os motores passam ao estado de fogo. As máquinas ocupam áreas sólidas; o rádio fica acessível pelo perímetro para interceptação.
- 16: Escorpião com 25 HP, com dash, disparos, blindagem e lacaios já existentes. Arena com motores em chamas. A vitória usa a morte real do chefe; não há instalação adicional de bombas.

Cap de inimigos: 4/3/4. Cap por pool de tiros: 4. O boss está incluído no cap, portanto no máximo 3 lacaios simultâneos. Objetos de missão não consomem slots de inimigo. Dinorah permanece no console protegido do sindicato e participa remotamente caso tenha sobrevivido; diálogos são integrados centralmente por `campaignFlags`.

## Reprodução

`python3 game/tools/build_campaign_launch.py` recompõe atlas/mapas e valida as cinco frentes de interação por flood de 1955 posições. Dependência: Pillow.

`arch -x86_64 /usr/bin/python3 game/tools/test_campaign_launch_emulator.py --build-dir game/out/release --movie` executa Genesis Plus GX libretro. Acrescentar `--pal` para 50 Hz.

Os relatórios distinguem setup de RAM, interação exclusivamente com controle, carga artificial e amostra limitada de dificuldade. FPS indica atualizações lógicas/VBlank, não velocidade do computador. Uma amostra automática não substitui playtest humano completo. A origem da ROM é identificada por SHA256 em cada relatório.

Saídas: `validation/ntsc/report.json`, `validation/pal/report.json`, capturas e vídeos. `review.html` reúne os resultados para revisão.
