#ifndef DARKSPACE_EIGHT_DIRECTIONS_H
#define DARKSPACE_EIGHT_DIRECTIONS_H

/* Same clockwise order as ENEMYGFX_faceDir and the player's FACE_DIR table. */
enum DarkspaceDirection
{
    DARKSPACE_N = 0,
    DARKSPACE_NE = 1,
    DARKSPACE_L = 2,
    DARKSPACE_SE = 3,
    DARKSPACE_S = 4,
    DARKSPACE_SO = 5,
    DARKSPACE_O = 6,
    DARKSPACE_NO = 7
};

/* Each direction has two consecutive SGDK animations: idle, then run. */
#define DARKSPACE_IDLE_ANIM(dir) ((dir) * 2)
#define DARKSPACE_RUN_ANIM(dir)  ((dir) * 2 + 1)
#define DARKSPACE_IDLE_FRAMES 4
#define DARKSPACE_RUN_FRAMES 6
#define DARKSPACE_FRAME_WIDTH 32
#define DARKSPACE_FRAME_HEIGHT 48

#endif
