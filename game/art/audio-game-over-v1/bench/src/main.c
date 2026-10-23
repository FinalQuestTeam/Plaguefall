// Isolated audition ROM. START replays the original four-second game-over audition.
#include <genesis.h>
#include "audio.h"

typedef struct { u16 at, frequency, length; u8 voice, volume, style; } Event;
#include "score.h"
typedef struct { u16 frequency, length, left; u8 volume, style; } Voice;
static Voice voices[4];

int main(bool hardReset)
{
    (void)hardReset;
    VDP_drawText("PLAGUEFALL", 14, 9);
    VDP_drawText("CINZA E SILENCIO", 11, 12);
    VDP_drawText("GAME OVER - 90 BPM - 4 SEGUNDOS", 5, 14);
    VDP_drawText("START: OUVIR NOVAMENTE", 9, 18);
    AUDIO_silenceAll();
    u16 elapsed = 0, next = 0, previous = 0;
    const u16 frameTicks = SYS_isPAL() ? 12 : 10;
    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        if ((joy & ~previous) & BUTTON_START)
        {
            elapsed = next = 0;
            for (u16 ch = 0; ch < 4; ch++) voices[ch].left = 0;
            AUDIO_silenceAll();
        }
        previous = joy;
        AUDIO_frameBegin();
        while (next < EVENT_COUNT && SCORE[next].at <= elapsed && elapsed < SCORE_TICKS)
        {
            const Event *event = &SCORE[next++];
            Voice *voice = &voices[event->voice];
            voice->frequency = event->frequency;
            voice->length = voice->left = event->length;
            voice->volume = event->volume;
            voice->style = event->style;
        }
        for (u16 ch = 0; ch < 4; ch++)
        {
            Voice *voice = &voices[ch];
            if (!voice->left || elapsed >= SCORE_TICKS) continue;
            const u16 age = voice->length - voice->left;
            u16 volume = voice->volume;
            if (voice->style)
                volume += (15 - voice->volume) * age / voice->length;
            else
            {
                const u16 release = voice->length / 4;
                if (age == 0) volume++;
                if (voice->left < release)
                    volume += (15 - voice->volume) * (release - voice->left) / release;
            }
            if (volume > 15) volume = 15;
            if (ch < 3) AUDIO_tone(ch, voice->frequency, volume, AUD_PRIO_MUSIC);
            else AUDIO_noise(voice->frequency == 0 ? PSG_NOISE_TYPE_PERIODIC : PSG_NOISE_TYPE_WHITE,
                             voice->frequency == 2 ? PSG_NOISE_FREQ_CLOCK8 : PSG_NOISE_FREQ_CLOCK2,
                             volume, AUD_PRIO_MUSIC);
            voice->left = voice->left > frameTicks ? voice->left - frameTicks : 0;
        }
        if (elapsed < SCORE_TICKS) elapsed += frameTicks;
        AUDIO_frameEnd();
        SYS_doVBlankProcess();
    }
    return 0;
}
