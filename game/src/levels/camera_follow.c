// Stable player-only framing: scenery and escort never move the idle camera.
#include "levels/camera_follow.h"
static s16 bound(s16 value,s16 low,s16 high)
{return value<low ? low : value>high ? high : value;}
void CAMERAFOLLOW_safe(const ArenaDef *world,s16 px,s16 py,s16 *x,s16 *y)
{
    const s16 mx=world->width>320 ? world->width-320 : 0;
    const s16 my=world->height>224 ? world->height-224 : 0;
    // Actual body: px-8,py-31,32x48. Eight pixels of safe space where
    // physically possible; intersect with the real world's camera bounds.
    *x=bound(*x,bound(px-288,0,mx),bound(px-16,0,mx));
    *y=bound(*y,bound(py-199,0,my),bound(py-63,0,my));
}
void CAMERAFOLLOW_target(const ArenaDef *world,s16 px,s16 py,s16 *x,s16 *y)
{
    const s16 mx=world->width>320 ? world->width-320 : 0;
    const s16 my=world->height>224 ? world->height-224 : 0;
    // Body center(px+8,py-7), useful viewport center(160,124).
    // This is deliberately stateless: entry, stopping, NPC movement/death
    // and elapsed idle time cannot add a second framing adjustment.
    *x=bound(px-152,0,mx);
    *y=bound(py-131,0,my);
    CAMERAFOLLOW_safe(world,px,py,x,y);
}
