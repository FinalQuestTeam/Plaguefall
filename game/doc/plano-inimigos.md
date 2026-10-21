# Plaguefall — Plano de Implementação: +9 Inimigos (cor = comportamento, forma = perfil)

> Expandir de **3 para 12 inimigos** numa **grade 4 cores × 3 formas**. A **cor** ensina o *comportamento* (o jogador lê a ameaça na hora); a **forma** define o *perfil*: quadrado = mais resistente, triângulo = mais agressivo, pentágono = elite. Cada forma acrescenta uma **variação** do comportamento da cor, e o pentágono ganha um **truque extra**.
> Plano de design + engenharia — valores são pontos de partida, ajustáveis no balanceamento.

---

## 1. A linguagem de leitura (cor + forma)

O jogador aprende **4 cores** e **3 formas** e consegue prever qualquer um dos 12 inimigos:

### Cor = comportamento base (vale em qualquer forma)
| Cor | Comportamento | O que o jogador aprende |
|---|---|---|
| 🔴 Vermelho | **Atirador** — dispara projéteis mirados | "vermelho atira: fique em movimento" |
| 🟡 Amarelo | **Perseguidor** — vai ao seu encontro (contato) | "amarelo corre atrás: não deixe encostar" |
| 🟣 Roxo | **Blindado** — ergue escudo em ciclos (invulnerável ~2 s) | "roxo se protege: não desperdice tiro" |
| 🟠 Laranja | **Investida** — telegrafa e dá dash reto | "laranja avança: esquive na hora do bote" |

### Forma = perfil + variação do comportamento
| Forma | Perfil | Variação sobre o comportamento da cor |
|---|---|---|
| ■ Quadrado — "Bruto" | **Mais resistente** (maior HP), ritmo estável | comportamento na forma "pura" e pesada |
| ▲ Triângulo — "Lâmina" | **Mais agressivo** (HP mínimo, o mais veloz) | comportamento intensificado (mais rápido/frequente) |
| ⬠ Pentágono — "Elite" | Grande, raro, drop alto | comportamento **+ truque extra** |

> Regra de ouro: **cor nunca mente**. Um triângulo vermelho e um quadrado vermelho fazem a mesma coisa (atirar); mudam a velocidade, a resistência e a intensidade — não o "tipo" de ameaça.

---

## 2. A grade completa (4 × 3 = 12)

Legenda: **Tam.** lado do sprite (px) · **HP** tiros p/ morrer · **Dano** contato · **Drop** chance de item.

| Cor \ Forma | ■ Quadrado (resistente) | ▲ Triângulo (agressivo) | ⬠ Pentágono (elite + extra) |
|---|---|---|---|
| 🔴 **Vermelho** (atirador) | **Torreão** — HP 4, 16px, dano 8. Quase fixo, 1 tiro mirado / 2 s. Drop 45% | **Fuzileiro** — HP 1, 16px, dano 6. Veloz, atira em rajada (~1 s). Drop 20% | **Artilheiro** — HP 3, 24px, dano 10. *Extra:* **leque de 3 tiros**. Drop 60% |
| 🟡 **Amarelo** (perseguidor) | **Batedor** — HP 4, 16px, dano 8. Persegue firme e lento. Drop 40% | **Caçador** — HP 1, 16px, dano 8. Perseguição rápida (o mais veloz). Drop 20% | **Alcateia** — HP 3, 24px, dano 10. *Extra:* **divide-se em 2** ao morrer. Drop 55% |
| 🟣 **Roxo** (blindado) | **Baluarte** — HP 6, 32px, dano 15. Persegue devagar + escudo cíclico (o tanque supremo). Drop 75% | **Escudeiro** — HP 2, 16px, dano 10. Rápido, escudo curto e frequente. Drop 30% | **Fortaleza** — HP 4, 32px, dano 15. *Extra:* **invoca lacaios** enquanto blindado. Drop 80% |
| 🟠 **Laranja** (investida) | **Aríete** — HP 4, 16px, dano 12. Dash lento-telegrafado e forte. Drop 45% | **Adaga** — HP 1, 16px, dano 10. Dashes rápidos e repetidos. Drop 25% | **Meteoro** — HP 3, 24px, dano 14. *Extra:* **teleporta e então investe**. Drop 60% |

Os 3 atuais (Torreão, Batedor→hoje "Perseguidor", Baluarte→hoje "Tanque") entram nessa grade com **HP revisado** (ver §3). Novos: os outros 9.

---

## 3. Resistência (HP) e dano

**Quadrados são os mais resistentes; triângulos os mais frágeis; pentágonos no meio.** Isso inverte a lógica antiga (onde o pentágono era o mais tanque): agora o tanque supremo é o **Baluarte (quadrado roxo, HP 6)**.

| Forma | Faixa de HP | Papel |
|---|---|---|
| ■ Quadrado | 4 (roxo 6) | absorve tiros; ameaça por atrito |
| ▲ Triângulo | 1 (roxo 2) | morre num tiro; ameaça por velocidade/volume |
| ⬠ Pentágono | 3 (roxo 4) | elite; ameaça pelo truque + tamanho |

