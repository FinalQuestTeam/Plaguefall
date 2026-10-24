// Ten persistent clutches; enemy kills never advance this objective.
#include "levels/campaign_factory.h"
static const u8 roster[]={ENEMY_TRI_RED,ENEMY_SQ_PUR,ENEMY_PEN_YEL};
const LevelDef LEVEL10_def={.objective=OBJ_EGGS,.objTarget=10,.spawnSeconds=3,
.spawnCount=1,.enemyCap=4,.shotCap=6,.arena=&CF_FACTORY,
.musicTrack=MUSIC_TRACK_BAIAO,LVL_ROSTER(roster)};
