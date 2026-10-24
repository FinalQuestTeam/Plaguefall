// Reheat the cleared factory. Eggs do not return in this stage.
#include "levels/campaign_factory.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_PEN_YEL,ENEMY_PEN_PUR};
const LevelDef LEVEL11_def={.objective=OBJ_VALVES,.objTarget=3,.spawnSeconds=3,
.spawnCount=1,.enemyCap=3,.shotCap=6,.arena=&CF_FACTORY,
.musicTrack=MUSIC_TRACK_BAIAO,LVL_ROSTER(roster)};