Dano de contato: triângulos batem forte para a fragilidade (troca justa), roxo é o mais pesado (15), laranja alto (12–14, é um projétil vivo). Todos respeitam a invencibilidade de 0,3 s do jogador.

---

## 4. Drops equilibrados

Chance de drop acompanha o **esforço para matar** (HP × dificuldade de acertar). Médias por forma:

| Forma | Drop médio | Racional |
|---|---|---|
| ▲ Triângulo | ~21% | morre num tiro e aparece em volume → recompensa pequena |
| ■ Quadrado | ~51% | exige vários tiros → recompensa média-alta |
| ⬠ Pentágono | ~64% | raro e perigoso → recompensa alta |

Gradiente **triângulo < quadrado < pentágono**, mantendo o fluxo de itens estável (teto de 8 no chão). O sorteio de *qual* item cai continua global (coração 70% / bomba 30%); opcional futuro: peso por inimigo.

---

## 5. Cores e paleta — o ganho da classificação

Como só existem **4 cores de inimigo**, e 3 já estão na PAL1 (vermelho=3, amarelo=4, roxo=8), **basta adicionar 1 cor: laranja** (índice 12). **Não é preciso PAL2** — tudo cabe na PAL1 (16 cores). A ideia de classificação por cor **resolveu sozinha** o gargalo de paleta do plano anterior.

- Estado **blindado** (roxo): sinal visual reutilizando o contorno claro pulsando, ou 1 cor opcional de "brilho de escudo" (índice 13). No máximo **+2 cores** no total.
- O tiro do jogador reusa o amarelo (4) e o tiro inimigo o laranja-avermelhado (5), como hoje — sem conflito, pois cor de inimigo ≠ cor de projétil na leitura.

---

## 6. Arquitetura: um arquivo por inimigo (config centralizada)

Objetivo do usuário: **cada inimigo num arquivo, bem segmentado e fácil de configurar.** Solução: separar **configuração** (dados por inimigo) de **comportamento** (lógica compartilhada por cor).

### 6.1 Config por inimigo — `EnemyDef`
Cada inimigo é uma linha de dados; todos os "botões" de ajuste ficam num só lugar:
```c
typedef struct EnemyDef {
    const char *name;
    u8  shape;        // SHAPE_SQUARE / TRIANGLE / PENTAGON
    u8  color;        // COLOR_RED / YELLOW / PURPLE / ORANGE  (= comportamento)
    u8  size;         // 16 / 24 / 32
    u8  hp;
    u8  contactDmg;
    u8  dropChance;   // %
    u16 speedFp;      // velocidade (perseguição/dash) em 26.6
    u16 timerA, timerB; // cadências do comportamento (ex.: intervalo de tiro; escudo on/off; intervalo de dash)
    u8  extra;        // truque do pentágono: EXTRA_NONE / SPREAD / SPLIT / SUMMON / TELEPORT
    void (*behavior)(Enemy*, const struct EnemyDef*);  // função da COR
} EnemyDef;
```

### 6.2 Comportamento compartilhado por cor (não se repete)
São **4 funções**, uma por cor, que leem os parâmetros do `EnemyDef` e aplicam o truque extra quando houver:
`BEH_shooter`, `BEH_chaser`, `BEH_shielded`, `BEH_charger`. A variação por forma sai naturalmente dos parâmetros (velocidade, cadência, HP) — sem duplicar lógica.

### 6.3 Estrutura de pastas proposta
```
enemies/
├── enemies.h          // struct Enemy, enums, EnemyDef, API pública
├── enemies.c          // spawn (via def), dispatch, dano de contato, damageBox
├── behaviors.c/.h     // BEH_shooter/chaser/shielded/charger + helpers (dash, spread, split, summon, teleport, escudo)
└── defs/              // 1 ARQUIVO POR INIMIGO — só configuração (fácil de ajustar)
    ├── sq_red.c   sq_yellow.c   sq_purple.c   sq_orange.c
    ├── tri_red.c  tri_yellow.c  tri_purple.c  tri_orange.c
    └── pen_red.c  pen_yellow.c  pen_purple.c  pen_orange.c
```
Cada arquivo em `defs/` tem só um `const EnemyDef ...` — abrir o arquivo é ver/ajustar todos os números daquele inimigo. Uma tabela `ENEMY_DEFS[]` (em `enemies.c`) agrega as 12 defs por índice de tipo.

> Alternativa (se preferir): colocar a lógica junto da config no mesmo arquivo. Não recomendo, pois a lógica é por **cor** (compartilhada pelas 3 formas) e seria duplicada 3×. Manter config (12 arquivos) + comportamento (4 funções) é o mais "fácil de configurar".

