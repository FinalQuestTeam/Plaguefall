// Até o último sair: one contact enemy, ninety seconds to evacuate the church.
#include "levels/levels.h"
static const u8 roster[]={ENEMY_SQ_YEL};
const LevelDef LEVEL01_def={
    .objective=OBJ_SURVIVE,.objTarget=90,
    .spawnSeconds=5,.musicTrack=MUSIC_TRACK_LADAINHA,
    .enemyCap=4,.shotCap=6,.musCalmUntil=1,.musEnemyMax=4,
    .arena=&COURTYARD_arena,LVL_ROSTER(roster),
};
