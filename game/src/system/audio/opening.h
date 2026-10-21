#ifndef OPENING_H
#define OPENING_H
#include <genesis.h>

// One continuous score from the Plaguefall logo through the monologue.
// Its VInt callback owns the arbiter until stop; no VDP access in the callback.
void OPENING_start(void);
void OPENING_fadeOut(u16 frames);
void OPENING_stop(void);

#endif
