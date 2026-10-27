# Fonte aprovada do núcleo do rádio

Criada inicialmente como arte isolada para revisão e depois aprovada pelo usuário para substituir o console central. A exportação ativa das fases 15/16 usa `radio-core-native-48x64.png` como fonte, com conversão para a PAL1 existente.

- `source/radio-core-master.png`: imagem original criada com a ferramenta integrada image_gen.
- `radio-core-native-48x64.png`: exportação de 48 × 64 pixels, 16 cores incluindo transparência, bordas sem suavização.
- `radio-core-preview-8x.png`: ampliação de 8 vezes por vizinho mais próximo, para avaliar os pixels.
- `prompt.txt`: prompt completo usado na geração; as referências foram o gerador nativo da sala 14 e a antena atual da sala 15.
- `export.cjs`: exportação determinística restrita a esta pasta.

O núcleo com visor é o único componente protegido. O mastro é apenas visual. A integração usa uma base sólida de 32 × 16 pixels; só ela recebe dano por contato. Barra de integridade e reação ao dano são elementos de gameplay e não estão gravados nesta imagem.

A conversão ativa, as conexões de energia, a profundidade e a colisão estão documentadas e validadas em `../phase15-shipyard-v2/`. Esta pasta conserva a fonte aprovada e sua ampliação para revisão.
