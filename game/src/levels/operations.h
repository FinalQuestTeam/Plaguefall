#ifndef TEST_OPERATIONS_H
#define TEST_OPERATIONS_H
#include "levels/levels.h"
#define OPS_FIRST_ROOM 11
#define OPS_COUNT 8
// These missions are deliberately outside the campaign graph.
typedef struct {
    u16 work[3], clock, spawnTimer, damageTimer, captured;
    u16 peakEnemies, peakPlayerShots, peakEnemyShots;
    u8 done, delivered, cargo, phase, gateHp[3], outcome, bonus, postHp;
    u16 trappedMask;
    u8 cargoOpen,held;
} OperationsState;
extern OperationsState operations;
extern const ArenaDef OPS_arenas[OPS_COUNT];
extern const ArenaRect OPS_evacGates[3];
extern const RouteDef OPS_evacRoute;
bool OPS_active(void);
const LevelDef *OPS_def(u8 room);
void OPS_begin(void);
void OPS_beforeUpdate(void);
void OPS_update(void);
void OPS_animateResult(void);
void OPS_draw(u16 *sprites);
void OPS_drawHUD(void);
void OPS_restoreView(void);
const char *OPS_hint(void);
bool OPS_blocked(s16 x,s16 y,u16 w,u16 h);
bool OPS_shotBlocked(s16 x,s16 y,bool player);
u16 OPS_backgroundAttr(s16 col,s16 row);
#endif
