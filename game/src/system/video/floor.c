// Chão da arena: pinta os char-maps 32x32 (16 tiles cada) e ladrilha o plano BG_B.
// Variantes simples (PEDRA/FLORESTA/CAVERNA) — uma por fase — e o esquema MIX,
// que mostra DOIS chões na mesma fase (rocha na arena + grama ao redor da lama)
// dividindo a única paleta do plano (PAL3). O flash da bomba clareia a paleta ativa.

#include "system/video/floor.h"
#include "system/video/sprites/floor_data.h"
#include "core/game.h"         // ARENA_*
#include "levels/levels.h"     // LEVEL_current() -> retângulos de lama (esquema MIX)

// tabelas indexadas pela variante simples (FLOOR_STONE/FOREST/CAVE)
static const char *const *const FLOOR_ARTS[FLOOR_VARIANTS] =
    { FLOOR_STONE_ART, FLOOR_FOREST_ART, FLOOR_CAVE_ART };
static const u16 *const FLOOR_PALS[FLOOR_VARIANTS] =
    { FLOOR_STONE_PAL, FLOOR_FOREST_PAL, FLOOR_CAVE_PAL };

// paleta do chão atualmente desenhado (usada pelo flash da bomba)
static const u16 *activePal = FLOOR_STONE_PAL;

// pinta um char-map 32x32 em 16 tiles (ordem coluna, como os sprites)
static void paintFloor(u32 *buf, const char *const art[32])
{
    for (u16 y = 0; y < 32; y++)
    {
        for (u16 x = 0; x < 32; x++)
        {
            const char ch = art[y][x];
            const u16 col = (ch <= '9') ? (u16) (ch - '0') : (u16) (ch - 'a' + 10);
            const u16 tile = (x / 8) * 4 + (y / 8);
            buf[tile * 8 + (y % 8)] |= (u32) col << ((7 - (x % 8)) * 4);
        }
    }
}

// gera um tileset na VRAM a partir do seu char-map
static void loadVariant(u16 base, const char *const art[32])
{
    u32 *buf = MEM_alloc(FLOOR_TILES * 8 * (u16) sizeof(u32));
    memset(buf, 0, FLOOR_TILES * 8 * (u16) sizeof(u32));
    paintFloor(buf, art);
    VDP_loadTileData(buf, TILE_USER_INDEX + base, FLOOR_TILES, DMA);
    MEM_free(buf);
}

void FLOOR_init(void)
{
    for (u8 v = 0; v < FLOOR_VARIANTS; v++)
        loadVariant(FLOOR_TILE_BASE + v * FLOOR_TILES, FLOOR_ARTS[v]);
    // tilesets do esquema MIX (grama + rocha na mesma paleta)
    loadVariant(FLOOR_MIX_GRASS_BASE, FLOOR_MIXGRASS_ART);
    loadVariant(FLOOR_MIX_ROCK_BASE,  FLOOR_MIXROCK_ART);
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

void FLOOR_draw(u8 variant)
{
    if (arenaActive) return; // resident scenery owns PAL3 and BG_B
    // ladrilha só o INTERIOR da arena (sem passar por baixo do HUD nem da borda)
    const u16 x0 = ARENA_TILE_X + 1, x1 = ARENA_TILE_X + ARENA_TILES_W - 1;
    const u16 y0 = ARENA_TILE_Y + 1, y1 = ARENA_TILE_Y + ARENA_TILES_H - 1;

    if (variant == FLOOR_MIX)
    {
        // dois chões: rocha na arena, grama ao redor da lama. Uma só paleta (PAL3).
        activePal = FLOOR_MIX_PAL;
        PAL_setColors(PAL3 * 16, activePal, 16, DMA);

        const LevelDef *def = LEVEL_current();
        for (u16 ty = y0; ty < y1; ty++)
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
        return;
    }

    // variante simples: um único tileset + sua paleta
    if (variant >= FLOOR_VARIANTS) variant = FLOOR_STONE;
    const u16 base = FLOOR_TILE_BASE + variant * FLOOR_TILES;
    activePal = FLOOR_PALS[variant];
    PAL_setColors(PAL3 * 16, activePal, 16, DMA);

    for (u16 ty = y0; ty < y1; ty++)
        for (u16 tx = x0; tx < x1; tx++)
        {
            const u16 sub = (tx % 4) * 4 + (ty % 4);   // sub-tile 32x32 (ordem coluna)
            VDP_setTileMapXY(BG_B,
                TILE_ATTR_FULL(PAL3, FALSE, FALSE, FALSE, TILE_USER_INDEX + base + sub),
                tx, ty);
        }
}

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
