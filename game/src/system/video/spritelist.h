#ifndef SPRITES_H
#define SPRITES_H

#include <genesis.h>

// Lista de sprites de hardware, reconstruída a cada quadro (jogador, inimigos,
// itens, projéteis e os arcos do raio), encadeada por link.
void SPRITES_draw(void);    // monta e envia a lista do quadro
void SPRITES_hide(void);    // esconde todos (telas de preparação/pausa)
// Stage during SPRITES_draw; final flush enforces <=80 sprites globally,
// <=20 and <=320 pixels per scanline, preserving actor pieces together.
bool SPRITES_emit(u16 *n, s16 x, s16 y, u8 size, u16 attr);

#endif // SPRITES_H
