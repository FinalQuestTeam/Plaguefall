#include <genesis.h>
#include "audio.h"
#include "music.h"
int main(bool hardReset)
{
    (void)hardReset;
    VDP_drawText("MAIS UM AMANHECER", 11, 12);
    VDP_drawText("START: OUVIR NOVAMENTE", 9, 18);
    MUSIC_init(); MUSIC_playVictory();
    u16 previous = 0;
    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        if ((joy & ~previous) & BUTTON_START) MUSIC_playVictory();
        previous = joy;
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        SYS_doVBlankProcess();
    }
    return 0;
}
