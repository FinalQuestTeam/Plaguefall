// music-bench — bancada de teste do motor de música (não mexe em game/).
//
// Toca Baiao de Ferrugem: baião e pulsos industriais no PSG.
// Usa o mesmo motor e a mesma partitura do jogo e demonstra o BPM DINÂMICO:
// simule a quantidade de inimigos e ouça o andamento subir suavemente, dando
// sensação de perigo. É o mesmo motor (music.c/h) pensado para plugar no jogo.
//
// Controles:  CIMA/BAIXO = + / - inimigos   |   A = modo automático (sobe/desce)
//             ESQ/DIR = faixa; B = primeira faixa; START = reiniciar

#include <genesis.h>
#include "music.h"
#include "audio.h"

int main(bool hardReset)
{
    (void) hardReset;

    VDP_setTextPalette(PAL0);
    MUSIC_init();

    VDP_drawText("PLAGUEFALL - BAIAO INDUSTRIAL", 5, 2);
    VDP_drawText(MUSIC_trackName(MUSIC_track()), 5, 3);
    VDP_drawText("BPM sobe com a AMEACA:", 5, 5);
    VDP_drawText("CIMA/BAIXO: inimigos   A: auto", 5, 6);
    VDP_drawText("START: reiniciar", 5, 7);
    VDP_drawText("ESQ/DIR: faixa   B: primeira", 5, 8);

    char buf[36];
    char bar[17];
    u16 prevJoy = 0;
    u8  enemies = 0;
    bool autoMode = FALSE;
    u16 autoT = 0;
    const u16 frameRate = SYS_isPAL() ? 50 : 60;
    s16 lastStep = -1;
    u16 lastBpm = 0, lastEn = 0xFFFF;

    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        const u16 pressed = joy & ~prevJoy;
        prevJoy = joy;

        if (pressed & BUTTON_START) { MUSIC_init(); enemies = 0; }
        if (pressed & (BUTTON_LEFT | BUTTON_RIGHT | BUTTON_B))
        {
            const u8 track = (pressed & BUTTON_B) ? MUSIC_TRACK_BAIAO :
                (MUSIC_track() + ((pressed & BUTTON_RIGHT) ? 1 : MUSIC_TRACK_COUNT - 1)) % MUSIC_TRACK_COUNT;
            MUSIC_previewTrack(track);
            VDP_clearTextArea(5, 3, 30, 1);
            VDP_drawText(MUSIC_trackName(track), 5, 3);
            lastStep = -1; lastBpm = 0;
        }
        if (pressed & BUTTON_A)     autoMode = !autoMode;

        if (autoMode)
        {
            // sobe até o máximo e desce, em ciclo lento (demonstra o glide)
            autoT++;
            const u16 half = 4 * frameRate;                       // 4 s subindo, 4 s descendo
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
            for (u16 i = 0; i < 8; i++)
                bar[i] = (i == (u16) sib) ? '#' : (((i & 3) == 0) ? '|' : '.');
            bar[8] = 0;
            VDP_drawText(bar, 5, 15);
            static const char *const CH[MUSIC_TRACK_COUNT][4] = {
                { "D7", "C ", "G ", "D7" }, { "Dm", "C ", "G ", "Am" },
                { "Dm", "Eb", "Bb", "A7" }, { "Dm", "Bb", "Gm", "A7" }
            };
            sprintf(buf, "ACORDE: %s ", CH[MUSIC_track()][MUSIC_chord()]);
            VDP_drawText(buf, 5, 16);
        }

        SYS_doVBlankProcess();
    }
    return 0;
}
