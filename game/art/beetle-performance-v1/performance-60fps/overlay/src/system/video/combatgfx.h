#ifndef COMBATGFX_H
#define COMBATGFX_H
#include <genesis.h>
#include "actors/shots.h"
#define COMBAT_DEATH_CAP 4
// Logical death is immediate. These records own no enemy pointer or hitbox.
typedef struct {
    s16 x,y;
    u16 age,tile;
    u8 type,size,frame,active,ready,pad;
} CombatDeath;
extern CombatDeath combatDeaths[COMBAT_DEATH_CAP];
void COMBATGFX_clear(void);
void COMBATGFX_invalidate(void);
void COMBATGFX_spawn(u8 type,s16 x,s16 y);
void COMBATGFX_update(void);
u16 COMBATGFX_remaining(void);
// Runs after actor uploads, with their remaining shared frame allowance.
void COMBATGFX_prepare(u16 actorTransfers);
u16 COMBATGFX_shotAttr(u8 style,s32 vx,s32 vy);

u16 COMBATGFX_cachedShotAttr(FShot *shot,u8 style);

const u16 *COMBATGFX_shotTable(void);
#endif
