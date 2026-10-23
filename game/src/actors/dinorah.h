#ifndef DINORAH_ACTOR_H
#define DINORAH_ACTOR_H
#include "levels/levels.h"
#include "actors/shots.h"
#define DIN_MOVING 0
#define DIN_WAITING 1
#define DIN_PAUSING 2
#define DIN_AIMING 3
#define DIN_ARRIVED 4
#define DIN_DEAD 5
extern s16 dinorahX,dinorahY,dinorahHp;
extern u8 dinorahState,dinorahNode;
extern FShot allyShots[2];
void DINORAH_start(const RouteDef *route);
void DINORAH_clear(void);
bool DINORAH_active(void);
bool DINORAH_alive(void);
bool DINORAH_hidden(void);
void DINORAH_damage(u16 damage);
u16 DINORAH_update(void);
void DINORAH_prepare(void);
u16 DINORAH_tile(void);
bool DINORAH_flip(void);
const char *DINORAH_status(void);
#endif
