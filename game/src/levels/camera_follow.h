#ifndef CAMERA_FOLLOW_H
#define CAMERA_FOLLOW_H
#include "levels/arena.h"

void CAMERAFOLLOW_target(const ArenaDef *world,s16 px,s16 py,s16 *x,s16 *y);
void CAMERAFOLLOW_safe(const ArenaDef *world,s16 px,s16 py,s16 *x,s16 *y);
#endif
