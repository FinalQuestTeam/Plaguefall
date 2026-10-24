// Motor de música PSG com andamento dinâmico — ver music.h.
//
// A música NÃO escreve no PSG direto: a cada quadro ela apenas REQUISITA voz ao
// árbitro (audio.c) com prioridade AUD_PRIO_MUSIC. O SFX requisita com prioridade
// maior nos mesmos canais, então preempta quando ativo e a música retoma o canal
// assim que ele solta. O árbitro é quem escreve o PSG (1x por canal por quadro).

#include "music.h"
#include "audio.h"

#define CH_MEL   0
#define CH_ARP   1
#define CH_BASS  2
#define CH_DRUM  3

// andamento (frames/passo): configurável em music.h (MUSIC_STEP_CALM / MUSIC_STEP_HOT)

// voz de tom: guarda a freq p/ reaplicar todo quadro (retoma após o SFX soltar).
// O canal ocioso é silenciado pelo próprio árbitro (a voz só deixa de requisitar).
// Durations use a 300 Hz clock: a video frame is 5 ticks in NTSC, 6 in PAL.
typedef struct { s16 left, gate; u8 vmin; u16 freq; } Voice;
typedef struct {
    const char *name;
    const u16 *mel;
    const u8 *gate;
    const u16 *arp, *bass;
    const u8 *drum;
    u8 calm, hot;
} MusicScore;
#include "song_catalog_data.h"

typedef struct {
    Voice vMel, vArp, vBass;
    s16 drumLeft, drumGate;
    u8 drumVmin, drumType, drumFreq, frameTicks, heat, track;
    u16 step, stepFramesCur, stepFramesTgt;
    s16 countdown;
    u8 rCalmUntil, rEnemyMax, rStepCalm, rStepHot;
    u8 rampLastCount;bool rampCached;
} MusicState;
static MusicState music = {
    .track = MUSIC_DEFAULT_TRACK,
    .rCalmUntil = MUSIC_CALM_UNTIL, .rEnemyMax = MUSIC_ENEMY_MAX,
    .rStepCalm = MUSIC_STEP_CALM, .rStepHot = MUSIC_STEP_HOT
};
static MusicState savedMusic;
static bool previewing;
static u32 lastVBlank;

typedef struct { u16 at, frequency, length; u8 voice, volume, style; } MusicCueEvent;
#include "victory_data.h"
#include "game_over_data.h"
// 0: campaign loop; 1: victory; 2: game over. Finished cues retain
// ownership (silence) until the result card is dismissed.
static u8 resultCueKind;
static const MusicCueEvent *resultCueScore;
static u16 resultCueCount, resultCueDuration;
static u16 resultCueElapsed, resultCueNext;
static u32 resultCueLastVBlank;
static const MusicCueEvent *resultCueVoices[4];

static void playResultCue(const MusicCueEvent *score, u16 count, u16 duration, u8 kind)
{
    AUDIO_silenceAll();
    resultCueKind = kind;
    resultCueScore = score; resultCueCount = count; resultCueDuration = duration;
    resultCueElapsed = resultCueNext = 0;
    resultCueLastVBlank = vtimer;
    for (u8 ch = 0; ch < 4; ch++) resultCueVoices[ch] = 0;
}

void MUSIC_playVictory(void)
{
    playResultCue(VICTORY_SCORE, VICTORY_EVENT_COUNT, VICTORY_TICKS, 1);
}

void MUSIC_playGameOver(void)
{
    playResultCue(GAME_OVER_SCORE, GAME_OVER_EVENT_COUNT, GAME_OVER_TICKS, 2);
}

void MUSIC_stopResultCue(void)
{
    if (!resultCueKind) return;
    resultCueKind = 0;
    AUDIO_silenceAll();
    MUSIC_syncClock();
}

void MUSIC_stopVictory(void)
{
    if (resultCueKind == 1) MUSIC_stopResultCue();
}

bool MUSIC_victoryActive(void) { return resultCueKind == 1; }
bool MUSIC_gameOverActive(void) { return resultCueKind == 2; }

