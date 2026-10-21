# Rodapé aprovado integrado

Nome do destino e duas frases centralizados no grid de 8 px. Comandos à direita com margem de 8 px. Sem prefixos AGORA/PROXIMA. As 23 transições têm texto próprio; os nove exemplos aprovados são a fonte do exportador.

A fonte existente usa PAL0 para explicações e PAL3 para título/ação; as quatro paletas são restauradas na saída. Não foram adicionados tiles à fonte, arte ou orçamento do overlay.

## Validação

- ROM de produção no Genesis Plus GX: 23 transições e duas campanhas de 16 etapas em cada sistema NTSC/PAL.
- Conteúdo e alinhamento das linhas, paletas, margens, fundo e substituição do comando de viagem verificados em VRAM.
- Entrada em sete fases iniciais revalidada em NTSC/PAL. Recursos e testes nativos de áudio/jogador passaram.
- A preparação de fases e resultados é acelerada por RAM; mapa, viagem, saída e entrada seguinte usam somente controles sob bloqueio de escrita.
- Sem validação em hardware físico ou CRT.

`build-validation.json` registra hash da ROM e relatórios. `validation/build-before.json` preserva a validação anterior.

Regenerar textos: `python3 game/art/routemap-footer-ux-v1/export_footer.py`. Conferir: adicionar `--check`.
Regenerar galeria: `python3 game/art/routemap-footer-ux-v1/integracao/revisao.py`.
