// Illustrated epilogue; same framing, fades, typewriter and dust as the opening.
#include "system/video/screens/ending.h"
#include "system/video/screens/ending_shots.h"
#include "system/audio/audio.h"
#include "system/audio/music.h"
#include "system/audio/sfx.h"
#include "text_data.h"
#include "intro_data.h"
#include "core/game.h"
#include "system/video/dust.h"
#include "ending_data.h"

#define TEXT_TOP 22
#define TEXT_ROWS 6
#define FADE_LEVELS 32
#define PARTICLE_TILE (TILE_USER_INDEX + ENDING_FRAME_TILES)

static void imageBrightness(const u16 *source, u16 level)
{
    u16 colors[32];
    for (u16 i = 0; i < 32; i++)
    {
        const u16 word = source[i];
        colors[i] = (((((word >> 1) & 7) * level + 16) / FADE_LEVELS) << 1) |
                    (((((word >> 5) & 7) * level + 16) / FADE_LEVELS) << 5) |
                    (((((word >> 9) & 7) * level + 16) / FADE_LEVELS) << 9);
    }
    PAL_setColors(PAL1 * 16, colors, 32, CPU);
    DUST_brightness(level);
}

static void drawText(const EndingCaption *shot, u16 *typed, u16 target)
{
    u16 offset = 0;
    const u16 firstY = TEXT_TOP + (TEXT_ROWS - shot->lineCount) / 2;
    for (u16 row = 0; row < 4; row++)
    {
        const char *line = shot->lines[row];
        // Anchor each line to its final width, so typing never shifts the text.
        const u16 firstX = (40 - strlen(line)) / 2;
        for (u16 col = 0; line[col]; col++, offset++)
        {
            if (offset >= target) { *typed = target; return; }
            if (offset >= *typed)
            {
                char letter[2] = { line[col], 0 };
                VDP_drawText(letter, firstX + col, firstY + row);
            }
        }
    }
    *typed = target;
}

static void loadShot(u16 index)
{
    const u8 *groups = ending_groups + (u32) index * ENDING_FRAME_TILES;
    u16 row[ENDING_TILES_W];
    SYS_doVBlankProcess();
    VDP_setEnable(FALSE);
    VDP_resetSprites();
    VDP_updateSprites(1, DMA);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    PAL_setColors(PAL1 * 16, palette_black, 16, CPU);
    PAL_setColors(PAL2 * 16, palette_black, 16, CPU);
    PAL_setColors(PAL3 * 16, palette_black, 16, CPU);
    // Flush the outgoing transition's final queued fade before setting ink.
    // Otherwise that DMA turns PAL0 black on the first illustrated frame.
    PAL_setColor(0, 0);
    PAL_setColor(1, 0);
    PAL_setColor(15, RGB24_TO_VDPCOLOR(0xFFFFFF));
    VDP_loadTileData((const u32 *)(ending_tiles + (u32) index * ENDING_FRAME_TILES * 32),
                    TILE_USER_INDEX, ENDING_FRAME_TILES, DMA);
    DUST_load(PARTICLE_TILE);
    for (u16 y = 0; y < ENDING_TILES_H; y++)
    {
        for (u16 x = 0; x < ENDING_TILES_W; x++)
        {
            const u16 tile = y * ENDING_TILES_W + x;
            row[x] = TILE_ATTR_FULL(PAL1 + groups[tile], FALSE, FALSE, FALSE, TILE_USER_INDEX + tile);
        }
        VDP_setTileMapDataRow(BG_B, row, y, 0, ENDING_TILES_W, CPU);
    }
    // A fixed 8px crop on either side. The exported bottom edge fades to black;
    // rows 22..27 of BG_B are empty, so no rectangular UI mask is necessary.
    VDP_setHorizontalScroll(BG_B, -8);
    VDP_setVerticalScroll(BG_B, 0);
    VDP_setEnable(TRUE);
}

