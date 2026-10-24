// Entre os escombros: same targets, persistent roof debris changes circulation.
#include "levels/campaign_early.h"
static const u8 roster[]={ENEMY_SQ_YEL,ENEMY_SQ_RED};
const LevelDef LEVEL02B_def={
    .killTarget=15,.spawnSeconds=5,.musicTrack=MUSIC_TRACK_ENTARDECER,
    .enemyCap=4,.shotCap=6,.musEnemyMax=4,
    .arena=&EARLY_ARENA02B,LVL_ROSTER(roster),
};
