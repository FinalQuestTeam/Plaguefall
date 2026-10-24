// Scorpion emerges from the burning rocket engines. Existing authored bossAI.
#include "levels/levels.h"
#include "levels/campaign_launch.h"
static const u8 roster[]={ENEMY_BOSS,ENEMY_TRI_YEL};
const LevelDef LEVEL16_def={.killTarget=1,.spawnSeconds=99,.enemyCap=4,.shotCap=4,
 .arena=&CAMPAIGN_LAUNCH_BOSS,.musCalmUntil=1,.musEnemyMax=4,.musStepCalm=7,
 .musStepHot=5,.musicTrack=MUSIC_TRACK_BREU,LVL_ROSTER(roster)};
