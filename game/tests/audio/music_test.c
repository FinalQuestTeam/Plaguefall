// Compile with the real music.c and audio.c; no copied sequencer logic.
#include <assert.h>
#include <stdio.h>
#include "music.h"
#include "audio.h"

static u16 pal, frequencies[3], volumes[4], noiseType, noiseFrequency;
static unsigned toneWrites, noiseWrites;
u16 SYS_isPAL(void) { return pal; }
void PSG_setFrequency(u16 ch, u16 frequency)
{
    assert(ch < 3 && frequency >= 109 && frequency < 4000);
    frequencies[ch] = frequency;
    toneWrites++;
}
void PSG_setEnvelope(u16 ch, u16 volume)
{
    assert(ch < 4 && volume <= 15);
    volumes[ch] = volume;
}
void PSG_setNoise(u16 type, u16 frequency)
{
    assert(type <= 1 && frequency <= 2);
    noiseType = type;
    noiseFrequency = frequency;
    noiseWrites++;
}

static uint32_t forward(unsigned frames)
{
    uint32_t hash = 2166136261u;
    for (unsigned frame = 0; frame < frames; frame++)
    {
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        for (unsigned ch = 0; ch < 4; ch++)
        {
            const u16 tone = volumes[ch] == 15 ? 0 : ch < 3 ? frequencies[ch] : (noiseType * 4 + noiseFrequency);
            hash = (hash ^ tone) * 16777619u;
            hash = (hash ^ volumes[ch]) * 16777619u;
        }
    }
    return hash;
}

static void prepareReference(void)
{
    pal = 0;
    MUSIC_endPreview();
    MUSIC_setRamp(1, 6, 8, 4);
    MUSIC_init();
    MUSIC_setEnemies(6);
    forward(37);
}

static void checkPreview(void)
{
    prepareReference();
    const uint32_t expected = forward(96);
    prepareReference();
    const u8 track = MUSIC_track();
    const u16 step = MUSIC_stepInBar(), bpm = MUSIC_bpm();
    MUSIC_previewTrack(255);
    assert(MUSIC_track() == track && MUSIC_stepInBar() == step && MUSIC_bpm() == bpm);
    assert(MUSIC_trackName(255)[0] == 0);
    uint32_t signatures[MUSIC_TRACK_COUNT];
    static const u16 calm[MUSIC_TRACK_COUNT] = { 100, 90, 75, 64 };
    static const u16 hot[MUSIC_TRACK_COUNT] = { 150, 128, 112, 90 };
    for (u8 i = 0; i < MUSIC_TRACK_COUNT; i++)
    {
        MUSIC_previewTrack(i);
        assert(MUSIC_track() == i && MUSIC_stepInBar() == 0);
        assert(MUSIC_bpm() == calm[i] && MUSIC_trackName(i)[0]);
        signatures[i] = forward(2000); // at least a full loop of every score
        MUSIC_setEnemies(15);
        forward(200);
        assert(MUSIC_bpm() == hot[i]);
    }
    for (u8 i = 0; i < MUSIC_TRACK_COUNT; i++)
        for (u8 j = i + 1; j < MUSIC_TRACK_COUNT; j++) assert(signatures[i] != signatures[j]);
    MUSIC_endPreview();
    assert(MUSIC_track() == track && MUSIC_stepInBar() == step && MUSIC_bpm() == bpm);
    assert(forward(96) == expected); // exact future tones/envelopes, not only track ID
    MUSIC_endPreview(); // safe to call again after leaving a character tab
    MUSIC_setEnemies(2);
    forward(120);
    assert(MUSIC_bpm() == 112); // the original custom phase ramp was restored too
}

static unsigned run(u16 region, u8 enemies)
{
    pal = region;
    MUSIC_setRamp(0, 0, 0, 0);
    MUSIC_init();
    MUSIC_setEnemies(enemies);
    unsigned steps = 0;
    u16 previous = MUSIC_stepInBar();
    for (unsigned frame = 0; frame < (pal ? 500u : 600u); frame++)
    {
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        u16 current = MUSIC_stepInBar();
        assert(current < 8);
        if (current != previous)
        {
            assert(current == (previous + 1) % 8);
            previous = current;
            steps++;
        }
    }
    assert(MUSIC_bpm() == 900 / (enemies ? MUSIC_STEP_HOT : MUSIC_STEP_CALM));
    return steps;
}

int main(void)
{
    unsigned calm60 = run(0, 0), calm50 = run(1, 0);
    unsigned hot60 = run(0, 15), hot50 = run(1, 15);
#ifdef MUSIC_DARK
    assert(calm60 == 50 && hot60 == 75);
#elif defined(MUSIC_MELANCHOLIC)
    assert(calm60 == 60 && hot60 == 86);
#else
    assert(calm60 == 67 && hot60 == 100);
#endif
    assert(calm50 == calm60);
    assert(hot60 == hot50 && hot60 >= calm60 + 25);
    assert(toneWrites > 100 && noiseWrites > 100);

    // The same channels remain available to combat, then music resumes.
    AUDIO_frameBegin(); MUSIC_update();
    AUDIO_tone(1, 900, 2, AUD_PRIO_SFX);
    AUDIO_noise(PSG_NOISE_TYPE_WHITE, PSG_NOISE_FREQ_CLOCK4, 1, AUD_PRIO_ALERT);
    AUDIO_frameEnd();
    assert(frequencies[1] == 900 && volumes[1] == 2 && volumes[3] == 1);
    bool resumed = false;
    for (unsigned frame = 0; frame < 50; frame++)
    {
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        if (volumes[1] < 15 && frequencies[1] != 900) resumed = true;
    }
    assert(resumed);
    AUDIO_silenceAll();
    for (unsigned ch = 0; ch < 4; ch++) assert(volumes[ch] == 15);

    // Run many full loops and custom extreme ramps under sanitizers.
    for (unsigned pass = 0; pass < 3; pass++)
    {
        MUSIC_setRamp(1, 1, pass == 0 ? 1 : 9, pass == 1 ? 20 : 1);
        MUSIC_init();
        MUSIC_setEnemies(255);
        for (unsigned frame = 0; frame < 4000; frame++)
        { AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd(); }
    }
    checkPreview();
    printf("PASS: 50/60 Hz timing (%u calm / %u hot steps in 10s), loops, envelopes, SFX, all four runtime tracks and exact preview restoration.\n", calm60, hot60);
    return 0;
}
