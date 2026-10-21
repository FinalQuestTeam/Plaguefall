#include "system/video/screens/titlecard.h"
#include "system/video/dust.h"
#include "system/audio/opening.h"
#include "core/game.h"
#include "titlecard_data.h"
#define ART_TILES 1120
#define DUST_TILE (TILE_USER_INDEX + ART_TILES)

static u16 brightness(u16 word, u16 level)
{
    return (((((word >> 1) & 7) * level + 16) / 32) << 1) |
           (((((word >> 5) & 7) * level + 16) / 32) << 5) |
           (((((word >> 9) & 7) * level + 16) / 32) << 9);
}

// A two-second eased breath. Only the three reserved core inks change.
static const u8 BREATH[32] = {
    0,0,1,2,3,4,5,7,8,10,11,12,13,14,15,16,
    16,16,15,14,13,12,11,9,8,6,5,4,3,2,1,0
};
static void colors(u16 level, u16 tick)
{
    const u16 *source = (const u16 *) titlecard_palettes;
    u16 palette[32];
    u16 pulse = BREATH[((u32) tick * 16 / fps) % 32];
    for (u16 i = 0; i < 32; i++)
    {
        u16 word = source[i];
        if ((i & 15) >= 13)
        {
            // Ease the existing warm inks between 75% and 100%. Different
            // channel thresholds stagger the VDP's discrete brightness steps.
            word = brightness(word, 24 + pulse / 2);
        }
        palette[i] = brightness(word, level);
    }
    PAL_setColors(PAL1 * 16, palette, 32, CPU);
    DUST_brightness(level);
}

static void clear(void)
{
    VDP_resetSprites(); VDP_updateSprites(1, DMA);
    VDP_clearPlane(BG_A, TRUE); VDP_clearPlane(BG_B, TRUE);
}

bool TITLECARD_run(void)
{
    u16 saved[64];
    const u16 priority = VDP_getTextPriority();
    PAL_getColors(0, saved, 64);
    VDP_setScreenWidth320();
    VDP_setScrollingMode(HSCROLL_PLANE, VSCROLL_PLANE);
    VDP_setHorizontalScroll(BG_A, 0); VDP_setVerticalScroll(BG_A, 0);
    VDP_setHorizontalScroll(BG_B, 0); VDP_setVerticalScroll(BG_B, 0);
    clear();
    PAL_setColors(0, palette_black, 64, CPU);
    VDP_setTextPlane(BG_A); VDP_setTextPalette(PAL0); VDP_setTextPriority(TRUE);
    VDP_drawText("APRESENTA", 15, 13);
    u16 prev = JOY_readJoypad(JOY_1);
    bool skipped = FALSE;
    const u16 fade = fps / 4;
    u16 end = fps * 6 / 5;
    for (u16 tick = 0; tick < end; tick++)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        if ((joy & ~prev) & BUTTON_START)
        {
            skipped = TRUE;
            if (end > tick + fade) end = tick + fade;
        }
        prev = joy;
        const u16 edge = tick < end - tick - 1 ? tick : end - tick - 1;
        PAL_setColor(15, brightness(0xEEE, edge < fade ? edge * 32 / fade : 32));
        SYS_doVBlankProcess();
    }
    if (skipped)
    {
        clear();
        VDP_setTextPriority(priority);
        PAL_setColors(0, saved, 64, CPU);
        return TRUE;
    }
    VDP_setEnable(FALSE);
    clear();
    VDP_loadTileData((const u32 *) titlecard_tiles, TILE_USER_INDEX, ART_TILES, DMA);
    DUST_load(DUST_TILE);
    for (u16 y = 0; y < 28; y++)
    {
        u16 row[40];
        for (u16 x = 0; x < 40; x++)
        {
            const u16 tile = y * 40 + x;
            row[x] = TILE_ATTR_FULL(PAL1 + titlecard_groups[tile], FALSE, FALSE, FALSE, TILE_USER_INDEX + tile);
        }
        VDP_setTileMapDataRow(BG_B, row, y, 0, 40, CPU);
    }
    DustParticle particles[DUST_COUNT];
    DUST_reset(particles, 0, 216);
    VDP_setEnable(TRUE);
    OPENING_start();
    end = fps * 4;
    for (u16 tick = 0; tick < end; tick++)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        if ((joy & ~prev) & BUTTON_START)
        {
            skipped = TRUE;
            if (end > tick + fade) end = tick + fade;
            OPENING_fadeOut(end - tick);
        }
        prev = joy;
        const u16 edge = tick < end - tick - 1 ? tick : end - tick - 1;
        colors(edge < fade ? edge * 32 / fade : 32, tick);
        DUST_update(particles, DUST_TILE, 216);
        SYS_doVBlankProcess();
    }
    clear();
    if (skipped) OPENING_stop();
    VDP_setTextPriority(priority);
    PAL_setColors(0, saved, 64, CPU);
    return skipped;
}
