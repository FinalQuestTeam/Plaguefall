// Splash de caatinga da tela de titulo (art/title-caatinga-v1). Pintada fileira de
// tiles a fileira direto na VRAM, como o splash — só que em tela cheia e com
// duas paletas: cada tile aponta para a PAL1 ou a PAL2.
//
// Os 1120 tiles ocupam a região dos inimigos rotacionados / mech / chão; nada
// disso existe no título e tudo é regenerável, então TITLEBG_release() apenas
// devolve o que o jogo precisa antes de a partida começar.

#include "system/video/titlebg.h"
#include "system/video/tilegen.h"       // TILEGEN_palette: devolve a PAL1 aos objetos
#include "system/video/floor.h"         // FLOOR_init: regenera os tiles do chão (PAL3)
#include "system/video/enemygfx.h"      // ENEMYGFX_reset: invalida o cache dos rotacionados

void TITLEBG_load(void)
{
    // não deixa um fade de paleta pendente (ex.: do splash pulado) sobrescrever a
    // PAL1/PAL2 do fundo nos quadros seguintes
    while (PAL_isDoingFade()) SYS_doVBlankProcess();
    SYS_doVBlankProcess();          // sincroniza num quadro limpo + esvazia a fila de DMA

    u32 *buf = MEM_alloc(TITLEBG_TILES_W * 8 * (u16) sizeof(u32));  // 1 fileira de tiles

    // carrega com o display DESLIGADO: as ~28 DMAs completam sem disputar acesso à
    // VRAM com o raster — senão, na 1ª carga (logo após o boot), alguma faixa de
    // tiles vinha truncada (elementos pretos até uma recarga)
    VDP_setEnable(FALSE);

    for (u16 ty = 0; ty < TITLEBG_TILES_H; ty++)
    {
        // a arte é densa (sem transparência): monta a palavra de 8 pixels de uma
        // vez, varrendo a linha em sequência — sem máscara nem limpeza do buffer
        for (u16 py = 0; py < 8; py++)
        {
            const char *px = TITLEBG_ART[ty * 8 + py];
            for (u16 tx = 0; tx < TITLEBG_TILES_W; tx++)
            {
                u32 w = 0;
                for (u16 i = 0; i < 8; i++)
                {
                    const char ch = *px++;
                    w = (w << 4) | ((ch <= '9') ? (u32) (ch - '0') : (u32) (ch - 'a' + 10));
                }
                buf[tx * 8 + py] = w;
            }
        }
        VDP_loadTileData(buf, TILE_USER_INDEX + TITLEBG_TILE_BASE + ty * TITLEBG_TILES_W,
                         TITLEBG_TILES_W, DMA);
    }

    MEM_free(buf);

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
