#ifndef PAUSE_H
#define PAUSE_H
#include <genesis.h>
#define PAUSE_STAY 0
#define PAUSE_RESUME 1
#define PAUSE_EXIT 2
#define PAUSE_TEST_CONFIG 3
#define PAUSE_TEST_RESTART 4
#define PAUSE_TEST_ROOM 5
bool PAUSE_show(u16 kills);
u8 PAUSE_update(u16 pressed);
#endif
