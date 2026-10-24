#ifndef CAMPAIGN_STATE_H
#define CAMPAIGN_STATE_H
#include <genesis.h>
#define CAMPAIGN_CHURCH_RUINED 1
#define CAMPAIGN_RESCUE_PARTIAL 2
#define CAMPAIGN_DINORAH_DEAD 4
extern u8 campaignFlags;
void CAMPAIGN_reset(void);
void CAMPAIGN_record(u8 node,bool failed);
#endif
