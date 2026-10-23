#ifndef COUNTDOWN_H
#define COUNTDOWN_H
#include <genesis.h>
#define COUNTDOWN_CACHE_TILES 180
bool COUNTDOWN_active(void);
void COUNTDOWN_begin(void);
void COUNTDOWN_set(u8 number); // 3/2/1; zero releases the short VAI tag
void COUNTDOWN_update(void);
void COUNTDOWN_draw(u16 *n);
void COUNTDOWN_close(void);
#endif
