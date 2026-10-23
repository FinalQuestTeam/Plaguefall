#ifndef ACTORDEATH_H
#define ACTORDEATH_H
#include <genesis.h>
#define ACTOR_DEATH_HERO 0
#define ACTOR_DEATH_DINORAH 1
#define ACTOR_DEATH_FRAMES 4
// Separate records allow both characters to fall in the same game update.
typedef struct { u16 tick; u8 pose,loadedPose; bool active,flip; } ActorDeath;
extern ActorDeath actorDeaths[2];
void ACTORDEATH_clear(u8 actor);
void ACTORDEATH_start(u8 actor,bool flip);
void ACTORDEATH_update(void);
void ACTORDEATH_prepare(u8 actor,u16 tile);
bool ACTORDEATH_active(u8 actor);
bool ACTORDEATH_pending(void);
bool ACTORDEATH_flip(u8 actor);
#endif
