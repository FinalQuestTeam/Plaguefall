# Rádio e entrada em combate — integração

**Atualização de 22/10/2026:** o rádio com fundo de fase descrito abaixo foi substituído pelo [console de holodeck aprovado](../dialogue-holodeck-v1/README.md). As capturas deste pacote preservam o desenho anterior. `exportar.py` agora delega os recursos visuais do rádio ao novo pacote e continua exportando a contagem existente.

`revisao.html` compara a proposta aprovada com capturas de uma cópia fixa da ROM de entrega em NTSC/PAL. `proposta-aprovada.html` e `conteudo-aprovado.json` preservam a aprovação. Os relatórios e a ROM são identificados pelo mesmo SHA-256 no relatório consolidado. A cópia em `integracao/rom/Plaguefall.bin` evita que compilações paralelas do workspace alterem o arquivo validado; sua ELF e definições de tiles ficam ao lado para repetir a verificação. A implementação está nos fontes normais do jogo.

## Diálogos

`StoryLine.side` volta a determinar a janela ativa. Damião fica em 16,40 e o interlocutor em 248,144, com retratos de 48×48, paletas originais e sem espelhamento. A janela acompanha quem fala; os retratos não mudam de posição. A completa a fala e uma nova pressão avança; START pula. O roteiro permanece idêntico, com 51 falas verificadas em até quatro linhas de 26 caracteres, fonte 8×8 e entrelinha de 16 px. O clique de rádio é curto e espaçado, independente do som de coleta.

O compositor `screens/radio.c` usa 97 tiles de geometria, 72 de retratos e até 400 tiles dinâmicos, abaixo do início do cenário no tile 785. O cache de pixels ocupa 12.800 bytes e o mapa 2.240 bytes. As quatro paletas são UI, Damião, interlocutor e cenário. Na arena clássica, as cores opacas de parede/lava/lama são adaptadas à paleta da moldura; o piso mantém a paleta original. Ao sair, os gráficos de objetos/piso e o cache de atores são reconstruídos.

`LEVEL_preview` desenha a vista nativa sem iniciar fase, spawnar inimigos, marcar visita ou zerar estatísticas. Posição e estado de dano do cenário são preservados; o desenho usa uma vista íntegra. Menus/missões/guia/resultados continuam com seus compositores anteriores.

## Contagem

3/2/1 dura um segundo por algarismo. Quinze sprites formam o instrumento 144×80; VAI! usa três sprites e 96×32. São emprestados 180 tiles da reserva de ícones, com snapshot de 5.760 bytes. A paleta dos objetos é reutilizada sem alteração, preservando HUD, cenário e personagens. Ao terminar ou abrir a pausa, os tiles são restaurados exatamente. A geometria segue a proposta; as cores usam os tons disponíveis nessa paleta.

No zero, movimento e tiro ficam ativos no mesmo quadro. VAI! dura 21 quadros em NTSC ou 18 em PAL (~350 ms) sem bloquear o combate. A contagem observa quando A é solto para armar o próximo disparo; A mantido desde a confirmação não dispara acidentalmente. Há um pulso curto por número e um sinal de liberação distinto, sem reiniciar a música.

## Validação

Os testes usam Genesis Plus GX. RAM prepara fases e antecipa morte/meta/chefe apenas para acessar as cenas. Navegação, texto e contagens executam o código normal. Não são batalhas naturalmente vencidas nem ensaio físico/CRT.

- 51 falas por sistema: quebra de linhas, pixels de cada glifo, quatro retratos originais, paletas, âncoras, ausência de espelhamento e simulação congelada.
- 20 contagens por sistema: intervalos exatos de 60/50 quadros, movimento e disparo no zero, restauração dos ícones e pausa após VAI!. Verificação separada de A mantido desde a confirmação.
- Regressões NTSC/PAL: menus/guia/pausa e resultados nas 20 localidades, VRAM restaurada, 23 ligações e duas campanhas completas, fase 5 com contatos reais, objetivo, três tentativas e ensaios de carga.
- Recursos, partituras, testes nativos de jogador/áudio/contato, exportação de cenários e pacote da ROM conferidos.

```sh
python3 game/art/radio-dialogos-ux-v1/exportar.py --check
python3 game/art/radio-dialogos-ux-v1/validar_revisao.py
```

`capturar.py` e `atuais/` registram a interface anterior. `propor.py` recompõe os desenhos sem exportar recursos. `exportar.py` lê apenas a composição geométrica aprovada; não depende das capturas de cenário para produzir os recursos da ROM.
