#ifndef SIGNAL_H
#define SIGNAL_H
#include <genesis.h>

#define SIGNAL_LENGTH 6
#define SIGNAL_SYMBOLS 16
#define SIGNAL_VERSION 1

// Checkpoint at phase entry. Speed is a count of 20-percent upgrades.
// Repeating a password deliberately restores that checkpoint, never mid-combat.
typedef struct { u8 node, flags, power, speed; } SignalProgress;
bool SIGNAL_valid(const SignalProgress *progress);
bool SIGNAL_encode(const SignalProgress *progress,u8 symbols[SIGNAL_LENGTH]);
bool SIGNAL_decode(const u8 symbols[SIGNAL_LENGTH],SignalProgress *progress);
u32 SIGNAL_history(const SignalProgress *progress); // completed nodes only
void SIGNAL_reset(void);
void SIGNAL_capture(u8 node,u8 flags,u8 power,u8 speed);
bool SIGNAL_checkpoint(SignalProgress *progress);
#endif
