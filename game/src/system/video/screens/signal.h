#ifndef SIGNAL_SCREEN_H
#define SIGNAL_SCREEN_H
#include <genesis.h>
#include "core/signal.h"
// Draw inside an existing mission/pause panel; caller owns its lifecycle.
bool SIGNALSCR_checkpoint(void);
// Dedicated title-menu input, with its own radio panel and audio loop.
bool SIGNALSCR_read(SignalProgress *progress);
#endif
