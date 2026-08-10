// Vitrine dos personagens: o mech selecionado desenhado nas 8 direções, em volta
// de uma bússola (dir 0 = cima, horário). ESQ/DIR troca de personagem, A/B/START sai.

#include "system/video/screens/chardemo.h"
#include "system/video/chars.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "core/game.h"     // fps

// posição (canto sup. esq. do sprite 32x32) de cada direção, ao redor do centro
// (160,112) num raio ~70 px — mesma ordem das direções (0=cima, horário)
static const struct { s16 x, y; } COMPASS[8] =
{
    { 144,  26 },   // 0 cima
    { 193,  47 },   // 1 cima-direita
    { 214,  96 },   // 2 direita
    { 193, 145 },   // 3 baixo-direita
    { 144, 166 },   // 4 baixo
    {  95, 145 },   // 5 baixo-esquerda
    {  74,  96 },   // 6 esquerda
    {  95,  47 },   // 7 cima-esquerda
};

static void drawLabels(u8 which)
{
    VDP_clearTextArea(0, 13, 40, 1);        // limpa a linha do nome (centro)
    const char *name = CHARS_NAME[which];
    u16 len = 0; while (name[len]) len++;
    VDP_drawText(name, (40 - len) / 2, 13);

    char buf[8];
    sprintf(buf, "%d/%d", which + 1, CHARS_COUNT);
    VDP_drawText(buf, 19, 15);
}

void CHARDEMO_run(void)
{
    VDP_setScreenWidth320();
    VDP_setTextPlane(BG_A);
    VDP_setTextPalette(PAL0);
    VDP_clearPlane(BG_A, TRUE);
    PAL_setColor(0, RGB24_TO_VDPCOLOR(0x101018));   // fundo azul bem escuro

    VDP_drawText("PERSONAGENS - 8 DIRECOES", 8, 0);
    VDP_drawText("ESQ/DIR: TROCAR   B: SAIR", 8, 26);

    u8 which = 0;
    CHARS_load(which);
    drawLabels(which);

    u16 prev = JOY_readJoypad(JOY_1);

    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        const u16 pressed = joy & ~prev;
        prev = joy;

        AUDIO_frameBegin();
        MUSIC_update();
        AUDIO_frameEnd();

        if (pressed & BUTTON_RIGHT) { which = (which + 1) % CHARS_COUNT;              CHARS_load(which); drawLabels(which); }
        if (pressed & BUTTON_LEFT)  { which = (which + CHARS_COUNT - 1) % CHARS_COUNT; CHARS_load(which); drawLabels(which); }
        if (pressed & (BUTTON_A | BUTTON_B | BUTTON_START)) break;

        // os 8 sprites (uma direção em cada ponto da bússola)
        u16 n = 0;
        for (u8 d = 0; d < 8; d++)
        {
            VDP_setSpriteFull(n, COMPASS[d].x, COMPASS[d].y, SPRITE_SIZE(4, 4),
                TILE_ATTR_FULL(PAL2, TRUE, CHARS_dirFlipV(d), CHARS_dirFlipH(d),
                    TILE_USER_INDEX + CHARS_dirTile(d)), n + 1);
            n++;
        }
        VDP_setSpriteLink(n - 1, 0);
        VDP_updateSprites(n, DMA_QUEUE);

        SYS_doVBlankProcess();
    }

    VDP_resetSprites();
    VDP_updateSprites(1, DMA_QUEUE);
    VDP_clearPlane(BG_A, TRUE);
}
