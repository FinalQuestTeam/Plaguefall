// Motor de música PSG com andamento dinâmico — ver music.h.
//
// A música NÃO escreve no PSG direto: a cada quadro ela apenas REQUISITA voz ao
// árbitro (audio.c) com prioridade AUD_PRIO_MUSIC. O SFX requisita com prioridade
// maior nos mesmos canais, então preempta quando ativo e a música retoma o canal
// assim que ele solta. O árbitro é quem escreve o PSG (1x por canal por quadro).

#include "music.h"
#include "song_data.h"
#include "audio.h"

#define CH_MEL   0
#define CH_ARP   1
#define CH_BASS  2
#define CH_DRUM  3

// andamento (frames/passo): configurável em music.h (MUSIC_STEP_CALM / MUSIC_STEP_HOT)

// voz de tom: guarda a freq p/ reaplicar todo quadro (retoma após o SFX soltar).
// O canal ocioso é silenciado pelo próprio árbitro (a voz só deixa de requisitar).
typedef struct { s16 left, gate; u8 vmin; u16 freq; } Voice;
static Voice vMel, vArp, vBass;
static s16 drumLeft, drumGate; static u8 drumVmin, drumType, drumFreq;

static u16 step;                // passo atual (0..SEQ_STEPS-1)
static u16 countdown;           // frames até o próximo passo
static u16 stepFramesCur;       // andamento atual (0 = não inicializado)
static u16 stepFramesTgt;       // andamento alvo (pela ameaça)

// curva de BPM da fase atual (padrão = CONFIG de music.h; MUSIC_setRamp ajusta)
static u8 rCalmUntil = MUSIC_CALM_UNTIL;   // inimigos até ficar calmo
static u8 rEnemyMax  = MUSIC_ENEMY_MAX;    // inimigos p/ BPM máximo
static u8 rStepCalm  = MUSIC_STEP_CALM;    // frames/passo calmo
static u8 rStepHot   = MUSIC_STEP_HOT;     // frames/passo no perigo

// dispara uma nota (freq 0 = sustenta a nota anterior, não recorta)
static void setVoice(Voice *v, u16 freq, s16 gate, u8 vmin)
{
    if (!freq) return;
    v->freq = freq; v->left = v->gate = gate; v->vmin = vmin;
}

// requisita a voz ao árbitro todo quadro (freq + envelope com decaimento).
// Voz ociosa não requisita nada — o árbitro silencia o canal.
static void applyVoice(Voice *v, u8 ch)
{
    if (v->left > 0)
    {
        v->left--;
        const u8 vol = (u8) (v->vmin + ((15 - v->vmin) * (v->gate - v->left)) / v->gate);
        AUDIO_tone(ch, v->freq, vol, AUD_PRIO_MUSIC);
    }
}

static void setDrum(u8 type)
{
    if (!type) return;
    if (type == 1)      { drumType = PSG_NOISE_TYPE_WHITE; drumFreq = PSG_NOISE_FREQ_CLOCK2; drumVmin = 1; drumGate = 6; }
    else if (type == 2) { drumType = PSG_NOISE_TYPE_WHITE; drumFreq = PSG_NOISE_FREQ_CLOCK4; drumVmin = 2; drumGate = 5; }
    else                { drumType = PSG_NOISE_TYPE_WHITE; drumFreq = PSG_NOISE_FREQ_CLOCK8; drumVmin = 7; drumGate = 3; }
    drumLeft = drumGate;                          // só arma a nota; o árbitro escreve o ruído
}

static void applyDrum(void)
{
    // requisita ruído (tipo/freq + envelope) todo quadro enquanto a nota dura; o
    // árbitro só reescreve PSG_setNoise se o tipo/freq mudar (evita reiniciar o
    // gerador de ruído a cada frame = chiado). Ocioso: não requisita.
    if (drumLeft > 0)
    {
        drumLeft--;
        const u8 vol = (u8) (drumVmin + ((15 - drumVmin) * (drumGate - drumLeft)) / drumGate);
        AUDIO_noise(drumType, drumFreq, vol, AUD_PRIO_MUSIC);
    }
}

void MUSIC_init(void)
{
    AUDIO_silenceAll();
    step = 0; countdown = 1;
    stepFramesCur = stepFramesTgt = rStepCalm;
    vMel.left = vArp.left = vBass.left = drumLeft = 0;
}

void MUSIC_start(void) { }       // compat (a música já toca a partir de MUSIC_init)

void MUSIC_setRamp(u8 calmUntil, u8 enemyMax, u8 stepCalm, u8 stepHot)
{
    // 0 em qualquer campo => mantém o padrão do CONFIG (music.h)
    rCalmUntil = calmUntil ? calmUntil : MUSIC_CALM_UNTIL;
    rEnemyMax  = enemyMax  ? enemyMax  : MUSIC_ENEMY_MAX;
    rStepCalm  = stepCalm  ? stepCalm  : MUSIC_STEP_CALM;
    rStepHot   = stepHot   ? stepHot   : MUSIC_STEP_HOT;
    if (rEnemyMax <= rCalmUntil) rEnemyMax = rCalmUntil + 1;  // evita span 0
}

void MUSIC_setEnemies(u8 count)
{
    if (count > rEnemyMax) count = rEnemyMax;
    if (count <= rCalmUntil)                    // poucos inimigos: fica calmo
    {
        stepFramesTgt = rStepCalm;
        return;
    }
    // interpola do calmo (em rCalmUntil) ao quente (em rEnemyMax)
    const u16 span = rEnemyMax - rCalmUntil;
    const u16 k    = count - rCalmUntil;                      // 1..span
    stepFramesTgt  = (u16) (rStepCalm - ((rStepCalm - rStepHot) * k) / span);
}

void MUSIC_update(void)
{
    if (!stepFramesCur) return;                 // ainda não inicializado

    if (--countdown == 0)
    {
        // glide do andamento (1 passo por semicolcheia -> transição suave)
        if (stepFramesCur < stepFramesTgt) stepFramesCur++;
        else if (stepFramesCur > stepFramesTgt) stepFramesCur--;
        countdown = stepFramesCur;

        setVoice(&vMel,  MEL[step],  stepFramesCur * 3, 1);
        setVoice(&vArp,  ARP[step],  stepFramesCur,     7);
        setVoice(&vBass, BASS[step], stepFramesCur * 2, 3);
        setDrum(DRUM[step]);

        if (++step >= SEQ_STEPS) step = 0;
    }

    // escreve nos canais todo quadro (o SFX, chamado depois, tem prioridade)
    applyVoice(&vMel,  CH_MEL);
    applyVoice(&vArp,  CH_ARP);
    applyVoice(&vBass, CH_BASS);
    applyDrum();
}

u16 MUSIC_bpm(void)       { return stepFramesCur ? (900 / stepFramesCur) : 0; }
u8  MUSIC_chord(void)     { return (u8) ((step >> 4) & 3); }
u16 MUSIC_stepInBar(void) { return step & 15; }
