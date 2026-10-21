// Projéteis dos inimigos: disparo mirado no jogador (simples e em leque) e
// atualização/colisão com o círculo do jogador.

#include "actors/shots.h"
#include "core/game.h"
#include "actors/player.h"
#include "system/audio/sfx.h"
#include "levels/levels.h"

// cria um projétil inimigo em (fx, fy) 26.6 com velocidade dada (26.6) e `dmg`
static void spawnEShot(s32 fx, s32 fy, s32 vx, s32 vy, u8 dmg)
{
    const u16 cap = LEVEL_current()->shotCap ? LEVEL_current()->shotCap : MAX_ESHOTS;
    for (u16 i = 0; i < cap; i++)
    {
        if (eshots[i].active) continue;
        eshots[i].x = fx;
        eshots[i].y = fy;
        eshots[i].vx = vx;
        eshots[i].vy = vy;
        eshots[i].dmg = dmg;
        eshots[i].active = TRUE;
        return;
    }
}

void fireEnemyShot(s16 ex, s16 ey)
{
    s16 dx = (px + 8) - (ex + 8);
    s16 dy = (py + 8) - (ey + 8);
    u32 dist = getApproximatedDistance(dx, dy);
    if (dist == 0) dist = 1;

    spawnEShot((s32) (ex + 4) << 6, (s32) (ey + 4) << 6,
               ((s32) dx * ESHOT_SPEED << 6) / (s32) dist,
               ((s32) dy * ESHOT_SPEED << 6) / (s32) dist, ESHOT_DAMAGE);
    SFX_enemyShot();
}

void fireEnemySpreadDmg(s16 ex, s16 ey, u8 count, u8 dmg)
{
    s16 dx = (px + 8) - (ex + 8);
    s16 dy = (py + 8) - (ey + 8);
    u32 dist = getApproximatedDistance(dx, dy);
    if (dist == 0) { dx = 1; dist = 1; }

    const s32 bvx = ((s32) dx * ESHOT_SPEED << 6) / (s32) dist;
    const s32 bvy = ((s32) dy * ESHOT_SPEED << 6) / (s32) dist;
    const s32 fx = (s32) (ex + 4) << 6, fy = (s32) (ey + 4) << 6;

    // rotação aproximada por cisalhamento: ~18° por passo (k = s/3)
    const s16 half = count / 2;
    for (s16 s = -half; s <= half; s++)
        spawnEShot(fx, fy, bvx - (bvy * s) / 3, bvy + (bvx * s) / 3, dmg);

    SFX_enemyShot();
}

void fireEnemySpread(s16 ex, s16 ey, u8 count)
{
    fireEnemySpreadDmg(ex, ey, count, ESHOT_DAMAGE);
}

void SHOTS_updateEnemy(void)
{
    for (u16 i = 0; i < MAX_ESHOTS; i++)
    {
        if (!eshots[i].active) continue;
        eshots[i].x += eshots[i].vx;
        eshots[i].y += eshots[i].vy;

        s16 sx = (s16) (eshots[i].x >> 6);
        s16 sy = (s16) (eshots[i].y >> 6);

        if (arenaActive ? ARENA_shotBlocked(sx,sy) :
            ((sx < INNER_MIN_X) || (sx > INNER_MAX_X - 7) ||
             (sy < INNER_MIN_Y) || (sy > INNER_MAX_Y - 7)))
        {
            eshots[i].active = FALSE;
            continue;
        }

        // colisão com o círculo do jogador (raio 7 + raio do tiro 3)
        s16 dx = (sx + 4) - (px + 8);
        s16 dy = (sy + 4) - (py + 8);
        // Reject distant bullets before squaring: int is 16-bit on 68000,
        // and a scrolling 512px world can overflow the old distance sum.
        if (dx >= -10 && dx <= 10 && dy >= -10 && dy <= 10 && dx * dx + dy * dy <= 100)
        {
            eshots[i].active = FALSE;
            damagePlayer(eshots[i].dmg);
        }
    }
}
