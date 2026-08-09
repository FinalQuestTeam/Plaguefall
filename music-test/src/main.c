// music-test — bancada de teste do motor de música (não mexe em game/).
//
// Toca uma faixa de chiptune ORIGINAL de tom DARK (Ré menor harmônico, cadência
// andaluza Dm-C-Bb-A — vibe de shmup de insetos) e demonstra o BPM DINÂMICO:
// simule a quantidade de inimigos e ouça o andamento subir suavemente, dando
// sensação de perigo. É o mesmo motor (music.c/h) pensado para plugar no jogo.
//
// Controles:  CIMA/BAIXO = + / - inimigos   |   A = modo automático (sobe/desce)
//             START = reiniciar

#include <genesis.h>
#include "music.h"
#include "audio.h"

int main(bool hardReset)
{
    (void) hardReset;

    VDP_setTextPalette(PAL0);
    MUSIC_init();

    VDP_drawText("MUSIC TEST -- TEMA DARK (PSG)", 5, 2);
    VDP_drawText("Re menor / cadencia andaluza", 5, 3);
    VDP_drawText("BPM sobe com a AMEACA:", 5, 5);
    VDP_drawText("CIMA/BAIXO: inimigos   A: auto", 5, 6);
    VDP_drawText("START: reiniciar", 5, 7);

    char buf[36];
    char bar[17];
    u16 prevJoy = 0;
    u8  enemies = 0;
    bool autoMode = FALSE;
    u16 autoT = 0;
    s16 lastStep = -1;
    u16 lastBpm = 0, lastEn = 0xFFFF;

    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        const u16 pressed = joy & ~prevJoy;
        prevJoy = joy;

        if (pressed & BUTTON_START) { MUSIC_init(); enemies = 0; }
        if (pressed & BUTTON_A)     autoMode = !autoMode;

        if (autoMode)
        {
            // sobe até o máximo e desce, em ciclo lento (demonstra o glide)
            autoT++;
            const u16 half = 4 * 60;                       // 4 s subindo, 4 s descendo
            const u16 t = autoT % (2 * half);
            enemies = (u8) ((t < half ? t : (2 * half - t)) * MUSIC_ENEMY_MAX / half);
        }
        else
        {
            if (pressed & BUTTON_UP)   { if (enemies < MUSIC_ENEMY_MAX) enemies++; }
            if (pressed & BUTTON_DOWN) { if (enemies > 0) enemies--; }
        }

        MUSIC_setEnemies(enemies);
        AUDIO_frameBegin();
        MUSIC_update();
        AUDIO_frameEnd();

        // HUD
        if (enemies != lastEn)
        {
            lastEn = enemies;
            sprintf(buf, "INIMIGOS: %2d/%2d %s ", enemies, MUSIC_ENEMY_MAX,
                    autoMode ? "(AUTO)" : "      ");
            VDP_drawText(buf, 5, 10);
            // barra de perigo
            for (u16 i = 0; i < 12; i++) bar[i] = (i < enemies) ? '#' : '-';
            bar[12] = 0;
            VDP_drawText(bar, 5, 11);
        }
        const u16 bpm = MUSIC_bpm();
        if (bpm != lastBpm)
        {
            lastBpm = bpm;
            sprintf(buf, "BPM: %3d ", bpm);
            VDP_drawText(buf, 5, 13);
        }
        const s16 sib = (s16) MUSIC_stepInBar();
        if (sib != lastStep)
        {
            lastStep = sib;
            for (u16 i = 0; i < 16; i++)
                bar[i] = (i == (u16) sib) ? '#' : (((i & 3) == 0) ? '|' : '.');
            bar[16] = 0;
            VDP_drawText(bar, 5, 15);
            static const char *const CH[4] = { "Dm", "C ", "Bb", "A " };
            sprintf(buf, "ACORDE: %s ", CH[MUSIC_chord()]);
            VDP_drawText(buf, 5, 16);
        }

        SYS_doVBlankProcess();
    }
    return 0;
}