static void updateResultCue(void)
{
    // Absolute event ages preserve the approved articulation even after a
    // missed frame. Unsigned subtraction also handles VBlank counter wrap.
    const u32 now = vtimer, frames = now - resultCueLastVBlank;
    const u16 frameTicks = SYS_isPAL() ? 12 : 10; // 600 Hz score clock
    resultCueLastVBlank = now;
    if (frames >= (u32)(resultCueDuration - resultCueElapsed + frameTicks - 1) / frameTicks)
        resultCueElapsed = resultCueDuration;
    else resultCueElapsed += frames * frameTicks;
    if (resultCueElapsed >= resultCueDuration) return; // no loop or background restart
    while (resultCueNext < resultCueCount && resultCueScore[resultCueNext].at <= resultCueElapsed)
    {
        const MusicCueEvent *event = &resultCueScore[resultCueNext++];
        resultCueVoices[event->voice] = event;
    }
    for (u8 ch = 0; ch < 4; ch++)
    {
        const MusicCueEvent *event = resultCueVoices[ch];
        if (!event) continue;
        const u16 age = resultCueElapsed - event->at;
        if (age >= event->length) continue;
        const u16 left = event->length - age;
        u16 volume = event->volume;
        if (event->style) volume += (15 - event->volume) * age / event->length;
        else
        {
            const u16 release = event->length / 4;
            if (age == 0) volume++;
            if (release && left < release)
                volume += (15 - event->volume) * (release - left) / release;
        }
        if (volume > 15) volume = 15;
        if (ch < 3) AUDIO_tone(ch, event->frequency, volume, AUD_PRIO_MUSIC);
        else AUDIO_noise(event->frequency == 0 ? PSG_NOISE_TYPE_PERIODIC : PSG_NOISE_TYPE_WHITE,
                         event->frequency == 2 ? PSG_NOISE_FREQ_CLOCK8 : PSG_NOISE_FREQ_CLOCK2,
                         volume, AUD_PRIO_MUSIC);
    }
}

// dispara uma nota (freq 0 = sustenta a nota anterior, não recorta)
static void setVoice(Voice *v, u16 freq, s16 gate, u8 vmin)
{
    if (!freq) return;
    if (gate < 5) gate = 5; // keep envelopes valid even for custom one-frame steps
    v->freq = freq; v->left = v->gate = gate; v->vmin = vmin;
}

// requisita a voz ao árbitro todo quadro (freq + envelope com decaimento).
// Voz ociosa não requisita nada — o árbitro silencia o canal.
static void applyVoice(Voice *v, u8 ch)
{
    if (v->left > 0)
    {
        const u16 age = v->gate - v->left;
        u8 vol;
        u16 freq = v->freq;
        const bool church = music.track == MUSIC_TRACK_LADAINHA;
        const bool organ = church && (ch == CH_BASS || (ch == CH_ARP && v->freq < 700));
        if (ch == CH_MEL || organ)
        {
            // A held reed-like voice, a short release and restrained vibrato.
            // The PSG stays a square wave: this is articulation, not a sample.
            const u16 release = v->gate / 4;
            vol = v->vmin + 2;
            if (v->left <= release)
                vol += (u8) (divu((u32)(12-v->vmin)*(release-v->left),release));
            if (age >= 20 && !church)
            {
                static const s8 vibrato[8] = { 0, 1, 2, 1, 0, -1, -2, -1 };
                static const s8 darkVibrato[8] = { 0, 0, 1, 0, 0, 0, -1, 0 };
                const s8 *wave = music.track == MUSIC_TRACK_BREU ? darkVibrato : vibrato;
                freq = (u16) ((s16) freq + wave[(age / 10) & 7] * (freq >> 8));
            }
        }
        else
        {
            vol = (u8) (v->vmin + divu((u32)(15-v->vmin)*age,(u16)v->gate));
            // A brief downward transient gives the root/fifth bass some body.
            if (ch == CH_BASS && age < 10)
                freq += (u16) (((freq >> 3) * (10 - age)) / 10);
        }
        AUDIO_tone(ch, freq, vol, AUD_PRIO_MUSIC);
    }
}

