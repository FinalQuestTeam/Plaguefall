// 6B — ramal de pressão: escolta, duas válvulas e dois portões.
#include "levels/levels.h"
#include "levels/campaign_routes.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_TRI_YEL,ENEMY_TRI_ORG};
const LevelDef LEVEL06B_def={
    .objective=OBJ_ESCORT,.route=&CAMPAIGN_ROUTE06B,
    .arena=&CAMPAIGN_ARENA06B,.spawnSeconds=3,
    .enemyCap=3,.shotCap=4,.musicTrack=MUSIC_TRACK_BREU,
    .musCalmUntil=1,.musEnemyMax=3,.musStepCalm=8,.musStepHot=6,
    LVL_ROSTER(roster),
};
