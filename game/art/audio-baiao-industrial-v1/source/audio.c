// Árbitro do PSG — ver audio.h.

#include "audio.h"

#define NCH 4

// pedido vencedor deste frame, por canal (reqPrio 0 = nenhum pedido)
static u8  reqPrio[NCH];
static u16 reqFreq[NCH];         // tom (canais 0..2)
static u8  reqVol[NCH];
static u8  reqNoiseType, reqNoiseFreq;   // canal 3 (ruído)

// último estado ESCRITO no PSG (para só reescrever o que muda)
static bool haveLast[NCH];       // já escreveu algo neste canal?
static u16 lastFreq[NCH];
static u8  lastVol[NCH];
static u8  lastNoiseType = 0xFF, lastNoiseFreq = 0xFF;

void AUDIO_frameBegin(void)
{
    for (u8 c = 0; c < NCH; c++) reqPrio[c] = 0;
}

void AUDIO_tone(u8 ch, u16 freq, u8 vol, u8 prio)
{
    if (ch >= 3) return;                 // 0..2 são canais de tom
    if (prio <= reqPrio[ch]) return;     // já há pedido de prioridade igual/maior
    reqPrio[ch] = prio; reqFreq[ch] = freq; reqVol[ch] = vol;
}

void AUDIO_noise(u8 type, u8 nfreq, u8 vol, u8 prio)
{
    if (prio <= reqPrio[3]) return;
    reqPrio[3] = prio; reqNoiseType = type; reqNoiseFreq = nfreq; reqVol[3] = vol;
}

void AUDIO_frameEnd(void)
{
    // canais de tom (0..2)
    for (u8 c = 0; c < 3; c++)
    {
        if (reqPrio[c])
        {
            if (!haveLast[c] || reqFreq[c] != lastFreq[c])
            {
                PSG_setFrequency(c, reqFreq[c]);
                lastFreq[c] = reqFreq[c];
            }
            if (!haveLast[c] || reqVol[c] != lastVol[c])
            {
                PSG_setEnvelope(c, reqVol[c]);
                lastVol[c] = reqVol[c];
            }
            haveLast[c] = TRUE;
        }
        else if (!haveLast[c] || lastVol[c] != PSG_ENVELOPE_MIN)  // ocioso: silencia 1x
        {
            PSG_setEnvelope(c, PSG_ENVELOPE_MIN);
            lastVol[c] = PSG_ENVELOPE_MIN; haveLast[c] = TRUE;
        }
    }

    // canal de ruído (3): PSG_setNoise só quando o tipo/freq muda (reescrever
    // todo frame reiniciava o gerador de ruído -> chiado)
    if (reqPrio[3])
    {
        if (reqNoiseType != lastNoiseType || reqNoiseFreq != lastNoiseFreq)
        {
            PSG_setNoise(reqNoiseType, reqNoiseFreq);
            lastNoiseType = reqNoiseType; lastNoiseFreq = reqNoiseFreq;
        }
        if (!haveLast[3] || reqVol[3] != lastVol[3])
        {
            PSG_setEnvelope(3, reqVol[3]);
            lastVol[3] = reqVol[3];
        }
        haveLast[3] = TRUE;
    }
    else if (!haveLast[3] || lastVol[3] != PSG_ENVELOPE_MIN)
    {
        PSG_setEnvelope(3, PSG_ENVELOPE_MIN);
        lastVol[3] = PSG_ENVELOPE_MIN; haveLast[3] = TRUE;
    }
}

void AUDIO_silenceAll(void)
{
    for (u8 c = 0; c < NCH; c++)
    {
        PSG_setEnvelope(c, PSG_ENVELOPE_MIN);
        reqPrio[c] = 0; lastVol[c] = PSG_ENVELOPE_MIN; lastFreq[c] = 0xFFFF; haveLast[c] = TRUE;
    }
    lastNoiseType = 0xFF; lastNoiseFreq = 0xFF;   // força reescrever o ruído ao voltar
}
