// Cortar o chamado: the3marked transmitters matter; ordinary kills do not.
#include "levels/levels.h"
#include "levels/campaign_resistance.h"
static const u8 roster[]={ENEMY_SQ_RED,ENEMY_TRI_YEL,ENEMY_TRI_ORG};
const LevelDef LEVEL08_def={.objective=OBJ_PRIORITY,.objTarget=3,.spawnSeconds=2,.spawnCount=1,
 .enemyCap=6,.shotCap=6,.arena=&CAMPAIGN_RESISTANCE_FAVELA_TARGETS,
 .musicTrack=MUSIC_TRACK_BAIAO,LVL_ROSTER(roster)};
