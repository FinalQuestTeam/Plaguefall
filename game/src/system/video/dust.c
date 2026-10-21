// Shared subpixel dust, embers and soot for the title and monologue.
#include "system/video/dust.h"
#include "core/game.h"
static const u32 ART[24] = {
    0, 0, 0, 0x00010000, 0, 0, 0, 0,
    0, 0, 0, 0x00020000, 0x00020000, 0, 0, 0,
    0, 0, 0, 0x00033000, 0, 0, 0, 0
};
static const u16 COLORS[3] = { 0x246, 0x06E, 0x222 };
void DUST_load(u16 tile) { VDP_loadTileData(ART, tile, 3, DMA); }
void DUST_reset(DustParticle *particles, u16 seed, u16 height)
{
    for (u16 i = 0; i < DUST_COUNT; i++)
    {
        particles[i].x = (s32) ((i * 53 + seed * 17) % 320) << 8;
        particles[i].y = (s32) ((i * 37 + seed * 11) % height) << 8;
        particles[i].vx = ((s16) (16 + i % 5 * 3) * 256) / fps;
        particles[i].vy = ((s16) (i % 3 == 1 ? -32 : -18 - i % 4 * 2) * 256) / fps;
    }
}
void DUST_update(DustParticle *particles, u16 tile, u16 height)
{
    for (u16 i = 0; i < DUST_COUNT; i++)
    {
        DustParticle *p = &particles[i];
        p->x += p->vx; p->y += p->vy;
        if (p->x >= (320L << 8)) p->x -= 320L << 8;
        if (p->y < 0) p->y += (s32) height << 8;
        VDP_setSpriteFull(i, (s16) (p->x >> 8), (s16) (p->y >> 8), SPRITE_SIZE(1, 1),
            TILE_ATTR_FULL(PAL3, FALSE, FALSE, FALSE, tile + i % 3), i + 1);
    }
    VDP_setSpriteLink(DUST_COUNT - 1, 0);
    VDP_updateSprites(DUST_COUNT, DMA_QUEUE);
}
void DUST_brightness(u16 level)
{
    u16 colors[3];
    for (u16 i = 0; i < 3; i++)
    {
        const u16 word = COLORS[i];
        colors[i] = (((((word >> 1) & 7) * level + 16) / 32) << 1) |
                    (((((word >> 5) & 7) * level + 16) / 32) << 5) |
                    (((((word >> 9) & 7) * level + 16) / 32) << 9);
    }
    PAL_setColors(PAL3 * 16 + 1, colors, 3, CPU);
}
