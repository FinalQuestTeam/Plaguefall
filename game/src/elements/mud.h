#ifndef MUD_H
#define MUD_H

#include <genesis.h>
#include "elements/elements.h"

// lentidão progressiva: BASE% imediato ao entrar, +STEP% a cada segundo, até MAX%
#define MUD_PLAYER_BASE     50
#define MUD_PLAYER_STEP     15
#define MUD_PLAYER_MAX      85
#define MUD_ENEMY_BASE      15
#define MUD_ENEMY_STEP      10
#define MUD_ENEMY_MAX       45

// desenha o padrão do tile TILE_MUD no buffer de tiles procedurais
void MUD_buildTile(u32 *tileBuf);

// preenche as poças de lama no plano BG_A
void MUD_draw(const TileRect *rects, u16 count);

// zera a progressão do jogador (trocar de fase / reiniciar)
void MUD_reset(void);

// atualiza a lentidão do jogador e dos inimigos que pisam na lama
void MUD_update(const TileRect *rects, u16 count);

#endif // MUD_H
