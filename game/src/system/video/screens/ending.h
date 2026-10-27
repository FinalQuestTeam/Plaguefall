#ifndef ENDING_H
#define ENDING_H
#include <genesis.h>
#include "core/campaign_state.h"

// Three independent consequences, in storyboard order: 07A/B, 07C/D, 06C/D.
#define ENDING_SLIDE_COUNT 3
static inline u8 ENDING_shot(u8 flags, u8 slide)
{
    if(slide==0)return (flags&CAMPAIGN_CHURCH_RUINED) ? 1 : 0;
    if(slide==1)return (flags&CAMPAIGN_RESCUE_PARTIAL) ? 3 : 2;
    return (flags&CAMPAIGN_DINORAH_DEAD) ? 5 : 4;
}

// Timed illustrated epilogue. START skips; the caller rebuilds borrowed tiles.
void ENDING_run(void);
#endif
