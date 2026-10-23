// Exercise the real opening score and PSG arbiter, in both video regions.
#include <assert.h>
#include <stdio.h>
#include "opening.h"
#include "music.h"
#include "audio.h"

volatile u32 vtimer;
static u16 pal, frequencies[3], volumes[4], noiseType, noiseFrequency;
static unsigned writes, lockDepth;
static VoidCallback *vint;
void SYS_disableInts(void) { lockDepth++; }
void SYS_enableInts(void) { assert(lockDepth); lockDepth--; }
void SYS_setVIntCallback(VoidCallback *callback) { assert(lockDepth); vint = callback; }
u16 SYS_isPAL(void) { return pal; }
void PSG_setFrequency(u16 ch, u16 freq)
{
    assert(ch < 3 && freq >= 109 && freq < 4000);
    frequencies[ch] = freq;
    writes++;
}
void PSG_setEnvelope(u16 ch, u16 volume)
{
    assert(ch < 4 && volume <= 15);
    volumes[ch] = volume;
}
void PSG_setNoise(u16 type, u16 freq)
{
    assert(type <= 1 && freq <= 2);
    noiseType = type; noiseFrequency = freq;
}

static bool audible(void)
{
    for (u8 ch = 0; ch < 4; ch++) if (volumes[ch] < 15) return true;
    return false;
}

static uint32_t forward(unsigned frames, bool opening)
{
    uint32_t hash = 2166136261u;
    for (unsigned i = 0; i < frames; i++)
    {
        vtimer++;
        if (opening) { if (vint) vint(); }
        else { AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd(); }
        for (u8 ch = 0; ch < 4; ch++)
        {
            const u16 tone = volumes[ch] == 15 ? 0 : ch < 3 ? frequencies[ch] : noiseType*4+noiseFrequency;
            hash = (hash ^ tone) * 16777619u;
            hash = (hash ^ volumes[ch]) * 16777619u;
        }
    }
    return hash;
}

int main(void)
{
    for (pal = 0; pal < 2; pal++)
    {
        const unsigned fps = pal ? 50 : 60;
        OPENING_start();
        assert(vint && !lockDepth);
        uint32_t signature = 2166136261u;
        unsigned silent = 0, longest = 0;
        // No main-loop music calls or scene resets, including all load times.
        for (unsigned frame = 0; frame < 106*fps; frame++)
        {
            signature = (signature ^ forward(1,true)) * 16777619u;
            if (audible()) silent=0; else silent++;
            if (silent>longest) longest=silent;
        }
        assert(longest < fps/3);
        forward(4*fps,true); assert(!audible()); // score ends without looping
        OPENING_stop(); assert(!vint && !audible() && !lockDepth);
        OPENING_start();
        uint32_t repeated = 2166136261u;
        for (unsigned frame = 0; frame < 106*fps; frame++)
            repeated = (repeated ^ forward(1,true)) * 16777619u;
        assert(repeated == signature);
        OPENING_stop();

        // START's fade is the only gain fade after the initial logo entrance.
        OPENING_start(); forward(8*fps,true);
        OPENING_fadeOut(fps/2);
        for (unsigned frame=0;frame<fps;frame++)
        {
            OPENING_fadeOut(fps/2); // repeated requests must not restart it
            forward(1,true);
        }
        assert(!audible()); OPENING_stop();
        // Safely ending before or after an active score leaves no callback.
        OPENING_stop(); assert(!vint);

        MUSIC_setRamp(1,6,8,4); MUSIC_init(); MUSIC_setEnemies(6);
        forward(37,false);
        const uint32_t expected=forward(100,false);
        MUSIC_setRamp(1,6,8,4); MUSIC_init(); MUSIC_setEnemies(6);
        forward(37,false);
        OPENING_start(); forward(fps,true); OPENING_stop();
        assert(forward(100,false)==expected);
        printf("%u Hz: continuous 106s, longest musical rest %u frames.\n",fps,longest);
    }
    assert(writes>100);
    puts("PASS: continuous logo-to-intro score, independent VInt clock, no scene fades/restarts, START fade, callback teardown and untouched gameplay music.");
    return 0;
}
