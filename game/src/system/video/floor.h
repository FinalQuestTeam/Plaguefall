#ifndef FLOOR_H
#define FLOOR_H

#include <genesis.h>
#include "system/video/sprites/tiles.h"

// Chão da arena (pedra basketweave, recriado de img/floor.webp com a técnica de
// char-map). Tile 32x32 (16 tiles) ladrilhado no plano de fundo BG_B; paleta PAL3.
// Fica atrás de tudo (borda/HUD/elementos em BG_A, sprites por cima).

// Base na VRAM após a reserva de animação de Damião (48 tiles).
// As variantes ficam residentes em sequência: cada uma em FLOOR_TILE_BASE + v*16.
#define FLOOR_TILE_BASE  (HERO_TILE_BASE + HERO_RESERVED_TILES)
#define FLOOR_TILES      16    // 32x32 (por variante)

// variantes do chão (índice usado no campo LevelDef.floor)
#define FLOOR_STONE      0     // pedra (padrão)
#define FLOOR_FOREST     1     // grama/terra (fases de lama)
#define FLOOR_CAVE       2     // rocha úmida/pegajosa
#define FLOOR_VARIANTS   3     // nº de variantes simples (tiles em sequência)

// esquema MIX: dois chões na MESMA fase, dividindo a PAL3 — rocha na arena e
// GRAMA ao redor da lama (a região vem dos retângulos de lama do def). Como a
// rocha é a base, a área da lava fica sobre rocha. Ideal p/ fases lava+lama.
#define FLOOR_MIX        3
#define FLOOR_MIX_GRASS_BASE (FLOOR_TILE_BASE + FLOOR_VARIANTS * FLOOR_TILES)
#define FLOOR_MIX_ROCK_BASE  (FLOOR_MIX_GRASS_BASE + FLOOR_TILES)

// nº de tiles que o chão ocupa na VRAM (3 simples + 2 do mix)
#define FLOOR_TOTAL_TILES    ((FLOOR_VARIANTS + 2) * FLOOR_TILES)

// alcance (em tiles) da grama ao redor de cada retângulo de lama, no esquema MIX
#define FLOOR_MIX_MUD_PAD    2

void FLOOR_init(void);              // gera os 2 tilesets (boot)
void FLOOR_draw(u8 variant);       // preenche o BG_B com o chão da variante + paleta
void FLOOR_clear(void);             // limpa o BG_B (voltar ao título / preparação)
void FLOOR_setBright(u16 mix);      // 0..16: mistura o chão com branco (flash da bomba)

#endif // FLOOR_H
