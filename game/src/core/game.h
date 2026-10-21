#ifndef GAME_H
#define GAME_H

#include <genesis.h>
#include "levels/arena.h"

// ---------------------------------------------------------------------------
// Arena: tela inteira (40x27 tiles, 320x216 px), borda incluída.
// Linha 0 fica para o HUD.
// ---------------------------------------------------------------------------
#define ARENA_TILE_X    0
#define ARENA_TILE_Y    1
#define ARENA_TILES_W   40
#define ARENA_TILES_H   27

#define INNER_MIN_X     arenaMinX
#define INNER_MIN_Y     arenaMinY
#define INNER_MAX_X     arenaMaxX
#define INNER_MAX_Y     arenaMaxY

// O mapa de tiles da VRAM (TILE_*) foi para system/video/sprites/tiles.h.
// Os contratos por área foram para os headers donos:
//   damagePlayer / loseHp / healPlayer     -> actors/player.h
//   fireEnemyShot / fireEnemySpread         -> actors/shots.h
//   sfxItemPickup                           -> system/audio/sfx.h

// ---------------------------------------------------------------------------
// Estado global compartilhado entre os módulos (definido em core/flow.c e
// actors/player.c).
// ---------------------------------------------------------------------------
extern s16 px, py;          // canto superior esquerdo do jogador (16x16)
extern u8 playerSlowPct;    // lentidão do jogador em % (aplicada por elementos)
extern bool gameOver;
extern bool bossDefeated;   // chefe (Escorpiao) morto — encerra a fase 16
extern u16 fps;             // 60 (NTSC) ou 50 (PAL)
extern u16 ENEMY_CD;        // cadência de tiro inimigo (1 tiro / 2 s)

#endif // GAME_H
