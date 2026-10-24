#ifndef CAMPAIGN_RESISTANCE_H
#define CAMPAIGN_RESISTANCE_H
#include "levels/levels.h"
typedef struct {
    u16 clock,spawnTimer,work[5],peakEnemies;
    u8 opened,taken,delivered,cargo,priorityDone,prioritySlots[3];
} CampaignResistanceState;
extern CampaignResistanceState campaignResistance;
extern const ArenaDef CAMPAIGN_RESISTANCE_FAVELA,CAMPAIGN_RESISTANCE_FAVELA_TARGETS,CAMPAIGN_RESISTANCE_UNION_ALIVE,CAMPAIGN_RESISTANCE_UNION_DEAD;
bool CAMPAIGN_RESISTANCE_active(void);
bool CAMPAIGN_RESISTANCE_blocked(s16 x,s16 y,u16 w,u16 h);
bool CAMPAIGN_RESISTANCE_managesSpawn(void);
void CAMPAIGN_RESISTANCE_start(void);
void CAMPAIGN_RESISTANCE_beforeUpdate(void);
u8 CAMPAIGN_RESISTANCE_update(void);
void CAMPAIGN_RESISTANCE_draw(u16 *count);
bool CAMPAIGN_RESISTANCE_drawHUD(void);
void CAMPAIGN_RESISTANCE_forceHUD(void);
bool CAMPAIGN_RESISTANCE_prepText(char *buf,const LevelDef *def);
bool CAMPAIGN_RESISTANCE_hideEnemy(u16 i);
#endif
