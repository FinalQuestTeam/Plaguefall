// Projéteis dos inimigos: disparo mirado no jogador (simples e em leque) e
// atualização/colisão com o círculo do jogador.

#include "actors/shots.h"
#include "core/game.h"
#include "actors/player.h"
#include "actors/dinorah.h"
#include "system/audio/sfx.h"
#include "levels/levels.h"
#include "levels/test.h"

static s16 shotTargetX,shotTargetY;
void SHOTS_enemyTarget(s16 x,s16 y){shotTargetX=x;shotTargetY=y;}
// cria um projétil inimigo em (fx, fy) 26.6 com velocidade dada (26.6) e `dmg`
static void spawnEShot(s32 fx, s32 fy, s32 vx, s32 vy, u8 dmg, u8 style)
{
    const u16 cap = currentLevel==0 ? TEST_shotLimit() : (LEVEL_current()->shotCap ? LEVEL_current()->shotCap : MAX_ESHOTS);
    for (u16 i = 0; i < cap; i++)
    {
        if (eshots[i].active) continue;
        eshots[i].x = fx;
        eshots[i].y = fy;
        eshots[i].vx = vx;
        eshots[i].vy = vy;
        eshots[i].dmg = dmg;
        eshots[i].mode = style;
        eshots[i].active = TRUE;
        eshots[i].renderPose=0;
        return;
    }
}

static s32 aimedVelocity(s16 delta,u32 distance)
{
    const s32 numerator=(s32)delta*(ESHOT_SPEED*64);
    // The normalized two-pixel velocity fits s16. Retain the long-divide
    // fallback for a divisor outside the signed hardware instruction range.
    return distance<=32767 ? divs(numerator,distance) : numerator/(s32)distance;
}
void fireEnemyShot(s16 ex, s16 ey, u8 style)
{
    s16 dx = shotTargetX - (ex + 8);
    s16 dy = shotTargetY - (ey + 8);
    u32 dist = getApproximatedDistance(dx, dy);
    if (dist == 0) dist = 1;

    spawnEShot((s32) (ex + 4) << 6, (s32) (ey + 4) << 6,
               aimedVelocity(dx,dist),
               aimedVelocity(dy,dist), ESHOT_DAMAGE, style);
    SFX_enemyShot();
}

void fireEnemySpreadDmg(s16 ex, s16 ey, u8 count, u8 dmg, u8 style)
{
    s16 dx = shotTargetX - (ex + 8);
    s16 dy = shotTargetY - (ey + 8);
    u32 dist = getApproximatedDistance(dx, dy);
    if (dist == 0) { dx = 1; dist = 1; }

    const s32 bvx = aimedVelocity(dx,dist);
    const s32 bvy = aimedVelocity(dy,dist);
    const s32 fx = (s32) (ex + 4) << 6, fy = (s32) (ey + 4) << 6;

    // rotação aproximada por cisalhamento: ~18° por passo (k = s/3)
    const s16 half = count / 2;
    for (s16 s = -half; s <= half; s++)
        spawnEShot(fx, fy, bvx - (bvy * s) / 3, bvy + (bvx * s) / 3, dmg, style);

    SFX_enemyShot();
}

void fireEnemySpread(s16 ex, s16 ey, u8 count, u8 style)
{
    fireEnemySpreadDmg(ex, ey, count, ESHOT_DAMAGE, style);
}

__attribute__((noinline)) void SHOTS_updateEnemy(void)
{
    bool allyAlive=DINORAH_alive();
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

        if(allyAlive) {
            const s16 ax=sx+4-dinorahX-8,ay=sy+4-dinorahY-8;
            if(ax>=-10 && ax<=10 && ay>=-10 && ay<=10 && ax*ax+ay*ay<=100) {
                eshots[i].active=FALSE;DINORAH_damage(eshots[i].dmg);allyAlive=DINORAH_alive();continue;
            }
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
