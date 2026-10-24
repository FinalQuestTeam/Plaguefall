# Estaleiro: imagem completa antes dos tiles

Primeiro foram geradas duas imagens inteiras de 1448×1086 com ImageGen nativo: o estaleiro normal (fases 14 e 15) e a edição pareada em ignição (fase 16 e estado final da 15). As fontes estão em `source/`; nenhuma delas é uma folha de pequenos props.

A conversão reduz uniformemente para uma grade lógica de 256×192, usa uma única paleta de 16 cores reais do Mega Drive e só depois recorta módulos arquiteturais inteiros: baias dos motores 96×112, fachadas, paredes laterais, base inferior, a plataforma central, um piso de concreto e faixas contínuas. Os módulos compõem um lugar fechado, com construções em todo o perímetro. A repetição é explícita de arquitetura e pavimentação; não há substituição por tiles parecidos.

O atlas é deduplicado apenas quando os pixels são exatamente iguais, incluindo espelhamentos H/V. A reconstrução a partir do atlas e mapa é comparada pixel a pixel com a composição anterior ao corte.

- Estado normal: 552 tiles, mais 79 tiles dos geradores = 631/640.
- Estado em fogo: 560 tiles, mais 64 tiles do rádio = 624/640.
- Zero substituições aproximadas de tiles.
- As prévias `*-native-reconstructed.png` são a imagem exata representada pelos dados nativos.

Objetivos foram alinhados aos pads da imagem. Cinco máquinas: (139,145), (373,145), (424,196), (353,277), (159,277). Rádio: (256,187), contato em (244,171). Bounds impedem entrar nas construções do perímetro. A plataforma central (216,256,80,56) possui colisão de pés e tiros. As cinco frentes e o ponto de nascimento do chefe passam no flood 16×16.

Na ignição da fase 15, toda a cena é trocada atomicamente com o vídeo desabilitado, fila DMA esvaziada e o rádio recarregado na posição correta do novo atlas. Não se atualizam apenas duas pequenas áreas dos motores, nem se mostra um mapa antigo com tiles novos.

Reprodução: `python3 game/tools/build_campaign_launch.py` (Pillow). Os testes de emulador devem ser repetidos sobre o build conjunto; os resultados da revisão anterior não validam estes novos mapas.
