#ifndef MISSION_H
#define MISSION_H
#include <genesis.h>
// Two rows of 36 encoded glyphs, plus the terminator.
#define MISSION_GOAL_SIZE 73
const char *MISSION_name(u8 node);
void MISSION_goal(char *text,u8 node);
void MISSION_show(u8 node);
// B opens the phase guide; only A on the mission card requests gameplay.
bool MISSION_update(u16 pressed);
#endif
