// Velhos piquetes: Dinorah works in the separated north service compartment.
#include "levels/levels.h"
#include "levels/campaign_resistance.h"
static const u8 roster[]={ENEMY_SQ_PUR,ENEMY_TRI_YEL,ENEMY_TRI_RED,ENEMY_TRI_ORG,ENEMY_PEN_RED};
const LevelDef LEVEL13_def={.killTarget=30,.spawnSeconds=2,.spawnCount=2,.enemyCap=5,.shotCap=6,
 .arena=&CAMPAIGN_RESISTANCE_UNION_ALIVE,.musicTrack=MUSIC_TRACK_BAIAO,LVL_ROSTER(roster)};
