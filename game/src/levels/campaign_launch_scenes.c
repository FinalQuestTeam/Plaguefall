// Shared modular shipyard architecture across14/15/16.
#include "levels/campaign_launch.h"
#include "levels/campaign_launch_phase14.inc"
#include "levels/campaign_launch_phase15.inc"
#include "levels/campaign_launch_phase16.inc"
bool CL_sceneReset(void){return CL15_sceneReset();}
void CL_sceneFire(u16 row){if(row==8)CL15_sceneFire();}
