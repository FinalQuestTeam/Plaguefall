#ifndef DUST_H
#define DUST_H
#include <genesis.h>
#define DUST_COUNT 12
typedef struct { s32 x, y; s16 vx, vy; } DustParticle;
void DUST_load(u16 tile);
void DUST_reset(DustParticle *particles, u16 seed, u16 height);
void DUST_update(DustParticle *particles, u16 tile, u16 height);
void DUST_brightness(u16 level);
#endif
