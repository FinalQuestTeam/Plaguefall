// Open the industrial street: reach the factory, independent of kills.
#include "levels/campaign_factory.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_SQ_PUR,ENEMY_PEN_YEL};
const LevelDef LEVEL09_def={.objective=OBJ_REACH,.spawnSeconds=3,.spawnCount=1,
.enemyCap=3,.shotCap=4,.arena=&CF_STREET,.route=&CF_ROUTE09,
.musicTrack=MUSIC_TRACK_BREU,LVL_ROSTER(roster)};
