# Bornal de recuperação — integrado

Desenho de couro de cangaceiro e regras aprovados em 22/10/2026. O item está
integrado ao jogo, à tela de derrota e às páginas 7/8 e 8/8 do **Como jogar**.

## Regras atuais — recuperação pela fotografia da morte

Em toda derrota, a vida volta a 100, o equipamento volta ao básico e uma
bolsa é deixada perto da queda. `DEATH_capture` guarda os valores anteriores;
a recuperação só acontece ao recolher. As rotas A/B usam a etapa correspondente.

| Etapas | Conteúdo que a bolsa devolve |
|---|---|
| 1–5 | Todas as melhorias, bombas, itens/cargas, modo de tiro e escudo restantes. |
| 6–11 | Melhorias anteriores menos uma de tiro e uma de velocidade, sem piso 3; perde o último item ocupado ou, sem itens, uma bomba. |
| 12–16 | Até +1 projétil se tinha melhoria de tiro, até +20% se tinha velocidade; condições independentes. Itens, bombas e efeitos não voltam. |

Sempre cai uma bolsa, mesmo vazia. Não existe concessão automática de bônus
que não havia antes da morte. A fotografia não é alterada por coletas novas:
a recuperação soma apenas seu conteúdo, respeitando os tetos. Itens que não
couberem no inventário continuam na bolsa, sem repetir as outras melhorias.
Outra morte substitui tudo pela fotografia da queda mais recente; morrer sem
recolher perde o conteúdo da bolsa anterior.

A bolsa fica em chão sem obstáculos/lava, perto da queda ou da entrada,
fora da posição de renascimento. Não expira nem entra no sorteio de inimigos.
Sair da fase, iniciar campanha/treino ou repor a sala 10 limpa a recuperação.
As salas comuns de treino mantêm seu equipamento inicial e duas bombas.

## Sprite nativo

![Bornal 16×16 ampliado sem suavização](bag-native-16x.png)

- `bag-pixels.json`: grade editável de 16×16 e índices da PAL1 existente.
- `bag-native.png`: PNG indexado, transparência no índice zero.
- `export.py`: exporta PNGs e `src/system/video/sprites/bag_data.h`; `--check`
  verifica a reprodução e o contorno claro em todo o perímetro.
- Quatro cores: contorno/estrela claros, couro marrom, sombra escura e reflexo
  quente. Quatro tiles, 128 bytes. A reserva de mortes tinha quatro tiles
  excedentes: agora usa seus 68 necessários, preservando o início do herói e
  do cenário, o pool de inimigos e o limite da fonte em 1440.

```sh
python3 game/art/bolsa-recuperacao-v1/export.py --check
python3 game/tools/test_death_rules.py
```

A lógica fica em `src/core/death.c`, com captura na derrota, reinício e coleta em `core/flow.c` / `items.c`.
O teste nativo usa os módulos reais com ASan/UBSan e cobre as 20 fases em
50/60 Hz, fotografia imutável, ausência de piso 3, bônus finais condicionais,
bolsa vazia, inventário cheio, perdas repetidas, posição segura, coleta sem
duplicação e permanência além de 65.535 quadros.

## Sala 10 — Regras de morte

Entre em **FASE TESTE → 10. REGRAS DE MORTE**. A provoca morte; START na
derrota repete com equipamento básico; caminhe até a bolsa para recuperar; B na arena repõe o equipamento; C troca
entre os três trechos e repõe. START → Configurar teste ajusta o equipamento
inicial. Tiro, velocidade, itens, bombas e mortes ficam visíveis no painel.
A sala usa a mesma lógica da campanha sem avançar suas rotas. Relatórios de
ensaio apenas com controles: `validation/bag-rules-v2/training-ntsc/report.json` e
`validation/bag-rules-v2/training-pal/report.json`.

## Emulador

A regra atual está validada em `validation/bag-rules-v2/`, com campanha,
sala 10 e ajuda em NTSC/PAL. Os relatórios na raiz de `validation/` registram
a regra anterior e permanecem como histórico.


`validation/ntsc/` e `validation/pal/` contêm os resultados de campanha e
capturas da ROM; `validation/interface-ntsc/` e `validation/interface-pal/`
contêm a conferência da ajuda no título/pausa. Cada relatório identifica o
hash da ROM usada. Os testes aceleram a montagem dos cenários por RAM; a
morte, repetição, aplicação das regras, desenho, coleta e navegação usam o
código de produção. Os pixels do bornal são comparados com a VRAM real.

## Conceitos preservados

- `bolsa-proposta.png`: primeira proposta ocre.
- `bolsa-couro-cangaceiro-v2.png`: conceito de couro aprovado.
- `previa-no-cenario-v1.png`: montagem gerada para avaliar contraste antes
  da implementação; **não é uma captura da ROM**.
- `prompt.txt`, `prompt-couro-v2.txt` e `prompt-previa-cenario-v1.txt`:
  prompts completos da geração com image_gen integrado.

A captura real está em `validation/bag-rules-v2/ntsc/bolsa-fase-12.png`.
