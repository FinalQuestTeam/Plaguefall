// Um teto para a noite: remove twenty insects from the dry warehouse.
#include "levels/campaign_early.h"
static const u8 roster[]={ENEMY_SQ_YEL,ENEMY_SQ_RED};
const LevelDef LEVEL04_def={
    .killTarget=20,.spawnSeconds=4,.musicTrack=MUSIC_TRACK_BREU,
    .enemyCap=4,.shotCap=6,.musEnemyMax=4,
    .arena=&EARLY_ARENA04,LVL_ROSTER(roster),
};
