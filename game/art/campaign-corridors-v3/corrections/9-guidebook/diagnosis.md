# Fase9: comparação com a direção visual existente

A9v3 rejeitada muda a linguagem gráfica. A aprovação anterior de recortes/enquadramentos não verificou adequadamente projeção, material ou continuidade do kit. Caber na memória e ter prédios inteiros não corrige esse desvio.

## Referências lidas e inspecionadas

- `game/doc/historia/guia-producao-visual-fases.md`: linha11 define ortográfica elevada próxima de60°, normalizada ao pátio e aos atores; linhas518–555 definem a9. Linhas528–539 pedem kit urbano, veículos, muros, piso e portões/tubos existentes, com apenas2–3marcos exclusivos. A entrega da linha551 inclui vista da fábrica e encaixe da entrada com10/11.
- `game/doc/historia/storyboard-campanha.md`, linhas325–365, e `game/art/storyboard-campanha-v1/imagens/04-fabrica-escolta.png`: quadroA mostra aproximação industrial, fábrica reconhecível, tubulações e veículos pesados abandonados. É direção narrativa/cinemática; sua perspectiva não substitui a câmera ortográfica do jogo.
- `game/art/guia-assets-campanha-v1/imagens/01-igreja-rua-galpao.png`: K1C esquina/sarjeta gasta, K1D porta de galpão, K1E pilar com apoio. `.../imagens/04-fabrica-estaleiro.png`: K4A tubos azuis enferrujados, K4B caldeira, K4C painel. São estudos ampliados, não sprites finais automaticamente aprovados; README e guia exigem normalização contra o nativo.
- `game/art/phase01-courtyard-v2/intact-native.png` e README: referência aprovada pelo usuário em21/10; roof dominante, frente curta, ocre, cal gasta, azul desbotado e acabamento1px.
- `game/art/phase02a-service-v1/map-native.png`: pátina de cal/metal, piso com grão esparso e limites completos.
- `game/art/phase04-tunnels-v1/map-native.png` e `design.json`: parede industrial nativa, apoios, flangeamento, ferrugem e canalizações completos; grão1px no piso. Referência concreta para o entorno industrial.
- `game/art/campaign-corridors-v3/streets/9/complete-native.png`, `build.py` e capturas reais `game/art/campaign-corridors-v3/captures/ntsc/9/landmark-0.png`.
- `game/art/campaign-pattern-v2/factory/cycle-2/factory-native.png` e capturas reais `.../captures/ntsc/{10,11}/x1-y1.png`: continuidade da entrada e equipamentos. Essas salas também possuem grandes áreas lisas; não são justificativa para apagar a pátina do restante do jogo.

## Desvios concretos da9v3

1. **Câmera/projeção:** office304×160 em[64,32] usa56px de cobertura e aproximadamente104px de frente. A doca privilegia64/96. A igreja original tem aproximadamente60–65px de topo para25–30px de frente. A proporção comprova predominância frontal; não é medição matemática do ângulo. Alterar a câmera para caber o bbox mantém essa projeção diferente.
2. **Escala aparente:** a fachada do office equivale a aproximadamente3humanos de tinta33px; o front da igreja original é menor que1. A porta32×40 da9, isoladamente, é plausível. Não procede dizer que toda peça é grande demais: a inconsistência aparece no conjunto altura/profundidade/material.
3. **Cores e ambiente:** asfalto cinza uniforme, grandes paredes marrons/creme, coberturas cinzentas e faixas regulares de verde/grades parecem um campus industrial limpo. A referência é poeira ocre, carvão, cal descascada, ferrugem e azul sujo, com luzes discretas. O guia não proíbe cinza; proíbe implicitamente a substituição da linguagem inteira por outra biblioteca.
4. **Textura:** `streets/9/build.py:38` substitui todo o módulo de rua pela cor5; linhas48–50 montam grandes fachadas com amostras lisas. A grade2px de vários componentes e a ausência de desgaste1px contrastam com o piso/muros/tubos originais. Acrescentar ruído sobre os mesmos prédios frontais não corrigiria a câmera.
5. **Kit/continuidade:** o portão224×144 novo não repete a porta80×64 e o quadro de serviço usados em10/11. Usar tubulação, ferrugem e a própria entrada antiga evita inventar outra fábrica entre exterior e interior. Isso não implica alterar10/11 ou alegar que essas salas são perfeitas estilisticamente.

## Recursos existentes úteis

- Piso e perímetros de `phase01-courtyard-v2/intact-native.png`; porta/câmara/escala do pátio são a régua, não devem ser redesenhadas.
- `phase03-street-v2/source/street-kit.png`: oficina completa na segunda célula superior. A proposta converte a silhueta integral desde essa fonte em128×128, em1px; não amplia o sprite64×64 já reduzido e não fabrica um prédio por quadriláteros.
- `phase03-street-v2/assets/{car,van,barricade,lamp,curb}.png`: recursos urbanos nativos já existentes, se necessário. Não é recomendável repetir15veículos para preencher o mapa.
- `routes-2048-v2/source/evacuation-cutouts.png`: caminhão azul/ferrugem completo na célula superior direita; também há toldo e portão completos. A proposta usa o caminhão em96×64, duas posições/orientações, sem kit novo.
- `phase04-tunnels-v1/map-native.png`: parede completa[80,0,64,80] e painel de serviço completo[336,0,96,80], que inclui toda a válvula/pano vermelho e seu suporte. Usar como partes do mesmo muro, não como quadrados de máquina soltos sobre outro fundo.
- `campaign-pattern-v2/factory/modules/factory-door.png`:80×64, entrada existente de10/11. A proposta conserva todos os seus13RGB e todos os pixels.
- Outros recursos existentes úteis mas excluídos desta montagem para reduzir famílias: `factory-tanks.png`, `factory-supply-header.png` e `factory-corner-nw.png` no mesmo diretório; `phase03-shelter-v1/map-native.png` possui banco de manutenção inteiro[16,0,80,96]. Não se deve simplesmente colar esse retângulo de outro cômodo sobre o exterior.

A proposta isolada continua dependente da revisão do panorama e das cinco câmeras. Textura recuperada, porta exata e630tiles não constituem aprovação visual.