static void setDrum(u8 type)
{
    if (!type) return;
    if (type == 1)      { music.drumType = PSG_NOISE_TYPE_WHITE; music.drumFreq = PSG_NOISE_FREQ_CLOCK8; music.drumVmin = 5; music.drumGate = 20; }
    else if (type == 2) { music.drumType = PSG_NOISE_TYPE_WHITE; music.drumFreq = PSG_NOISE_FREQ_CLOCK4; music.drumVmin = 6; music.drumGate = 10; }
    else if (type == 3) { music.drumType = PSG_NOISE_TYPE_PERIODIC; music.drumFreq = PSG_NOISE_FREQ_CLOCK2; music.drumVmin = 9; music.drumGate = 10; }
    else                { music.drumType = PSG_NOISE_TYPE_WHITE; music.drumFreq = PSG_NOISE_FREQ_CLOCK2; music.drumVmin = 5; music.drumGate = 20; }
    music.drumLeft = music.drumGate;                          // só arma a nota; o árbitro escreve o ruído
}

static void applyDrum(void)
{
    // requisita ruído (tipo/freq + envelope) todo quadro enquanto a nota dura; o
    // árbitro só reescreve PSG_setNoise se o tipo/freq mudar (evita reiniciar o
    // gerador de ruído a cada frame = chiado). Ocioso: não requisita.
    if (music.drumLeft > 0)
    {
        const u8 vol = (u8) (music.drumVmin + divu((u32)(15-music.drumVmin)*(music.drumGate-music.drumLeft),(u16)music.drumGate));
        AUDIO_noise(music.drumType, music.drumFreq, vol, AUD_PRIO_MUSIC);
    }
}

void MUSIC_syncClock(void) { lastVBlank = vtimer; }

void MUSIC_init(void)
{
    music.rampCached=FALSE;
    MUSIC_stopResultCue();
    MUSIC_syncClock();
    AUDIO_silenceAll();
    music.step = 0; music.countdown = 1;
    music.frameTicks = SYS_isPAL() ? 6 : 5;
    music.heat = 0;
    music.stepFramesCur = music.stepFramesTgt = music.rStepCalm;
    music.vMel.left = music.vArp.left = music.vBass.left = music.drumLeft = 0;
}

void MUSIC_start(void) { }       // compat (a música já toca a partir de MUSIC_init)

void MUSIC_setRamp(u8 calmUntil, u8 enemyMax, u8 stepCalm, u8 stepHot)
{
    music.rampCached=FALSE;
    // 0 em qualquer campo => mantém o padrão do CONFIG (music.h)
    music.rCalmUntil = calmUntil ? calmUntil : MUSIC_CALM_UNTIL;
    music.rEnemyMax  = enemyMax  ? enemyMax  : MUSIC_ENEMY_MAX;
    music.rStepCalm  = stepCalm  ? stepCalm  : MUSIC_SCORES[music.track].calm;
    music.rStepHot   = stepHot   ? stepHot   : MUSIC_SCORES[music.track].hot;
    if (music.rEnemyMax <= music.rCalmUntil) music.rEnemyMax = music.rCalmUntil + 1;  // evita span 0
    if (music.rStepHot > music.rStepCalm) music.rStepHot = music.rStepCalm;
}

void MUSIC_setEnemies(u8 count)
{
    if (count > music.rEnemyMax) count = music.rEnemyMax;
    if(music.rampCached && music.rampLastCount==count)return;
    music.rampLastCount=count;music.rampCached=TRUE;
    if (count <= music.rCalmUntil)                    // poucos inimigos: fica calmo
    {
        music.stepFramesTgt = music.rStepCalm;
        music.heat = 0;
        return;
    }
    // interpola do calmo (em music.rCalmUntil) ao quente (em music.rEnemyMax)
    const u16 span = music.rEnemyMax - music.rCalmUntil;
    const u16 k    = count - music.rCalmUntil;                      // 1..span
    music.stepFramesTgt  = (u16) (music.rStepCalm - ((music.rStepCalm - music.rStepHot) * k) / span);
    music.heat = (u8) ((k * 3) / span);
}

