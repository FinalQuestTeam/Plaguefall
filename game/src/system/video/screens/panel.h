#ifndef PANEL_H
#define PANEL_H
#include <genesis.h>
#define PANEL_BODY PAL0
#define PANEL_ACCENT PAL2
#define PANEL_LIGHT PAL3
// One reversible graphics loan, shared by pause and its help subpages.
bool PANEL_begin(void);
// Destructive preparation pages need no snapshot of the previous arena.
bool PANEL_beginMission(const u16 *returnColors);
bool PANEL_isMission(void);
void PANEL_end(void);
void PANEL_page(const char *title, const char *right);
// Mission/guide pages use the same single-monitor console as preparation.
void PANEL_radioPage(const char *title, const char *right);
void PANEL_radioCell(u16 attr,u16 x,u16 y);
void PANEL_radioPortrait(const u32 *source);
void PANEL_radioCommit(void);
void PANEL_text(const char *text, u16 x, u16 y, u16 palette);
void PANEL_right(const char *text, u16 y, u16 palette);
void PANEL_wrap(const char *text, u16 x, u16 y, u16 width, u16 step, u16 palette);
void PANEL_selection(u16 row);
void PANEL_enemy(u8 type, u16 x, u16 y, u16 slot);
// Six 32x32 symbols share the existing 112-tile scratch loan, PAL1.
void PANEL_icon32(const u32 *source,u16 x,u16 y,u16 slot);
u16 PANEL_scratch(void);
#endif
