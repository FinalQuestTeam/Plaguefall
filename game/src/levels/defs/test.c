// Approved six-room training suite. Campaign definitions are independent.
#include "levels/levels.h"
#include "levels/test_scene.h"
#include "levels/stage_scenes.h"
static const u8 all[]={0,1,2,3,4,5,6,7,8,9,10,11,ENEMY_BOSS};
static const u8 dummy[]={ENEMY_DUMMY,ENEMY_TARGET};
static const u8 defense[]={ENEMY_TRI_RED,ENEMY_TRI_YEL,ENEMY_SQ_ORG};
const LevelDef TEST_def={.enemyCap=16,.shotCap=16,.arena=&TEST_LAB_arena,LVL_ROSTER(all)};
const LevelDef TEST2_def={.enemyCap=16,.shotCap=16,.arena=&TEST_ITEMS_arena,LVL_ROSTER(dummy)};
// Same map, objective, target, music and caps as campaign phase 5.
const LevelDef TEST3_def={.objective=OBJ_PROTECT,.objTarget=30,.npcX=176,.npcY=200,
    .spawnSeconds=4,.enemyCap=4,.shotCap=6,.musicTrack=MUSIC_TRACK_LADAINHA,
    .arena=&ARENA05,LVL_ROSTER(defense)};
const LevelDef TEST4_def={.enemyCap=16,.shotCap=16,.arena=&TEST_COLLISION_arena,
    .modularTerrain=TRUE,
    .lava=TEST_lava,.lavaCount=1,.mud=TEST_mud,.mudCount=1,LVL_ROSTER(dummy)};
const LevelDef TEST5_def={.enemyCap=16,.shotCap=16,.arena=&TEST_COMBAT_arena,LVL_ROSTER(all)};
const LevelDef TEST6_def={.enemyCap=16,.shotCap=16,.arena=&TEST_COMBAT_arena,LVL_ROSTER(all)};
// Isolated loss/recovery lab: no enemies or hazards are spawned.
const LevelDef TEST10_def={.enemyCap=1,.shotCap=16,.arena=&TEST_COMBAT_arena,LVL_ROSTER(dummy)};
