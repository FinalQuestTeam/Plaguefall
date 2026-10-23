// Host-only SGDK surface for exercising the production PSG sequencer/arbiter.
#ifndef TEST_GENESIS_H
#define TEST_GENESIS_H
#include <stdint.h>
#include <stdbool.h>
typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;
extern volatile u32 vtimer;
#define TRUE true
#define FALSE false
#define PSG_ENVELOPE_MIN 15
#define PSG_NOISE_TYPE_PERIODIC 0
#define PSG_NOISE_TYPE_WHITE 1
#define PSG_NOISE_FREQ_CLOCK2 0
#define PSG_NOISE_FREQ_CLOCK4 1
#define PSG_NOISE_FREQ_CLOCK8 2
typedef void VoidCallback(void);
void SYS_disableInts(void);
void SYS_enableInts(void);
void SYS_setVIntCallback(VoidCallback *callback);
u16 SYS_isPAL(void);
void PSG_setFrequency(u16 channel, u16 frequency);
void PSG_setEnvelope(u16 channel, u16 volume);
void PSG_setNoise(u16 type, u16 frequency);
#endif
