// Efeitos sonoros. Não escrevem no PSG direto: cada evento arma um timer e o
// SFX_update() REQUISITA voz ao árbitro (audio.c) todo quadro, com prioridade
// acima da música (SFX/ALERT). O ambiente do terreno é um leito de RUÍDO de
// prioridade mínima no canal 3 (a bateria e o combate passam por cima dele), o
// que libera o canal 0 (melodia) — antes o crepitar era um tom aleatório ali.

#include "system/audio/sfx.h"
#include "system/audio/audio.h"
#include "core/game.h"

static u16 sfxShot;
static u16 sfxNoise;
static u16 sfxPick;
static u16 sfxBoom;
static u16 sfxHurt;
static u8 sfxRadio,sfxCount;
static bool countGo;

static u8  ambientKind;     // som ambiente atual (leito de ruído, canal 3)
static u16 ambientPhase;    // fase do padrão ambiente (passos da lama)

void SFX_playerShot(void) { sfxShot = 10; }     // canal 1 (arpejo cede)
void SFX_enemyShot(void)  { sfxNoise = 8; }     // canal 3 (ruído)

// contrato de game.h (chamado pelos itens na coleta)
void sfxItemPickup(void)  { sfxPick = 8; }      // canal 2 (baixo cede)

// dano SOFRIDO pelo jogador (contato/projétil de inimigo): tom grave descendente,
// bem distinto do "blip" agudo da coleta. O dano da lava fica só com o crepitar
// ambiente (updateAmbient) — quem chama é damagePlayer, nunca loseHp.
void SFX_playerHit(void)  { sfxHurt = 14; }     // canal 2, prioridade ALERT

void SFX_bombBlast(void)  { sfxBoom = 30; }     // canal 3, prioridade ALERT

void SFX_ambient(u8 kind) { ambientKind = kind; }

void SFX_radioTick(void){if(!sfxRadio)sfxRadio=2;}
void SFX_countPulse(bool go){sfxCount=go ? 8 : 4;countGo=go;}

void SFX_silence(void)
{
    sfxRadio=sfxCount=0;
    sfxShot = 0;
    sfxNoise = 0;
    sfxPick = 0;
    sfxBoom = 0;
    sfxHurt = 0;
    ambientKind = SFX_AMB_NONE;
    ambientPhase = 0;
    AUDIO_silenceAll();
}

// leito de ruído (canal 3) do terreno sob o jogador — prioridade mínima
static void updateAmbient(void)
{
    if (ambientKind == SFX_AMB_LAVA)
    {
        // crepitar: ruído grave e trêmulo, presente mas sem virar hiss (crackle)
        AUDIO_noise(PSG_NOISE_TYPE_WHITE, PSG_NOISE_FREQ_CLOCK8,
                    (u8) (3 + (random() & 3)), AUD_PRIO_AMBIENT);
        ambientPhase = 0;
    }
    else if (ambientKind == SFX_AMB_MUD)
    {
        // passo: "squelch" curto de ruído a cada ~1/3 s, silêncio entre eles
        const u16 period = fps / 3;
        const u16 t = ambientPhase % period;
        if (t < 5)
            AUDIO_noise(PSG_NOISE_TYPE_WHITE, PSG_NOISE_FREQ_CLOCK8,
                        (u8) (2 + t), AUD_PRIO_AMBIENT);
        ambientPhase++;
    }
    // SFX_AMB_NONE: não requisita nada (o árbitro mantém o canal livre p/ a música)
}

void SFX_update(void)
{
    if (sfxShot)
    {
        sfxShot--;                          // pitch cai e volume decai até silenciar
        if (sfxShot) AUDIO_tone(1, 500 + sfxShot * 90, (u8) (12 - sfxShot), AUD_PRIO_SFX);
    }
    if (sfxBoom)
    {
        // explosão: mais longa e mais alta, tem prioridade sobre o tiro inimigo
        sfxBoom--;
        sfxNoise = 0;
        if (sfxBoom) AUDIO_noise(PSG_NOISE_TYPE_WHITE, PSG_NOISE_FREQ_CLOCK2,
                                 (u8) (15 - (sfxBoom >> 1)), AUD_PRIO_ALERT);
    }
    else if (sfxNoise)
    {
        sfxNoise--;
        if (sfxNoise) AUDIO_noise(PSG_NOISE_TYPE_WHITE, PSG_NOISE_FREQ_CLOCK4,
                                  (u8) (12 - sfxNoise), AUD_PRIO_SFX);
    }
    if (sfxHurt)
    {
        // dor: pitch grave caindo; tem prioridade sobre a coleta (mesmo canal 2)
        sfxHurt--;
        sfxPick = 0;
        if (sfxHurt) AUDIO_tone(2, 110 + sfxHurt * 14, (u8) (15 - sfxHurt), AUD_PRIO_ALERT);
    }
    else if (sfxPick)
    {
        sfxPick--;                          // pitch sobe: "blip" de recompensa
        if (sfxPick) AUDIO_tone(2, 1400 - sfxPick * 100, (u8) (11 - sfxPick), AUD_PRIO_SFX);
    }

    if(sfxRadio){sfxRadio--;AUDIO_tone(2,920+sfxRadio*80,11,AUD_PRIO_SFX);}
    if(sfxCount){sfxCount--;AUDIO_tone(2,countGo ? 880 : 440,7+sfxCount/2,AUD_PRIO_SFX);}
    updateAmbient();
}
