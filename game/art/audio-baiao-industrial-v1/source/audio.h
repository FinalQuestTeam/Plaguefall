#ifndef AUDIO_H
#define AUDIO_H

#include <genesis.h>

// Árbitro do PSG: ÚNICA via de escrita nos 4 canais (SN76489). Música e SFX não
// tocam no PSG direto — apenas REQUISITAM voz por frame com uma prioridade; o
// árbitro escolhe, por canal, o pedido de maior prioridade e escreve o PSG uma
// única vez. Isso acaba com a disputa por "ordem de escrita" e centraliza as
// defesas contra chiado (só reescreve ruído/frequência quando mudam; silencia o
// canal ocioso uma única vez).
//
// Ordem por frame:  AUDIO_frameBegin();  <fontes: MUSIC_update/SFX_update>;  AUDIO_frameEnd();

// prioridades (maior vence o canal no frame)
#define AUD_PRIO_AMBIENT  1     // leito de ruído/ambiente (mais baixa)
#define AUD_PRIO_MUSIC    4     // vozes da música
#define AUD_PRIO_SFX      8     // efeitos transitórios (tiro, coleta)
#define AUD_PRIO_ALERT   12     // dano/bomba (máxima)

void AUDIO_frameBegin(void);                              // zera os pedidos do frame
void AUDIO_tone (u8 ch, u16 freq, u8 vol, u8 prio);      // canais 0..2 (tom); vol 0=alto..15=mudo
void AUDIO_noise(u8 type, u8 nfreq, u8 vol, u8 prio);    // canal 3 (ruído)
void AUDIO_frameEnd(void);                                // resolve e escreve o PSG (1x/canal)
void AUDIO_silenceAll(void);                              // silencia já (transições/boot)

#endif // AUDIO_H
