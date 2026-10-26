// O sinal da santa: defend the transmitter through the last evacuation flight.
// The graph resolves survival to 6A and a fallen Santa to 6B.
#include "levels/campaign_early.h"
static const u8 roster[]={ENEMY_TRI_YEL,ENEMY_TRI_RED};
const LevelDef LEVEL05_def={
    .objective=OBJ_PROTECT,.npcX=176,.npcY=280,.npcHp=180,.objTarget=120,
    .spawnSeconds=4,.musicTrack=MUSIC_TRACK_LADAINHA,
    .enemyCap=3,.shotCap=6,.musEnemyMax=4,
    .arena=&EARLY_ARENA05,LVL_ROSTER(roster),
};
