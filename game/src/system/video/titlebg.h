#ifndef TITLEBG_H
#define TITLEBG_H

#include <genesis.h>
#include "system/video/sprites/tiles.h"          // ENEMY_ROT_BASE
#include "system/video/sprites/titlebg_data.h"   // TITLEBG_TILES_W / TITLEBG_TILES_H

// Fundo da tela de título: splash de art/title-caatinga-v1 exportada em char-map (mesma
// técnica do splash e dos personagens), em tela cheia — 320x224 = 40x28 tiles
// no plano BG_B, com duas paletas de 16 cores (PAL1/PAL2, escolhidas por tile).
//
// São 1120 tiles, que não cabem junto com os do jogo: ocupam a região dos
// inimigos rotacionados + mech + chão, tudo regenerável. TITLEBG_release()
// devolve essa VRAM (e a PAL1) ao jogo ao sair do título.

#define TITLEBG_TILE_BASE  ENEMY_ROT_BASE
#define TITLEBG_TILES      (TITLEBG_TILES_W * TITLEBG_TILES_H)

void TITLEBG_load(void);        // pinta os tiles na VRAM + carrega PAL1/PAL2
void TITLEBG_draw(void);        // desenha o tilemap no BG_B
void TITLEBG_drawLogo(void);    // ex-voto acima das opções e FinalQuest no canto inferior direito
void TITLEBG_clear(void);       // limpa o BG_B (telas de ajuda/personagens)
void TITLEBG_release(void);     // devolve a VRAM e as paletas ao jogo

#endif // TITLEBG_H
