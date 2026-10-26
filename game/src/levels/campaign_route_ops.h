#ifndef CAMPAIGN_ROUTE_OPS_H
#define CAMPAIGN_ROUTE_OPS_H
#include "levels/levels.h"
typedef struct {
    u16 work[2],steamClock,damageTimer;
    u8 gateHp[2],pressureMask;
    u16 gateClearTicks[2];
} CampaignRouteOperations;
extern CampaignRouteOperations campaignRouteOps;
bool CR_OPS_active(void);
u8 CR_OPS_gateBlockMask(void);
void CR_OPS_start(void);
void CR_OPS_update(void);
void CR_OPS_draw(u16 *sprites);
bool CR_OPS_drawHUD(void);
bool CR_OPS_prepText(char *buf,const LevelDef *def);
bool CR_OPS_blocked(s16 x,s16 y,u16 w,u16 h);
bool CR_OPS_shotBlocked(s16 x,s16 y,bool player);
#endif
