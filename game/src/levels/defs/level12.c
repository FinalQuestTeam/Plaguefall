// 12 — última escolta pelo corredor de serviço do estaleiro.
// Dinorah viva leva a13A; morte com Damião vivo leva a13B no fluxo.
#include "levels/levels.h"
#include "levels/campaign_routes.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_TRI_YEL,ENEMY_SQ_PUR};
const LevelDef LEVEL12_def={
    .objective=OBJ_ESCORT,.route=&CAMPAIGN_ROUTE12,
    .arena=&CAMPAIGN_ARENA12,.spawnSeconds=2,
    .enemyCap=3,.shotCap=4,.musicTrack=MUSIC_TRACK_BAIAO,
    .musEnemyMax=3,LVL_ROSTER(roster),
};
