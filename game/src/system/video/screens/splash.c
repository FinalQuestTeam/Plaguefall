// Tela de abertura: logo da desenvolvedora (FinalQuest) recriado com a técnica de
// char-map (system/video/sprites/logo_data.h) em 192x128, redesenhado para leitura
// no Mega Drive. Pintado em faixas de 1 fileira de tiles direto na VRAM,
// mostrado no BG_A centralizado com fade de entrada e saída. Paleta em PAL2; o
// índice 0 é transparente → aparece o fundo preto.

#include "system/video/screens/splash.h"
#include "system/video/sprites/logo_data.h"
#include "system/audio/music.h"
#include "core/game.h"     // fps

#define FADE_FRAMES  (fps / 5)
#define HOLD_FRAMES  fps    // 1 s, PAL e NTSC

// posição em tiles que centraliza a moldura 24x16 na tela de 320x224
#define LOGO_X  ((320 - LOGO_W) / 2 / 8)
#define LOGO_Y  ((224 - LOGO_H) / 2 / 8)

static u16 joyPrev;

// pinta os tiles do logo (fileira a fileira, na VRAM) e desenha o tilemap no BG_A
static void drawLogo(void)
{
    u32 rowBuf[LOGO_TILES_W * 8];       // 1 fileira de tiles (24 tiles = 768 bytes)

    for (u16 ty = 0; ty < LOGO_TILES_H; ty++)
    {
        memset(rowBuf, 0, sizeof(rowBuf));
        for (u16 tx = 0; tx < LOGO_TILES_W; tx++)
        {
            for (u16 py = 0; py < 8; py++)
            {
                const char *row = LOGO_ART[ty * 8 + py];
                for (u16 pxl = 0; pxl < 8; pxl++)
                {
                    const char ch = row[tx * 8 + pxl];
                    if (ch == '0') continue;
                    const u16 col = (ch <= '9') ? (u16) (ch - '0') : (u16) (ch - 'a' + 10);
                    rowBuf[tx * 8 + py] |= (u32) col << ((7 - pxl) * 4);
                }
            }
        }
        VDP_loadTileData(rowBuf, TILE_USER_INDEX + ty * LOGO_TILES_W, LOGO_TILES_W, DMA);
    }

    for (u16 ty = 0; ty < LOGO_TILES_H; ty++)
        for (u16 tx = 0; tx < LOGO_TILES_W; tx++)
            VDP_setTileMapXY(BG_A,
                TILE_ATTR_FULL(PAL2, FALSE, FALSE, FALSE, TILE_USER_INDEX + ty * LOGO_TILES_W + tx),
                LOGO_X + tx, LOGO_Y + ty);
}

static bool skipPressed(void)
{
    const u16 joy = JOY_readJoypad(JOY_1);
    const u16 pressed = joy & ~joyPrev;
    joyPrev = joy;
    return (pressed & BUTTON_START) != 0;
}

static bool pump(u16 n)
{
    while (n--)
    {
        if (skipPressed()) return TRUE;
        SYS_doVBlankProcess();
    }
    return FALSE;
}

static bool pumpFade(void)
{
    while (PAL_isDoingFade())
    {
        if (skipPressed()) return TRUE;
        SYS_doVBlankProcess();
    }
    return FALSE;
}

void SPLASH_run(void)
{
    VDP_setScreenWidth320();
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    PAL_setColor(0, RGB24_TO_VDPCOLOR(0x000000));       // fundo preto (backdrop)
    PAL_setColors(PAL2 * 16, palette_black, 16, CPU);   // PAL2 começa preta

    joyPrev = JOY_readJoypad(JOY_1);

    VDP_setEnable(FALSE);
    drawLogo();
    VDP_setEnable(TRUE);

    PAL_fadeInPalette(PAL2, LOGO_PAL, FADE_FRAMES, TRUE);
    bool skip = pumpFade();

    if (!skip) pump(HOLD_FRAMES);

    PAL_fadeOutPalette(PAL2, FADE_FRAMES, TRUE);
    pumpFade();
    // se o splash foi PULADO, pumpFade retorna sem terminar o fade — garante o
    // término aqui, senão sobra um fade pendente que corrompe a paleta (PAL2) da
    // próxima tela (fundo do título ficava com tiles pretos na 1ª vez)
    while (PAL_isDoingFade()) SYS_doVBlankProcess();

    VDP_clearPlane(BG_A, TRUE);
    PAL_setColors(PAL2 * 16, palette_black, 16, CPU);
}
