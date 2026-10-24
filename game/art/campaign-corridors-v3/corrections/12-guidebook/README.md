# Proposta isolada da fase 12

Candidata para revisão visual. Não foi ativada nem compilada em ROM. A versão ativa permanece intacta, confirmada pelos hashes em [reviews/review.json](reviews/review.json).

[Panorama 3072×320](complete-native.png) · [Cinco câmeras comparadas](reviews/comparison-5-cameras.png) · [Manifesto](manifest.json)

A primeira composição com todos os telhados de barro foi rejeitada por perder a identidade do estaleiro. Ela está preservada em `reviews/cycle1-all-clay-rejected/`.

A composição atual mantém telhas apenas no sindicato. Os demais prédios usam as coberturas metálicas da fonte existente da fase 12 em resolução de 1 px. Os cortes conservam cumeeira, plano, beiral e extremidades; a faixa de muro que aparecia acima da cobertura foi excluída. A ampliação acontece no canvas do telhado, sem redimensionar o prédio inteiro.

| Família | Altura total | Cobertura | Frente |
|---|---:|---:|---:|
| Oficina | 160 | 104 | 56 |
| Anexo | 128 | 88 | 40 |
| Doca coberta | 144 | 96 | 48 |
| Doca baixa | 112 | 72 | 40 |
| Sindicato | 176 | 120 | 56 |

O reboco vem de trechos claros da fachada original da igreja; o piso cinza usa o grão esparso do túnel nativo. O perímetro industrial reaproveita o módulo completo da fase 04 e a tubulação horizontal compartilhada com a fábrica 10. Janelas e emblema permanecem inteiros; portas pequenas e conjuntos de entrada foram normalizados como peças completas.

O atlas tem **508 de 640 tiles**, com deduplicação exata e reconstrução idêntica aos pixels indexados. As posições e os sólidos ativos foram preservados. A verificação encontrou 4.904 posições conectadas e percorreu 2.833 amostras da rota com margem de 8 px para o ator de 16×16.

As cinco câmeras são simulações nativas das regras atuais de câmera com a dupla próxima. Não são capturas de emulador. Uma integração futura ainda precisa confirmar enquadramento, rolagem, combate e desempenho.

Ressalvas para o parecer visual: as chapas azuis da fonte têm pouco desgaste no miolo; os seis anexos continuam repetindo a mesma implantação; o emblema elevado do sindicato precisa parecer apoiado no encontro entre telhado e fachada. A contagem de tiles e as verificações de percurso não aprovam esses pontos.

`build.py` escreve apenas nesta pasta. `review.py` compara a proposta com a versão ativa e produz as evidências. As fontes e os cortes usados estão relacionados no manifesto.
