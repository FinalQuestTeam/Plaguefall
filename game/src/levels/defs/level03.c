// Abram caminho: clear the 2560px road to the depot; arrival wins, not kills.
#include "levels/campaign_early.h"
static const u8 roster[]={ENEMY_SQ_YEL,ENEMY_SQ_RED};
const LevelDef LEVEL03_def={
    .objective=OBJ_REACH,.route=&EARLY_ROUTE03,
    .spawnSeconds=4,.musicTrack=MUSIC_TRACK_ENTARDECER,
    .enemyCap=4,.shotCap=6,.musEnemyMax=4,
    .arena=&EARLY_ARENA03,LVL_ROSTER(roster),
};
