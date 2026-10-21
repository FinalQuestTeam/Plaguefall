// Splash de caatinga da tela de titulo (art/title-caatinga-v1). Pintada fileira de
// dados 4bpp ja preparados direto na VRAM, em tela cheia e com
// duas paletas: cada tile aponta para a PAL1 ou a PAL2.
//
// Os 1120 tiles ocupam a região dos inimigos rotacionados / mech / chão; nada
// disso existe no título e tudo é regenerável, então TITLEBG_release() apenas
// devolve o que o jogo precisa antes de a partida começar.

#include "system/video/titlebg.h"
#include "system/video/sprites/menulogo_data.h"
#include "system/video/sprites/finalquest_menu_data.h"

// The compact logo follows the background and ends before the SGDK font.
#define LOGO_BASE (TILE_USER_INDEX + TITLEBG_TILE_BASE + TITLEBG_TILES)
#define FINALQUEST_BASE (LOGO_BASE + MENULOGO_TILES)
// Keep both logos within a conservative 219-tile budget before the font.
#if MENULOGO_TILES + FINALQUEST_MENU_TILES > 219
#error "FinalQuest menu logo overlaps the SGDK font"
#endif
#include "system/video/tilegen.h"       // TILEGEN_palette: devolve a PAL1 aos objetos
#include "system/video/floor.h"         // FLOOR_init: regenera os tiles do chão (PAL3)
#include "system/video/enemygfx.h"      // ENEMYGFX_reset: invalida o cache dos rotacionados

void TITLEBG_load(void)
{
    // não deixa um fade de paleta pendente (ex.: do splash pulado) sobrescrever a
    // PAL1/PAL2 do fundo nos quadros seguintes
    while (PAL_isDoingFade()) SYS_doVBlankProcess();
    SYS_doVBlankProcess();          // sincroniza num quadro limpo + esvazia a fila de DMA

    // carrega com o display DESLIGADO: o DMA completa sem disputar acesso à
    // VRAM com o raster — senão, na 1ª carga (logo após o boot), alguma faixa de
    // tiles vinha truncada (elementos pretos até uma recarga)
    VDP_setEnable(FALSE);

    // The exporter already packs the 4bpp words: no 71680-pixel conversion
    // and no temporary RAM allocation on the transition from the monologue.
    VDP_loadTileData(TITLEBG_PIXELS, TILE_USER_INDEX + TITLEBG_TILE_BASE,
                     TITLEBG_TILES_W * TITLEBG_TILES_H, DMA);

    VDP_loadTileData(MENULOGO_PIXELS, LOGO_BASE, MENULOGO_TILES, DMA);
    PAL_setColors(PAL3 * 16, MENULOGO_PAL, 16, DMA);
    VDP_loadTileData(FINALQUEST_MENU_PIXELS, FINALQUEST_BASE, FINALQUEST_MENU_TILES, DMA);
    // Text keeps white ink 15; the developer credit uses the other PAL0 inks.
    PAL_setColors(PAL0 * 16, FINALQUEST_MENU_PAL, 16, DMA);

    PAL_setColors(PAL1 * 16, TITLEBG_PAL_A, 16, DMA);
    PAL_setColors(PAL2 * 16, TITLEBG_PAL_B, 16, DMA);
    // Pixel 0 dos dois bancos usa o backdrop. A galeria troca essa cor;
    // restaura o preto para a arte nao mudar ao voltar ao menu.
    PAL_setColor(0, RGB24_TO_VDPCOLOR(0x000000));

    VDP_setEnable(TRUE);            // religa o display com a arte já completa na VRAM
}

void TITLEBG_draw(void)
{
    u16 row[TITLEBG_TILES_W];

    for (u16 ty = 0; ty < TITLEBG_TILES_H; ty++)
    {
        const char *pal = TITLEBG_TILE_PAL[ty];
        const u16 base = TILE_USER_INDEX + TITLEBG_TILE_BASE + ty * TITLEBG_TILES_W;

        for (u16 tx = 0; tx < TITLEBG_TILES_W; tx++)
            row[tx] = TILE_ATTR_FULL((pal[tx] == 'a') ? PAL1 : PAL2,
                                     FALSE, FALSE, FALSE, base + tx);

        VDP_setTileMapDataRow(BG_B, row, ty, 0, TITLEBG_TILES_W, CPU);
    }
}

void TITLEBG_drawLogo(void)
{
    for (u16 y = 0; y < MENULOGO_TILES_H; y++)
        for (u16 x = 0; x < MENULOGO_TILES_W; x++)
            VDP_setTileMapXY(BG_A,
                TILE_ATTR_FULL(PAL3, TRUE, FALSE, FALSE, LOGO_BASE + MENULOGO_MAP[y * MENULOGO_TILES_W + x]),
                MENULOGO_X + x, MENULOGO_Y + y);

    for (u16 y = 0; y < FINALQUEST_MENU_TILES_H; y++)
        for (u16 x = 0; x < FINALQUEST_MENU_TILES_W; x++)
            VDP_setTileMapXY(BG_A,
                TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE,
                    FINALQUEST_BASE + FINALQUEST_MENU_MAP[y * FINALQUEST_MENU_TILES_W + x]),
                FINALQUEST_MENU_X + x, FINALQUEST_MENU_Y + y);
}

void TITLEBG_clear(void)
{
    VDP_clearPlane(BG_B, TRUE);
}

void TITLEBG_release(void)
{
    TILEGEN_palette();          // PAL1 volta a ser a paleta dos objetos do jogo
    FLOOR_init();               // tiles + PAL3 do chão (a arte tomou o lugar deles)
    ENEMYGFX_reset();           // rotacionados dos inimigos: regerar na próxima fase
}
