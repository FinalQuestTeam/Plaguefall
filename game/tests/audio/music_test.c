// Compile with the real music.c and audio.c; no copied sequencer logic.
#include <assert.h>
#include <stdio.h>
#include "music.h"
#include "audio.h"

volatile u32 vtimer;
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
        vtimer++; AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
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

static void checkCampaignSelection(void)
{
    MUSIC_selectTrack(MUSIC_TRACK_BAIAO);
    MUSIC_setRamp(1, 6, 8, 4);
    MUSIC_setEnemies(6);
    forward(100);
    MUSIC_selectTrack(MUSIC_TRACK_LADAINHA);
    assert(MUSIC_track() == MUSIC_TRACK_LADAINHA && MUSIC_bpm() == 64);
    forward(37);
    const u16 step = MUSIC_stepInBar();
    MUSIC_selectTrack(255);
    assert(MUSIC_track() == MUSIC_TRACK_LADAINHA && MUSIC_stepInBar() == step);
    MUSIC_previewTrack(MUSIC_TRACK_BREU);
    MUSIC_selectTrack(MUSIC_TRACK_BREU); // selecting the preview must be permanent
    MUSIC_endPreview();
    assert(MUSIC_track() == MUSIC_TRACK_BREU && MUSIC_bpm() == 75);
    MUSIC_setEnemies(15); forward(200);
    assert(MUSIC_bpm() == 112); // old phase's custom ramp did not leak
    MUSIC_selectTrack(MUSIC_TRACK_ENTARDECER);
    assert(MUSIC_bpm() == 90);
    MUSIC_selectTrack(MUSIC_DEFAULT_TRACK);
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
        vtimer++; AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
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

// Compare actual PSG output with an uninterrupted reference at the same video
// timestamps. Dropped game frames must not stretch notes, gates or score tempo.
static uint32_t sampled(unsigned stride, bool duplicate)
{
    static const unsigned elapsedFrames = 2400;
    uint32_t hash = 2166136261u;
    MUSIC_init(); MUSIC_setEnemies(15);
    for (unsigned frame = 1; frame <= elapsedFrames; frame++)
    {
        vtimer++;
        if (stride == 1 || frame % stride == 0)
        {
            AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
            if (duplicate) { AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd(); }
        }
        if (frame % 6 != 0) continue;
        for (unsigned ch = 0; ch < 4; ch++)
        {
            const u16 tone = volumes[ch] == 15 ? 0 : ch < 3 ? frequencies[ch] : noiseType * 4 + noiseFrequency;
            hash = (hash ^ tone) * 16777619u;
            hash = (hash ^ volumes[ch]) * 16777619u;
        }
        hash = (hash ^ MUSIC_stepInBar()) * 16777619u;
    }
    return hash;
}
static void checkDroppedFrames(void)
{
    for (pal = 0; pal < 2; pal++)
        for (u8 track = 0; track < MUSIC_TRACK_COUNT; track++)
        {
            MUSIC_selectTrack(track); MUSIC_setRamp(0,0,0,0);
            vtimer = 100;
            const uint32_t reference = sampled(1, false);
            vtimer = 100; assert(sampled(2, false) == reference);
            vtimer = 100; assert(sampled(3, false) == reference);
            vtimer = 100; assert(sampled(6, false) == reference);
            vtimer = 100; assert(sampled(1, true) == reference);
            vtimer = UINT32_MAX - 20; assert(sampled(3, false) == reference);
        }
}

static void checkVictory(void)
{
    for (pal = 0; pal < 2; pal++)
    {
        const unsigned fps = pal ? 50 : 60;
        MUSIC_init(); forward(37);
        const uint32_t future = forward(100);
        MUSIC_init(); forward(37);
        const u16 savedStep = MUSIC_stepInBar();
        MUSIC_playVictory();
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        assert(MUSIC_victoryActive() && frequencies[0] == 587 && volumes[0] < 15);
        // Every eighth-note onset, including the held high final D.
        static const u16 melody[] = {587, 698, 880, 1175, 1047, 880, 1175, 1175};
        for (unsigned eighth = 1; eighth < 8; eighth++)
        {
            const unsigned before = ((eighth - 1) * fps + 3) / 4;
            const unsigned after = (eighth * fps + 3) / 4;
            forward(after - before);
            assert(frequencies[0] == melody[eighth] && volumes[0] < 15);
        }
        forward(2*fps - (7*fps + 3)/4);
        for (u8 ch = 0; ch < 4; ch++) assert(volumes[ch] == 15);
        forward(4*fps); // no loop and no background bleeding into the result
        for (u8 ch = 0; ch < 4; ch++) assert(volumes[ch] == 15);
        assert(MUSIC_victoryActive() && MUSIC_stepInBar() == savedStep);
        MUSIC_stopVictory(); MUSIC_stopVictory();
        assert(!MUSIC_victoryActive() && forward(100) == future);

        // Early confirmation, same-track selection, and immediate replay.
        MUSIC_playVictory(); forward(fps/2);
        MUSIC_selectTrack(MUSIC_track()); assert(!MUSIC_victoryActive());
        MUSIC_playVictory(); forward(fps/2); MUSIC_playVictory();
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        assert(frequencies[0] == 587);
        MUSIC_init(); assert(!MUSIC_victoryActive());

        // Skipped/duplicate updates, counter wraparound, and a very long load.
        uint32_t reference = 0;
        for (unsigned pass = 0; pass < 4; pass++)
        {
            vtimer = pass == 3 ? UINT32_MAX - 10 : 100;
            MUSIC_playVictory();
            uint32_t hash = 2166136261u;
            for (unsigned frame = 0; frame < 3*fps; frame++)
            {
                vtimer++;
                if (!pass || frame % 3 == 2)
                {
                    AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
                    if (pass == 2) { AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd(); }
                }
                if (frame % 3 == 2)
                    for (u8 ch = 0; ch < 4; ch++)
                    {
                        hash = (hash ^ volumes[ch]) * 16777619u;
                        if (ch < 3 && volumes[ch] < 15) hash = (hash ^ frequencies[ch]) * 16777619u;
                    }
            }
            if (!pass) reference = hash; else assert(hash == reference);
            MUSIC_stopVictory();
        }
        MUSIC_playVictory(); vtimer += 1000000;
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        for (u8 ch = 0; ch < 4; ch++) assert(volumes[ch] == 15);
        MUSIC_stopVictory();
    }
}

static void checkGameOver(void)
{
    for (pal = 0; pal < 2; pal++)
    {
        const unsigned fps = pal ? 50 : 60, ticks = pal ? 12 : 10;
        MUSIC_init(); forward(37);
        const uint32_t future = forward(100);
        MUSIC_init(); forward(37);
        MUSIC_playGameOver();
        assert(MUSIC_gameOverActive() && !MUSIC_victoryActive());
        AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
        assert(frequencies[0] == 587 && volumes[0] < 15);
        static const u16 times[] = {300, 600, 800, 1200, 1600, 1800};
        static const u16 melody[] = {440, 349, 330, 294, 277, 294};
        unsigned previous = 0;
        for (u8 i = 0; i < 6; i++)
        {
            const unsigned frame = (times[i] + ticks - 1) / ticks;
            forward(frame - previous); previous = frame;
            assert(frequencies[0] == melody[i] && volumes[0] < 15);
        }
        forward(4*fps - previous);
        for (u8 ch = 0; ch < 4; ch++) assert(volumes[ch] == 15);
        forward(3*fps);
        for (u8 ch = 0; ch < 4; ch++) assert(volumes[ch] == 15);
        assert(MUSIC_gameOverActive()); // final silence still owns the card
        MUSIC_stopResultCue(); MUSIC_stopResultCue();
        assert(!MUSIC_gameOverActive() && forward(100) == future);

        MUSIC_playGameOver(); forward(fps/2);
        MUSIC_selectTrack(MUSIC_track()); assert(!MUSIC_gameOverActive());
        MUSIC_playGameOver(); forward(fps/2); MUSIC_playVictory();
        assert(MUSIC_victoryActive() && !MUSIC_gameOverActive());
        MUSIC_playGameOver(); assert(!MUSIC_victoryActive());
        MUSIC_init(); assert(!MUSIC_gameOverActive());
    }
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
    vtimer++; AUDIO_frameBegin(); MUSIC_update();
    AUDIO_tone(1, 900, 2, AUD_PRIO_SFX);
    AUDIO_noise(PSG_NOISE_TYPE_WHITE, PSG_NOISE_FREQ_CLOCK4, 1, AUD_PRIO_ALERT);
    AUDIO_frameEnd();
    assert(frequencies[1] == 900 && volumes[1] == 2 && volumes[3] == 1);
    bool resumed = false;
    for (unsigned frame = 0; frame < 50; frame++)
    {
        vtimer++; AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd();
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
        { vtimer++; AUDIO_frameBegin(); MUSIC_update(); AUDIO_frameEnd(); }
    }
    checkPreview();
    checkCampaignSelection();
    checkDroppedFrames();
    checkVictory();
    checkGameOver();
    printf("PASS: 50/60 Hz timing (%u calm / %u hot steps in 10s), loops, envelopes, SFX, four tracks, exact preview restoration, missed/duplicate VBlanks, clock wraparound, victory and game-over cues.\n", calm60, hot60);
    return 0;
}