void ENDING_run(void)
{
    u16 savedPalette[64];
    DustParticle particles[DUST_COUNT];
    const u16 savedPriority = VDP_getTextPriority();
    const bool savedEnable = VDP_getEnable();
    const u16 savedTextPalette = VDP_getTextPalette();
    VDP_setWindowOff();
    MUSIC_setEnemies(0);
    PAL_getColors(0, savedPalette, 64);
    VDP_setScreenWidth320();
    VDP_setScrollingMode(HSCROLL_PLANE, VSCROLL_PLANE);
    VDP_setHorizontalScroll(BG_A, 0);
    VDP_setVerticalScroll(BG_A, 0);
    VDP_setTextPlane(BG_A);
    VDP_setTextPalette(PAL0);
    VDP_setTextPriority(TRUE);
    VDP_loadFontData((const u32 *) intro_font, FONT_LENGTH, DMA);
    u16 prev = JOY_readJoypad(JOY_1);
    bool skipped = FALSE;
    const u16 fadeTicks = fps * 2 / 5;

    for (u16 slide = 0; slide < ENDING_SLIDE_COUNT && !skipped; slide++)
    {
        const u16 index = ENDING_shot(campaignFlags, slide);
        const EndingShot *shot = &ENDING_SHOTS[index];
        const u16 duration = (u16) shot->seconds * fps;
        u16 captionIndex = shot->firstCaption;
        const EndingCaption *caption = &ENDING_CAPTIONS[captionIndex];
        u16 captionEnd = (u16) caption->seconds * fps;
        const u16 *palette = (const u16 *)(ending_palettes + index * 64);
        u16 endTick = duration;
        u16 typed = 0, typeClock = 0, lastLevel = 0xFFFF;
        loadShot(index);
        DUST_reset(particles, index, 156);
        for (u16 tick = 0; tick < endTick; tick++)
        {
            if (tick >= captionEnd && captionIndex + 1 < shot->firstCaption + shot->captionCount)
            {
                caption = &ENDING_CAPTIONS[++captionIndex];
                captionEnd += (u16) caption->seconds * fps;
                typed = typeClock = 0;
                VDP_clearTextArea(0, TEXT_TOP, 40, TEXT_ROWS);
            }
            const u16 joy = JOY_readJoypad(JOY_1);
            const u16 pressed = joy & ~prev;
            prev = joy;
            if (pressed & BUTTON_START)
            {
                skipped = TRUE;
                if (endTick > tick + fadeTicks) endTick = tick + fadeTicks;
            }
            typeClock += 36;
            if (typeClock >= fps && typed < caption->letters)
            {
                typeClock -= fps;
                drawText(caption, &typed, typed + 1);
            }
            const u16 edge = (tick < endTick - tick - 1) ? tick : endTick - tick - 1;
            const u16 level = edge < fadeTicks ? edge * FADE_LEVELS / fadeTicks : FADE_LEVELS;
            if (level != lastLevel) { imageBrightness(palette, level); lastLevel = level; }

            DUST_update(particles, PARTICLE_TILE, 156);
            AUDIO_frameBegin();
            MUSIC_update();SFX_update();
            AUDIO_frameEnd();
            SYS_doVBlankProcess();
        }
    }

    // Leave borrowed VRAM blank while flow rebuilds the victory background.
    VDP_setEnable(FALSE);
    VDP_resetSprites();
    VDP_updateSprites(1, DMA_QUEUE);
    SYS_doVBlankProcess();
    VDP_setHorizontalScroll(BG_B, 0);
    VDP_setVerticalScroll(BG_B, 0);
    VDP_setHorizontalScroll(BG_A, 0);
    VDP_setVerticalScroll(BG_A, 0);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    VDP_loadTileData((const u32 *)text_font, TILE_FONT_INDEX, FONT_LENGTH, DMA);
    VDP_setTextPalette(savedTextPalette);
    VDP_setTextPriority(savedPriority);
    PAL_setColors(0, savedPalette, 64, CPU);
    VDP_setEnable(savedEnable);
    // Flow restores fixed tiles before capturing the victory card.
}
