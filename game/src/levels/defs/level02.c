// A igreja de pé: same courtyard, introduce the ranged enemy.
#include "levels/levels.h"
static const u8 roster[]={ENEMY_SQ_YEL,ENEMY_SQ_RED};
const LevelDef LEVEL02_def={
    .killTarget=15,.spawnSeconds=5,.musicTrack=MUSIC_TRACK_LADAINHA,
    .enemyCap=4,.shotCap=6,.musEnemyMax=4,
    .arena=&COURTYARD_arena,LVL_ROSTER(roster),
};