### 6.4 Campos novos na struct `Enemy`
Estado por inimigo, reaproveitado conforme o comportamento (documentado por cor):
- `u16 tA, tB;` — cadências ativas (tiro, escudo on/off, intervalo de dash).
- `u8 mode;` — sub-estado (perseguir vs. investir; escudo erguido; já dividiu).
- `bool shielded;` — roxo; **`ENEMIES_damageBox` ignora inimigos com `shielded`** (o feedback de "tiro sem efeito" ensina a mecânica).

---

## 7. Outros pontos técnicos

- **Formas procedurais:** adicionar rasterizador de triângulo e pentágono no `gfx.c` (como coração/bomba): `buildShape(baseTile, size, colTiles, forma, cor)`. Colisão continua **AABB pela caixa** (simples; hitbox um pouco generosa — refino opcional).
- **Sinal de escudo:** ao ficar `shielded`, desenhar contorno pulsante (troca de tile ou flag de highlight) para o jogador entender o "não adianta atirar agora".
- **VRAM (tiles):** 16px=4, 24px=9, 32px=16. Novos ≈ 70 tiles; total ~116, dentro da área de usuário do SGDK. Lacaios/estilhaços **reusam** o tile de quadrado pequeno.
- **`MAX_ENEMIES`:** subir de 10 para **16** (Alcateia divide e Fortaleza invoca criam inimigos em runtime). Conferir limite de sprites do MD (80/quadro; aglomerado de 32px pode piscar por linha — aceitável).
- **Helpers novos:** dash (acelera rumo a ponto travado), reflexão em parede (se algum comportamento errante for usado), `fireEnemySpread(n)` (leque), `ENEMIES_spawnAt(type,x,y)` (divisão/invocação), teleporte, flag de escudo em `damageBox`.

---

## 8. Sequência de implementação

> **Status:** Fases A–D **implementadas** (12 inimigos, formas procedurais, 4 comportamentos por cor, truques dos pentágonos, escudo, cor laranja, `MAX_ENEMIES` 16). Fase E parcial: fases 1–5 já usam a nova grade; falta o ajuste fino por playtest e regenerar o `GDD.md`.


**Fase A — Fundação (sem inimigo novo; validar que os 3 atuais ficam idênticos):**
1. `EnemyDef` + tabela `ENEMY_DEFS[]`; migrar tamanho/HP/dano/drop/tile/velocidade para os `defs/`.
2. Dispatch por ponteiro de função (`def->behavior`).
3. `defs/` com os 3 atuais (sq_red, sq_yellow, sq_purple) + HP revisado.
4. Rasterizador `buildShape` no `gfx.c` (quadrado já existe; add triângulo e pentágono) e a cor **laranja** na paleta.

**Fase B — Completar os quadrados e os comportamentos por cor:**
5. `BEH_shooter/chaser/shielded/charger` parametrizados. Adicionar **sq_orange (Aríete)** e o **escudo do roxo** (sq_purple ganha o ciclo de escudo + flag em `damageBox`).

**Fase C — Triângulos (agressivos, reusam os 4 comportamentos com params rápidos e HP 1):**
6. tri_red, tri_yellow, tri_purple, tri_orange — em geral só configuração nova sobre os comportamentos da Fase B.

**Fase D — Pentágonos (elite + truque extra, exigem sistemas novos):**
7. `fireEnemySpread` (pen_red), `ENEMIES_spawnAt` + divisão (pen_yellow), invocação (pen_purple), teleporte-investida (pen_orange). Subir `MAX_ENEMIES`.

**Fase E — Balanceamento e integração:**
8. Ajuste fino de HP/dano/drop/velocidades e cadências (tudo nos `defs/`).
9. Introduzir por fase (ver §9), atualizar o **GDD** (`doc/GDD.md`).

Cada fase é validável no emulador antes da próxima.

---

## 9. Progressão sugerida nas fases

O `LevelDef.enemyTypes` já aceita qualquer combinação. Ensinar as cores antes de misturar:

| Fases | Introduz | Ideia |
|---|---|---|
| 1–4 (atuais) | Quadrados (as 4 cores, aos poucos) | ensina a "ler" cada cor com inimigos resistentes e lentos |
| 5–7 | + Triângulos | mesma leitura de cor, agora rápido → testa reflexo |
| 8–10 | + Pentágonos | elite + truques; escudo/invocação/leque/teleporte |
| clímax | mistura + Fortaleza | horda com invocação |

---

## 10. Decisões já tomadas e em aberto

**Tomadas (por você):** cor = comportamento com **variação por forma**; **roxo = blindado/escudo**; pentágonos com **truque extra** além da cor; quadrados = mais resistentes; triângulos = mais agressivos.

**Em aberto (posso decidir com bom senso, mas confirme se quiser mudar):**
- Cor exata do laranja e se o escudo ganha 1 cor própria (índice 13) ou reusa o contorno pulsante.
- Tamanho dos pentágonos "normais": 24px (mais barato) vs. 32px. Sugiro 24, com Baluarte/Fortaleza em 32.
- Colisão AABB (recomendado agora) vs. hitbox por forma.
