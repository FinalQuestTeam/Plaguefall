// O que ainda resta: five persistent supply sources, one carried load, depot.
#include "levels/levels.h"
#include "levels/campaign_resistance.h"
static const u8 roster[]={ENEMY_TRI_YEL,ENEMY_TRI_RED,ENEMY_SQ_PUR};
const LevelDef LEVEL07_def={.objective=OBJ_CARGO,.objTarget=5,.spawnSeconds=3,.spawnCount=1,
 .enemyCap=4,.shotCap=6,.arena=&CAMPAIGN_RESISTANCE_FAVELA,
 .musicTrack=MUSIC_TRACK_ENTARDECER,LVL_ROSTER(roster)};
