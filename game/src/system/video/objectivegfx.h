#ifndef OBJECTIVE_GFX_H
#define OBJECTIVE_GFX_H
#include <genesis.h>
#define OBJECTIVE_VISUAL_CAP 7
#define OBJECTIVE_ART_COUNT 10
#define OART_NEST 0
#define OART_GENERATOR 1
#define OART_CARGO 2
#define OART_TRANSMITTER 3
#define OART_VALVE 4
#define OART_GATE 5
#define OART_TRAP 6
#define OART_RADIO 7
#define OART_REFUGEE 8
#define OART_CAGE 9
typedef struct {
    s16 x,y;
    u16 age;
    u8 art,frame,mode,visible,ground,primed;
} ObjectiveVisual;
extern ObjectiveVisual objectiveVisuals[OBJECTIVE_VISUAL_CAP];
extern u16 objectiveAnimationEvents[OBJECTIVE_ART_COUNT];
extern u8 objectiveAnimationFrameMask[OBJECTIVE_ART_COUNT];
extern u16 objectiveArtBases[OBJECTIVE_ART_COUNT];
void OBJECTIVEGFX_start(u8 mission);
bool OBJECTIVEGFX_startCampaign(u16 artMask);
void OBJECTIVEGFX_place(u8 slot,u8 art,s16 x,s16 y,bool ground);
void OBJECTIVEGFX_prime(u8 slot,bool primed);
void OBJECTIVEGFX_activate(u8 slot);
void OBJECTIVEGFX_idle(u8 slot);
void OBJECTIVEGFX_hide(u8 slot);
void OBJECTIVEGFX_settle(u8 slot,u8 frame);
void OBJECTIVEGFX_update(void);
void OBJECTIVEGFX_ground(bool force);
void OBJECTIVEGFX_draw(u16 *count);
void OBJECTIVEGFX_radioHit(void);
u16 OBJECTIVEGFX_actorDepth(s16 x,s16 feetY,u16 width,u16 attr);
void OBJECTIVEGFX_cargo(u16 *count,s16 x,s16 y);
bool OBJECTIVEGFX_pending(void);
#endif
