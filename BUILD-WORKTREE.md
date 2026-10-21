# Build em worktrees

O Makefile de `game/` procura o SGDK local e reutiliza o SDK da checkout principal quando ele não existe na worktree. Também é possível definir `GDK` explicitamente.

```sh
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
make -C game -j4
python3 game/tools/check.py
```

A ROM principal é [game/out/release/rom.bin](game/out/release/rom.bin). O build não exige copiar a ROM para outro diretório. Objetos, dependências e compilações alternativas são ignorados pelo Git.

[Configuração e testes](game/doc/desenvolvimento.md) · [Validação atual](game/doc/build-validation.json) · [Arte ativa](game/art/README.md). As auditorias antigas de desempenho continuam nas pastas dos respectivos estudos e não representam a build atual.
