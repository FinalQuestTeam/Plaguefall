#ifndef INTRO_H
#define INTRO_H

#include <genesis.h>

// Boot only: storyboard monologue after FinalQuest, before the title menu.
// A completes text / advances, START skips. Automatic playback uses fps.
// Borrows the future gameplay VRAM; call before TILEGEN_init / FLOOR_init.
void INTRO_run(void);

#endif
