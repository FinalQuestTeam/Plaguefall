#ifndef ENEMY_BOSS_H
#define ENEMY_BOSS_H
#include "enemies/enemies.h"

#define BOSS_FURY_HP 12
// Boss-only flags in the otherwise unused tB; every spawn clears them.
#define BOSS_FURY 0x8000
#define BOSS_SECOND_DASH 0x4000
#define BOSS_NARROW_FAN 0x2000
#define BOSS_APPROACH 0
#define BOSS_TELEGRAPH 1
#define BOSS_DASH 2
#define BOSS_TRANSITION 3
#define BOSS_RECOVER 4
#define BOSS_RANGED 5

static inline bool ENEMYBOSS_stationary(const Enemy *e)
{
    return e->type==ENEMY_BOSS && (e->tB&BOSS_FURY) &&
           (e->mode==BOSS_TRANSITION || e->mode==BOSS_TELEGRAPH || e->mode==BOSS_RECOVER);
}
#endif
