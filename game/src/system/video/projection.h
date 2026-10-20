#ifndef VIDEO_PROJECTION_H
#define VIDEO_PROJECTION_H
// Ground-space simulation is shared by collision/AI. All enemy bodies,
// projectiles and chain sparks use this same screen-space height offset.
#define VIDEO_HEIGHT_OFFSET 16
#define VIDEO_PROJECT_Y(y) ((y)-VIDEO_HEIGHT_OFFSET)
#endif
