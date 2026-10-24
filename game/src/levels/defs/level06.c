// 6A — escolta pelos esgotos após a evacuação completa.
#include "levels/levels.h"
#include "levels/campaign_routes.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_TRI_YEL};
const LevelDef LEVEL06_def={
    .objective=OBJ_ESCORT,.route=&CAMPAIGN_ROUTE06A,
    .arena=&CAMPAIGN_ARENA06A,.spawnSeconds=3,
    .enemyCap=3,.shotCap=4,.musicTrack=MUSIC_TRACK_ENTARDECER,
    .musEnemyMax=3,LVL_ROSTER(roster),
};
