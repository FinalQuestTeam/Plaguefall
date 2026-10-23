#include "system/video/screens/loading.h"
// Chão da arena: pinta os char-maps 32x32 (16 tiles cada) e ladrilha o plano BG_B.
// Variantes simples (PEDRA/FLORESTA/CAVERNA) — uma por fase — e o esquema MIX,
// que mostra DOIS chões na mesma fase (rocha na arena + grama ao redor da lama)
// dividindo a única paleta do plano (PAL3). O flash da bomba clareia a paleta ativa.

#include "system/video/floor.h"
#include "system/video/sprites/floor_data.h"
#include "system/video/sprites/floor_tiles_data.h"
#include "core/game.h"         // ARENA_*
#include "levels/graph.h"
#include "levels/levels.h"     // LEVEL_current() -> retângulos de lama (esquema MIX)

// tabelas indexadas pela variante simples (FLOOR_STONE/FOREST/CAVE)
static const u16 *const FLOOR_PALS[FLOOR_VARIANTS] =
    { FLOOR_STONE_PAL, FLOOR_FOREST_PAL, FLOOR_CAVE_PAL };

// paleta do chão atualmente desenhado (usada pelo flash da bomba)
static const u16 *activePal = FLOOR_STONE_PAL;

// All five original char-maps are packed at build time. Borrowers no longer
// trigger pixel-by-pixel generation or a temporary heap allocation at runtime.
void FLOOR_init(void)
{
    LOADING_tiles(FLOOR_PACKED,TILE_USER_INDEX+FLOOR_TILE_BASE,FLOOR_TOTAL_TILES,DMA);
}

// o tile (tx,ty) está a até `pad` tiles de algum retângulo de lama? (esquema MIX)
static bool nearMud(u16 tx, u16 ty, const TileRect *rects, u16 count, s16 pad)
{
    for (u16 i = 0; i < count; i++)
    {
        const s16 x0 = rects[i].x - pad, x1 = rects[i].x + rects[i].w + pad;
        const s16 y0 = rects[i].y - pad, y1 = rects[i].y + rects[i].h + pad;
        if ((s16) tx >= x0 && (s16) tx < x1 && (s16) ty >= y0 && (s16) ty < y1)
            return TRUE;
    }
    return FALSE;
}

static void drawFloor(u8 variant,const LevelDef *def)
{
    if (arenaActive) return; // resident scenery owns PAL3 and BG_B
    FLOOR_init(); // a previous full-screen owner may have borrowed these tiles
    // ladrilha só o INTERIOR da arena (sem passar por baixo do HUD nem da borda)
    const u16 x0 = ARENA_TILE_X + 1, x1 = ARENA_TILE_X + ARENA_TILES_W - 1;
    const u16 y0 = ARENA_TILE_Y + 1, y1 = ARENA_TILE_Y + ARENA_TILES_H - 1;

    if (variant == FLOOR_MIX)
    {
        // dois chões: rocha na arena, grama ao redor da lama. Uma só paleta (PAL3).
        activePal = FLOOR_MIX_PAL;
        PAL_setColors(PAL3 * 16, activePal, 16, DMA);

        for (u16 ty = y0; ty < y1; ty++) {
            for (u16 tx = x0; tx < x1; tx++)
            {
                const bool grass = def->mud &&
                    nearMud(tx, ty, def->mud, def->mudCount, FLOOR_MIX_MUD_PAD);
                const u16 base = grass ? FLOOR_MIX_GRASS_BASE : FLOOR_MIX_ROCK_BASE;
                const u16 sub = (tx % 4) * 4 + (ty % 4);
                VDP_setTileMapXY(BG_B,
                    TILE_ATTR_FULL(PAL3, FALSE, FALSE, FALSE, TILE_USER_INDEX + base + sub),
                    tx, ty);
            }
            LOADING_poll();
        }
        return;
    }

    // variante simples: um único tileset + sua paleta
    if (variant >= FLOOR_VARIANTS) variant = FLOOR_STONE;
    const u16 base = FLOOR_TILE_BASE + variant * FLOOR_TILES;
    activePal = FLOOR_PALS[variant];
    PAL_setColors(PAL3 * 16, activePal, 16, DMA);

    for (u16 ty = y0; ty < y1; ty++) {
        for (u16 tx = x0; tx < x1; tx++)
        {
            const u16 sub = (tx % 4) * 4 + (ty % 4);   // sub-tile 32x32 (ordem coluna)
            VDP_setTileMapXY(BG_B,
                TILE_ATTR_FULL(PAL3, FALSE, FALSE, FALSE, TILE_USER_INDEX + base + sub),
                tx, ty);
        }
        LOADING_poll();
    }
}

void FLOOR_draw(u8 variant){drawFloor(variant,LEVEL_current());}
void FLOOR_preview(u8 node){const LevelDef *def=GRAPH[node].def;drawFloor(def->floor,def);}

void FLOOR_clear(void)
{
    VDP_clearPlane(BG_B, TRUE);
}

void FLOOR_setBright(u16 mix)
{
    if (arenaActive) { ARENA_bright(mix); return; }
    u16 out[16];
    for (u16 i = 0; i < 16; i++)
    {
        const u16 c = activePal[i];
        u16 r = (c >> 1) & 7, g = (c >> 5) & 7, b = (c >> 9) & 7;
        r += ((7 - r) * mix) >> 4;      // aproxima do branco (7) por mix/16
        g += ((7 - g) * mix) >> 4;
        b += ((7 - b) * mix) >> 4;
        out[i] = (u16) ((r << 1) | (g << 5) | (b << 9));
    }
    PAL_setColors(PAL3 * 16, out, 16, CPU);
}
