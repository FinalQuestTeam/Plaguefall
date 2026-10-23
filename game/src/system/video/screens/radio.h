#ifndef RADIO_H
#define RADIO_H
#include <genesis.h>
bool RADIO_begin(u8 node);
void RADIO_line(u8 side,u8 remote,u8 page,u8 total);
void RADIO_glyph(char glyph,u8 col,u8 row);
void RADIO_command(const char *command);
void RADIO_end(void);
bool RADIO_handoffMission(void);
#endif
