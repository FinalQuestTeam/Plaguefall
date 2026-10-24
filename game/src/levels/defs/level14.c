// Five generators power the launch systems. Release fire at each front panel.
#include "levels/levels.h"
#include "levels/campaign_launch.h"
static const u8 roster[]={ENEMY_TRI_YEL,ENEMY_SQ_RED,ENEMY_TRI_RED};
const LevelDef LEVEL14_def={.objective=OBJ_POWER,.objTarget=5,.spawnSeconds=3,.spawnCount=1,
 .enemyCap=4,.shotCap=4,.arena=&CAMPAIGN_LAUNCH_POWER,.musicTrack=MUSIC_TRACK_BREU,LVL_ROSTER(roster)};
