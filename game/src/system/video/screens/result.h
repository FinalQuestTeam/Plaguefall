#ifndef RESULT_H
#define RESULT_H
#include <genesis.h>
#define RESULT_STAY 0
#define RESULT_RETRY 1
#define RESULT_TITLE 2
#define RESULT_REPLAY 3
// Results own a frozen background until closed; they never resume live actors.
bool RESULT_defeat(u16 kills);
bool RESULT_complete(u16 kills, bool failed);
bool RESULT_victory(void);
u8 RESULT_update(u16 joy, u16 pressed);
void RESULT_close(void);
#endif
