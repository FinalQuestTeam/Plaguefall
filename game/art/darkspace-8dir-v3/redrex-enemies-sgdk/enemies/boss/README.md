# boss — Lacraia

Definição: [`boss.c`](../../../../../src/enemies/defs/boss.c).

- Tipo: `ENEMY_BOSS` = `14`.
- Dados: `ENEMYDEF_boss`.
- Recurso SGDK: `enemy8_boss`.
- Folha completa: [`boss.png`](boss.png), 192×768.
- Oito folhas de 192×96 em `directions/`: N, NE, L, SE, S, SO, O, NO.
- Oito vistas: [`boss_turntable.png`](boss_turntable.png).
- GIFs em `previews/`; fonte da arte em `originals/`.

Células 32×48, quatro frames de repouso e seis de corrida por direção.
Paleta, mapeamento de animações e recursos ficam na raiz do pacote.
