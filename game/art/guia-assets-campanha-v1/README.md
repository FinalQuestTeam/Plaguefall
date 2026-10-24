# Guia de assets das fases para aprovação

Pacote de pré-produção baseado no pátio da igreja, nas primeiras fases aprovadas e na história revisada da campanha. São 19 fichas de fase, cinco pranchas e 30 famílias de pequenos elementos de referência, com estados de objetivo e consequência narrativa.

- [PDF de revisão](../../../output/pdf/plaguefall-guia-producao-visual-fases-v1.pdf)
- [Guia completo por fase](../../doc/historia/guia-producao-visual-fases.md)
- [Dados das fases](fases.json), [catálogo dos kits](kits.json) e [inventário existente](inventario.json)
- [Prompts completos](prompts/) e [manifesto das fontes](manifest.json)
- [Script de composição](build_guide.py)

## Referências geradas

| Prancha | Elementos |
|---|---|
| [Kit 1](imagens/01-igreja-rua-galpao.png) | Parede da igreja, destroços, esquina, entrada de galpão, pilar e banco |
| [Kit 2](imagens/02-esgotos-favela.png) | Arco de esgoto, válvula, portão, vapor, casa e depósito |
| [Kit 3](imagens/03-objetivos.png) | Caixa, carga, transmissor, ovos, gerador e marcas de interação |
| [Kit 4](imagens/04-fabrica-estaleiro.png) | Tubulação, caldeira, console, distribuição elétrica, motor e piso de lançamento |
| [Kit 5](imagens/05-estados-narrativos.png) | Rádio, mastro, armário, memória de Dinorah, civis e ferrão do Escorpião |

Cada imagem tem seis células: A/B/C na linha superior e D/E/F na inferior. Pares ou trios de desenhos na mesma célula são estados da mesma família. Os códigos K1A a K5F ligam as peças às fichas de fase.

## Escopo da aprovação

As imagens foram geradas com **image_gen integrado**, usando mapas e sprites do projeto como referências. São estudos ampliados de forma, material e estados; ainda não são PNGs nativos indexados, folhas de animação finais ou mapas para integração. O fundo escuro é fundo de revisão, não canal alfa de um sprite final.

Recursos marcados como reutilizar mantêm a arte já aprovada. Uma referência ilustrada de válvula, rádio ou gerador não exige substituí-los por desenhos novos. A câmera elevada, o apoio, a escala em 1x/2x, a paleta e a colisão devem ser normalizados contra os arquivos nativos antes da montagem das fases.

Os tamanhos dos elementos e as alturas dos mapas são propostas. Comprimentos de 2.560/3.072 px, objetivos, tempos e condições narrativas seguem a história. Três emissores na fase 8 e três válvulas na 11 permanecem sugestões. O guia também registra os limites de tiles compartilhados e de instâncias visuais para evitar orçamentos inviáveis.

A implementação das fases fica para depois da aprovação do usuário. Esta entrega prepara o inventário, as dependências, as peças e os critérios para essa produção. A abertura já existente continua sendo o início da história, e o papel de Dinorah respeita sua sobrevivência na fase 12.

## Reprodução do documento

`build_guide.py` usa Python, ReportLab e Arial do macOS para compor o PDF e o guia Markdown com as imagens inteiras. Não recorta ou redesenha as pranchas. A pasta `qa` guarda paginação, renderizações e validação do documento.
