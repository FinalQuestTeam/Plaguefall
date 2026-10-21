#ifndef PANEL_H
#define PANEL_H
#include <genesis.h>
#define PANEL_BODY PAL0
#define PANEL_ACCENT PAL2
#define PANEL_LIGHT PAL3
// One reversible graphics loan, shared by pause and its help subpages.
bool PANEL_begin(void);
void PANEL_end(void);
void PANEL_page(const char *title, const char *right);
void PANEL_text(const char *text, u16 x, u16 y, u16 palette);
void PANEL_right(const char *text, u16 y, u16 palette);
void PANEL_wrap(const char *text, u16 x, u16 y, u16 width, u16 step, u16 palette);
void PANEL_selection(u16 row);
void PANEL_enemy(u8 type, u16 x, u16 y, u16 slot);
u16 PANEL_scratch(void);
#endif
