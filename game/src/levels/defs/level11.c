// Reheat the cleared factory. Eggs do not return in this stage.
#include "levels/campaign_factory.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_PEN_YEL,ENEMY_PEN_PUR};
const LevelDef LEVEL11_def={.objective=OBJ_VALVES,.objTarget=6,.spawnSeconds=2,
.spawnCount=1,.enemyCap=5,.shotCap=6,.arena=&CF_FACTORY_REHEAT,
.musicTrack=MUSIC_TRACK_BAIAO,LVL_ROSTER(roster)};
