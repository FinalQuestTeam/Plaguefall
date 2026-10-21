# Worktree cangaço — build atual

Branch: `codex/cangaco-sprites-60`. Sprites consolidados para integração via PR na main.

Inimigos: `game/art/cangaco-insects-sized-v3/`; Damião: `game/art/cangaco-protagonista-iso60-v2/`. Todos mantêm oito direções, dois quadros de repouso e quatro de movimento no runtime. Os inimigos seguem os tamanhos originais de EnemyDef:16/24/32 pixels e48 para o chefe. As versões anteriores foram preservadas. A santa está em `game/art/santa-aparecida-v1/`, substituindo a antena24×24 nos mesmos11 tiles. A parceira está somente em concept, aguardando aprovação.

## Build e exportação

O Makefile reutiliza o SGDK da checkout principal quando não existe SDK local nesta worktree.

```sh
/opt/homebrew/bin/python3 game/tools/pack_actor_animation.py
make -C game clean
make -C game -j4
cp game/out/release/rom.bin game/out/rom.bin
```

Para apenas conferir o empacotamento, usar `pack_actor_animation.py --check`. ROM: [game/out/rom.bin](game/out/rom.bin), cópia idêntica de `game/out/release/rom.bin`.

## Resultado verificado

- ROM512 KiB; RAM estática6165 bytes; heap livre observado47332 bytes.
- Animação dos inimigos118080 bytes (antes299520); pool de inimigos em VRAM10 KiB (antes12).
- Inimigos comuns: uma peça de hardware; chefe48×48: quatro peças.
- Geometria visual e AABB usam os mesmos tamanhos e a mesma projeção dos tiros. Movimento, contato e IA mantêm as caixas no plano lógico original.
- 1380 casos de colisão no código de produção,600 na ROM executada,120 checagens de geometria SAT,128 quadros aleatórios,600 de estresse e1024 de reutilização/fragmentação do cache.
- Emulador:1159 VBlanks de teste funcional com os13 inimigos e Damião nas8direções.
- Arena completa:8 inimigos60FPS;15 inimigos31,75FPS. A atualização redundante do HUD foi reduzida para10Hz, com atributos atualizados imediatamente. Isso não garante quinze a60FPS.

[Relatório e arquivos da arte ativa](game/art/cangaco-insects-sized-v3/README.md) · [Auditoria desta build](game/art/cangaco-insects-sized-v3/validation/worktree-build.json)
