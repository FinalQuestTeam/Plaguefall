#ifndef CAMPAIGN_FACTORY_H
#define CAMPAIGN_FACTORY_H
#include "levels/levels.h"
typedef struct { u16 destroyed,opened,work[3],clock; u8 hp[10],slots[7],done,artReady; } CampaignFactoryState;
extern CampaignFactoryState campaignFactory;
extern const ArenaDef CF_STREET,CF_FACTORY;
extern const RouteDef CF_ROUTE09;
bool CF_active(void);
void CF_start(void);
u8 CF_update(void);
void CF_draw(u16 *count);
bool CF_drawHUD(void);
void CF_forceHUD(void);
bool CF_prepText(char *buf,const LevelDef *def);
bool CF_shotHit(s16 worldX,s16 worldY);
void CF_bomb(void);
#endif
