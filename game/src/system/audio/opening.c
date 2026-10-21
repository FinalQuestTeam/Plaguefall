// O Sonho Atendido: one continuous PSG score from the Plaguefall logo.
#include "opening.h"
#include "audio.h"

typedef struct {
    u16 at, frequency;
    u8 length, voice, volume, style;
} OpeningEvent;
#include "opening_data.h"

typedef struct {
    u16 frequency, length, left;
    u8 volume, style;
} OpeningVoice;
static OpeningVoice voices[4];
static volatile bool openingActive;
static u16 openingElapsed, nextEvent;
static volatile u16 fadeLeft, fadeTotal;
static u8 frameTicks;

// Only this callback touches the PSG while the opening owns the audio arbiter.
// It never touches the VDP and keeps time while the main loop loads pictures.
static void openingTick(void)
{
    if (!openingActive) return;
    AUDIO_frameBegin();
    if (openingElapsed >= OPENING_DURATION_TICKS)
    {
        AUDIO_frameEnd();
        return;
    }
    while (nextEvent < OPENING_EVENT_COUNT && OPENING_EVENTS[nextEvent].at * OPENING_STEP_TICKS <= openingElapsed)
    {
        const OpeningEvent *event = &OPENING_EVENTS[nextEvent++];
        OpeningVoice *voice = &voices[event->voice];
        voice->frequency = event->frequency;
        voice->length = voice->left = event->length * OPENING_STEP_TICKS;
        voice->volume = event->volume;
        voice->style = event->style;
    }
    for (u8 ch = 0; ch < 4; ch++)
    {
        OpeningVoice *voice = &voices[ch];
        if (!voice->left) continue;
        const u16 age = voice->length - voice->left;
        u16 volume = voice->volume;
        if (ch == 3 || voice->style >= 2) // bell / pluck / metal: decay
            volume += (15 - voice->volume) * age / voice->length;
        else
        {
            // Soft attack and release leave room for the monologue captions.
            const u16 release = voice->length / 4;
            if (age < 20) volume += (20 - age) / 5;
            if (voice->left < release)
                volume += (15 - voice->volume) * (release - voice->left) / release;
        }
        // Start gently on the logo, then hold gain across every image fade.
        if (openingElapsed < 75) volume += (75 - openingElapsed) * 8 / 75;
        if (fadeTotal) volume += (fadeTotal - fadeLeft) * 15 / fadeTotal;
        if (volume > 15) volume = 15;
        if (ch < 3)
            AUDIO_tone(ch, voice->frequency, volume, AUD_PRIO_MUSIC);
        else
            AUDIO_noise(voice->frequency == 0 ? PSG_NOISE_TYPE_PERIODIC : PSG_NOISE_TYPE_WHITE,
                        voice->frequency == 2 ? PSG_NOISE_FREQ_CLOCK8 : PSG_NOISE_FREQ_CLOCK2,
                        volume, AUD_PRIO_MUSIC);
        voice->left = voice->left > frameTicks ? voice->left - frameTicks : 0;
    }
    if (fadeLeft) fadeLeft--;
    openingElapsed += frameTicks;
    AUDIO_frameEnd();
}

void OPENING_start(void)
{
    SYS_disableInts();
    for (u8 i = 0; i < 4; i++) voices[i].left = 0;
    openingElapsed = nextEvent = fadeLeft = fadeTotal = 0;
    frameTicks = SYS_isPAL() ? 6 : 5;
    AUDIO_silenceAll();
    openingActive = TRUE;
    SYS_setVIntCallback(openingTick);
    SYS_enableInts();
}

void OPENING_fadeOut(u16 frames)
{
    SYS_disableInts();
    if (!fadeTotal) fadeTotal = fadeLeft = frames ? frames : 1;
    SYS_enableInts();
}

void OPENING_stop(void)
{
    SYS_disableInts();
    SYS_setVIntCallback(0);
    openingActive = FALSE;
    for (u8 i = 0; i < 4; i++) voices[i].left = 0;
    AUDIO_silenceAll();
    SYS_enableInts();
}
