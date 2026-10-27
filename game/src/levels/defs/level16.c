// Two-phase Scorpion fight in the shared shipyard; boss plus at most2hunters.
#include "levels/levels.h"
#include "levels/campaign_launch.h"
static const u8 roster[]={ENEMY_BOSS,ENEMY_TRI_YEL};
// Two complete five-shot fans can coexist; the player's pool stays at four.
const LevelDef LEVEL16_def={.killTarget=1,.spawnSeconds=99,.enemyCap=3,.shotCap=4,.enemyShotCap=10,
 .arena=&CAMPAIGN_LAUNCH_BOSS,.musCalmUntil=1,.musEnemyMax=4,.musStepCalm=7,
 .musStepHot=5,.musicTrack=MUSIC_TRACK_BREU,LVL_ROSTER(roster)};
