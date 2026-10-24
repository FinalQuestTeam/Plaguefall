#ifndef CAMPAIGN_LAUNCH_H
#define CAMPAIGN_LAUNCH_H
#include "levels/levels.h"
typedef struct {u16 work[5],left,clock;u8 powered,ignition;} CampaignLaunchState;
extern CampaignLaunchState campaignLaunch;
extern const ArenaDef CAMPAIGN_LAUNCH_POWER,CAMPAIGN_LAUNCH_RADIO,CAMPAIGN_LAUNCH_BOSS;
bool CL_active(void);
void CL_start(void);
void CL_camera(s16 *x,s16 *y);
u8 CL_update(void);
void CL_draw(u16 *count);
bool CL_drawHUD(void);
void CL_forceHUD(void);
bool CL_prepText(char *buf,const LevelDef *def);
bool CL_target(s16 *x,s16 *y);
#endif