// Advance score/envelopes once per elapsed video frame, including frames the
// game missed. Submit only the final voices to the PSG arbiter, keeping SFX
// priority and avoiding a burst of obsolete notes when the game catches up.
static void tick(void)
{
    if (music.vMel.left > 0) music.vMel.left -= music.frameTicks;
    if (music.vArp.left > 0) music.vArp.left -= music.frameTicks;
    if (music.vBass.left > 0) music.vBass.left -= music.frameTicks;
    if (music.drumLeft > 0) music.drumLeft -= music.frameTicks;
    music.countdown -= music.frameTicks;
    if (music.countdown <= 0)
    {
        // glide do andamento (1 passo por semicolcheia -> transição suave)
        if (music.stepFramesCur < music.stepFramesTgt) music.stepFramesCur++;
        else if (music.stepFramesCur > music.stepFramesTgt) music.stepFramesCur--;
        const u16 ticks = music.stepFramesCur * 5;
        music.countdown += ticks;
        const MusicScore *score = &MUSIC_SCORES[music.track];
        const bool church = music.track == MUSIC_TRACK_LADAINHA;
        setVoice(&music.vMel, score->mel[music.step], ticks * score->gate[music.step] - 5, 2);
        u16 arp = score->arp[music.step];
        if (music.heat && !arp && (music.step & 3) == 2)
            arp = score->arp[music.step + 1]; // extra machine pulses; melody/bass keep the groove
        setVoice(&music.vArp, arp, ticks * (church ? 4 : 1) - 10,
                 church ? (arp >= 700 ? 4 : 6) : music.heat >= 2 ? 7 : 9);
        setVoice(&music.vBass, score->bass[music.step], ticks * (church ? 8 : 1) - 5,
                 church ? 2 : (music.step & 7) == 0 ? 3 : 5);
        setDrum(music.heat >= 2 && (music.step & 7) == 6 ? 4 : score->drum[music.step]);

        if (++music.step >= SEQ_STEPS) music.step = 0;
    }
}

void MUSIC_update(void)
{
    if (resultCueKind) { updateResultCue(); return; }
    const u32 now = vtimer;
    u32 elapsed = now - lastVBlank;
    lastVBlank = now;
    if (!music.stepFramesCur) return;
    while (elapsed--) tick();

    // Re-submit even when called twice in a video frame, without advancing.
    // SFX, called afterwards, retains channel priority.
    applyVoice(&music.vMel,  CH_MEL);
    applyVoice(&music.vArp,  CH_ARP);
    applyVoice(&music.vBass, CH_BASS);
    applyDrum();
}

u16 MUSIC_bpm(void)       { return music.stepFramesCur ? (900 / music.stepFramesCur) : 0; }
u8  MUSIC_chord(void)     { return (u8) ((music.step >> 4) & 3); }
u16 MUSIC_stepInBar(void) { return music.step & (SONG_BAR_STEPS - 1); }

void MUSIC_previewTrack(u8 track)
{
    if (track >= MUSIC_TRACK_COUNT) return;
    if (!previewing) { savedMusic = music; previewing = TRUE; }
    music.track = track;
    MUSIC_setRamp(0, 0, 0, 0);
    MUSIC_init();
}

void MUSIC_endPreview(void)
{
    if (!previewing) return;
    AUDIO_silenceAll();
    music = savedMusic;
    MUSIC_syncClock();
    previewing = FALSE;
}

u8 MUSIC_track(void) { return music.track; }
void MUSIC_selectTrack(u8 track)
{
    if (track >= MUSIC_TRACK_COUNT) return;
    MUSIC_stopResultCue();
    MUSIC_endPreview();
    if (track == music.track) return;
    music.track = track;
    MUSIC_setRamp(0, 0, 0, 0);
    MUSIC_init();
}
const char *MUSIC_trackName(u8 track)
{
    return track < MUSIC_TRACK_COUNT ? MUSIC_SCORES[track].name : "";
}
