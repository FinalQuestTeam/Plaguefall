// Estatísticas de fase — ver stats.h.

#include "core/stats.h"
#include "core/game.h"          // fps

PhaseStats phaseStats;

void STATS_reset(void)
{
    phaseStats.bombsUsed = 0;
    phaseStats.damageTaken = 0;
    phaseStats.frames = 0;
    phaseStats.objFailed = FALSE;
}

void STATS_tick(void)
{
    phaseStats.frames++;
}

u16 STATS_seconds(void)
{
    return (u16) (phaseStats.frames / fps);
}
