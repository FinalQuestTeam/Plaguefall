# Representação visual da fase 6

Proposta de composição para os esgotos de 6A e 6B: três bases de 512×320 px, montadas como A+B+B+B+B+C em 3072×320 px. A representação inclui os objetos, os dois conjuntos de pressão de 6B, vistas de câmera e comparação com a paleta dos esgotos existentes.

Abra [a revisão interativa](review.html) ou [a prancha de conjunto](representacao-visual.png). O [guia de produção](../../doc/historia/guia-imagens-fase06.md) define a história, os encaixes e a circulação.

## Arquivos

- `segments/`: entrada, galeria repetível e acesso ao abrigo, completos.
- `panorama-6A.png`, `panorama-6B.png` e `panorama-6B-aberta.png`: montagem com objetos e estados dos portões.
- `panorama-sem-objetos.png`: arquitetura compartilhada, sem os obstáculos independentes.
- `objects/`: silhuetas dos módulos e objetos, com transparência onde aplicável.
- `palette-preview/`: mesmas montagens convertidas para as 16 cores existentes, com reconstrução visual independente de um exportador de ROM.
- `seams/`: as cinco junções sem os objetos de campo.
- `cameras/`: recortes de 320×224, com HUD ilustrativo e extremos verticais. A página acrescenta os sprites de referência de Damião e Dinorah.
- `source/` e `prompts/`: imagens e instruções do imagegen. A primeira escada tem projeção diagonal e foi descartada; a montagem usa a versão frontal.
- `manifest.json`: posições, colisões propostas, rotas conectadas, paleta, contagens e hash da ROM preservada.

## Produção e revisão

As imagens novas foram criadas com o `image_gen.imagegen` integrado. O cenário é montado por `assemble.cjs`, com escala por vizinho mais próximo, recorte técnico de transparência e faixas de materiais compartilhadas. A parede usa um painel inteiro de dois arcos, mantendo sua escala proporcional; o piso reutiliza uma amostra nativa existente. Os objetos comuns variam de posição nas quatro instâncias idênticas de B.

O montador recupera o portão vertical por meio de `export-existing-gate.py`, usando a fonte e as âncoras originais de `visual-composition-fixes-v1/objectives/cycle-0`. O exportado compartilhado aponta para a revisão diagonal de `routes/cycle-2`. Consulte [a investigação](gate-investigation.json) e [a comparação visual](gate-orientation-before-after.png). A correção é isolada na proposta, sem editar os mecanismos compartilhados.

Reproduzir com `node game/art/phase06-three-segments-v1/assemble.cjs`. O gerador escreve apenas nesta pasta. A primeira escada diagonal foi substituída antes da composição; o primeiro piso gerado foi substituído por concreto nativo mais discreto, e a região escura atrás da parede foi uniformizada.

As cinco emendas A/B, B/B e B/C reproduzem o mesmo encaixe de 256×320 px. As rotas propostas têm base de 16×16 e margem adicional de 8 px; a região caminhável aberta é conectada nas duas variantes. Isso valida a geometria da proposta, não a IA, o vapor, a câmera ou as colisões da ROM.

## Memória e integração

A versão de 16 cores ainda não cabe inteira na reserva residente: 1093 padrões distintos em 6A e 1123 na imagem fechada de 6B, considerando inversões H/V. A imagem de 6B inclui uma pose estática dos mecanismos e não modela sua alocação animada. No jogo, eles reservam 256 tiles, deixando 384 para cenário. Esses números exigem otimização ou carregamento por trecho antes de integrar; não há promessa de desempenho baseada no panorama.

A ROM de produção permanece com SHA256 `c12217f9f5e8611c625e0a45d7356470f35a936111415ac5a6ce70d1d903f8cf`. Nenhuma fase ativa, rota de produção, recurso nativo ou lógica de jogo foi alterada por esta proposta.
