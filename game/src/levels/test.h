#ifndef LEVELS_TEST_H
#define LEVELS_TEST_H
#include <genesis.h>
#define TEST_ROOMS 18
#define TEST_DEATH_ROOM 9
#define TEST_RULE_ROOM 10
#define TEST_ENDING_COUNT 8
// Expanded where graph.h is also included, after the campaign node IDs.
#define TEST_ENDING_FIRST (TEST_ROOMS + NODE_COUNT + 1)
typedef struct {
    u8 animation,direction,slow,selected,repeat;
    u8 dummyHp,chain,restock,initialHp;
    u8 attacks,kind,noDefeat;
    u8 count,shots,status,deaths;
} TestSettings;
extern TestSettings testSettings[TEST_ROOMS];
extern u32 testTicks;
extern u8 testResult;
// Campaign shortcuts use the real nodes; technical-room settings stay separate.
extern bool testCampaignMode;
u16 TEST_measuredFps(void);
u16 TEST_peakCpu(void);
void TEST_defaults(void);
const char *TEST_name(u8 room);
void TEST_goal(char *text);
u8 TEST_chooseRoom(u8 initial); // 0 cancel; TEST_ROOMS+node; TEST_ENDING_FIRST+flags
bool TEST_configure(void);
void TEST_pauseDraw(u8 selection);
void TEST_pauseSelection(u8 selection);
void TEST_begin(bool retryRules);
void TEST_resume(void);
void TEST_beforeUpdate(void);
void TEST_afterUpdate(void);
void TEST_drawHUD(void);
void TEST_finish(u8 outcome);
bool TEST_objectiveRoom(void);
bool TEST_staticEnemies(void);
bool TEST_noDefeat(void);
bool TEST_effectTick(void);
bool TEST_animation(u8 index,u8 *dir,u8 *pose);
u16 TEST_shotLimit(void);
void TEST_requestDeath(void);
void TEST_deathInput(u16 pressed);
void TEST_ruleInput(u16 pressed);
u8 TEST_ruleNode(void); // nó representativo do trecho escolhido na sala 10
#endif
