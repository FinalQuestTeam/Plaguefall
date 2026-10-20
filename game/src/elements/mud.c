// Lama: área que reduz a velocidade progressivamente enquanto se pisa nela.
// Jogador: -30% ao entrar, -10% por segundo, até -70%.
// Inimigos: -3% ao entrar, -3% por segundo, até -30%.

#include "elements/mud.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "system/audio/sfx.h"
#include "enemies/enemies.h"

static u16 playerMudTime;   // frames seguidos do jogador na lama

void MUD_buildTile(u32 *tileBuf)
{
    // marrom com torrões mais escuros
    for (u16 y = 0; y < 8; y++)
    {
        for (u16 x = 0; x < 8; x++)
        {
            u16 c = (((x * 5 + y * 3 + (x >> 1)) & 7) < 2) ? 10 : 9;
            tileBuf[TILE_MUD * 8 + y] |= (u32) c << ((7 - x) * 4);
        }
    }
}

void MUD_draw(const TileRect *rects, u16 count)
{
    const u16 attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_USER_INDEX + TILE_MUD);
    for (u16 i = 0; i < count; i++)
        VDP_fillTileMapRect(BG_A, attr, rects[i].x, rects[i].y, rects[i].w, rects[i].h);
}

static bool isOn(const TileRect *rects, u16 count, s16 cx, s16 cy)
{
    for (u16 i = 0; i < count; i++)
    {
        const s16 x = rects[i].x * 8, y = rects[i].y * 8;
        const s16 w = rects[i].w * 8, h = rects[i].h * 8;
        if ((cx >= x) && (cx < x + w) && (cy >= y) && (cy < y + h)) return TRUE;
    }
    return FALSE;
}

// lentidão em %: BASE% imediato ao entrar, +STEP% a cada segundo, teto MAX%
static u16 slowFromTime(u16 time, u16 base, u16 step, u16 max)
{
    u16 slow = base + step * divu(time, fps);
    return (slow > max) ? max : slow;
}

void MUD_reset(void)
{
    playerMudTime = 0;
    playerSlowPct = 0;
}

void MUD_update(const TileRect *rects, u16 count)
{
    // jogador (centro do 16x16)
    if (isOn(rects, count, px + 8, py + 8))
    {
        SFX_ambient(SFX_AMB_MUD);       // som de passos na lama

        playerSlowPct = slowFromTime(playerMudTime, MUD_PLAYER_BASE, MUD_PLAYER_STEP, MUD_PLAYER_MAX);
        if (playerMudTime < 0xFFFF) playerMudTime++;
    }
    else MUD_reset();

    // inimigos (centro conforme o tamanho)
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;

        const s16 half = ENEMY_SIZE(e) / 2;
        if (isOn(rects, count, e->x + half, e->y + half))
        {
            e->slowPct = slowFromTime(e->mudTime, MUD_ENEMY_BASE, MUD_ENEMY_STEP, MUD_ENEMY_MAX);
            if (e->mudTime < 0xFFFF) e->mudTime++;
        }
        else
        {
            e->mudTime = 0;
            e->slowPct = 0;
        }
    }
}
