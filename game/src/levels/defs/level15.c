// Keep the powered radio intact for the full120second ignition sequence.
#include "levels/levels.h"
#include "levels/campaign_launch.h"
static const u8 roster[]={ENEMY_TRI_YEL,ENEMY_SQ_RED,ENEMY_TRI_RED};
const LevelDef LEVEL15_def={.objective=OBJ_RADIO,.objTarget=120,.spawnSeconds=3,.spawnCount=1,
 .npcX=244,.npcY=180,.npcHp=100,.enemyCap=3,.shotCap=4,.arena=&CAMPAIGN_LAUNCH_RADIO,
 .musicTrack=MUSIC_TRACK_BAIAO,LVL_ROSTER(roster)};
