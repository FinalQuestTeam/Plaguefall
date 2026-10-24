#include "core/campaign_state.h"
#include "levels/graph.h"
#include "core/stats.h"
u8 campaignFlags;
void CAMPAIGN_reset(void){campaignFlags=0;}
void CAMPAIGN_record(u8 node,bool failed)
{
    if(node==N_1 && phaseStats.bombsUsed)campaignFlags|=CAMPAIGN_CHURCH_RUINED;
    if(node==N_5 && failed)campaignFlags|=CAMPAIGN_RESCUE_PARTIAL;
    if(node==N_12 && failed)campaignFlags|=CAMPAIGN_DINORAH_DEAD;
}
