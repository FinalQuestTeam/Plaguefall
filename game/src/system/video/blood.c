// Poça de sangue (verde) ao matar inimigos: decalque 16x16 no BG_A, montado por
// 4 cópias espelhadas do tile TILE_BLOOD (quarto de disco), com o canto denso
// voltado para o centro. Fica sobre o chão (BG_B) e sob os sprites.

#include "system/video/blood.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "elements/terrain.h"

void BLOOD_splat(s16 cx, s16 cy)
{
    if(arenaActive && (cx<cameraX || cx>cameraX+320 || cy<cameraY || cy>cameraY+224))return;
    // canto superior-esquerdo (em tiles) da poça 16x16 centrada em (cx, cy)
    s16 tx = (s16) ((cx - 8) / 8);
    s16 ty = (s16) ((cy - 8) / 8);

    // mantém dentro do interior da arena (não pinta borda/HUD)
    if (tx < INNER_MIN_X/8) tx = INNER_MIN_X/8;
    if (tx > (INNER_MAX_X-15)/8) tx = (INNER_MAX_X-15)/8;
    if (ty < INNER_MIN_Y/8) ty = INNER_MIN_Y/8;
    if (ty > (INNER_MAX_Y-15)/8) ty = (INNER_MAX_Y-15)/8;
    if (arenaActive && ARENA_blocked(tx*8,ty*8,16,16)) return;
    // The residue shares BG_A with portable hazards. Never punch a visual
    // hole in damaging/slowing terrain by replacing its connected tiles.
    if(TERRAIN_active() && (TERRAIN_attr(tx,ty) || TERRAIN_attr(tx+1,ty) ||
       TERRAIN_attr(tx,ty+1) || TERRAIN_attr(tx+1,ty+1)))return;
    if (arenaActive) {ty &= 31;tx &= 63;}

    const u16 t = TILE_USER_INDEX + TILE_BLOOD;
    // TILE_ATTR_FULL(pal, prio, flipV, flipH, index) — prio FALSE: fica sob os sprites
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, TRUE,  TRUE,  t), tx,     ty);      // sup-esq
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, TRUE,  FALSE, t), (tx + 1)&63, ty);      // sup-dir
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, TRUE,  t), tx,     (ty + 1)&31);  // inf-esq
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, t), (tx + 1)&63, (ty + 1)&31);  // inf-dir
}
