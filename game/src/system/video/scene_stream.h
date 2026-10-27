#ifndef SCENE_STREAM_H
#define SCENE_STREAM_H
#include <genesis.h>
#include "levels/arena.h"
bool SCENESTREAM_begin(const ArenaScene *scene);
void SCENESTREAM_end(void);
bool SCENESTREAM_move(s16 x,s16 y);
u16 SCENESTREAM_attr(s16 col,s16 row);
void SCENESTREAM_suspend(void);
bool SCENESTREAM_resume(void);
bool SCENESTREAM_heavyFrame(void);
bool SCENESTREAM_active(void);
extern volatile u16 sceneStreamFaults,sceneStreamPeak,sceneStreamUploads;
extern volatile u16 sceneStreamDeferrals;
#endif
