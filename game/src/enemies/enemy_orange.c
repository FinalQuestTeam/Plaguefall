// Comportamento COR LARANJA — investida: aproxima, telegrafa e dá dash reto.
// mode: 0 aproxima · 1 telegrafa (parado) · 2 investe. timerA = cooldown (0,1 s).
// Pentágono (extra TELEPORT): teleporta para perto do jogador antes de investir.

#include "enemies/enemies.h"
#include "core/game.h"
#include "actors/dinorah.h"

#define M_APPROACH   0
#define M_TELEGRAPH  1
#define M_DASH       2

#define DASH_SPEED_FP  200  // ~3,1 px/frame (mais rápido que o jogador por instantes)

// trava a velocidade rumo ao jogador na magnitude dada (26.6)
static void aimAt(Enemy *e, u16 speedFp)
{
    const s16 half = ENEMY_SIZE(e) / 2;
    s16 dx = (DINORAH_alive() && !e->aggroPlayer ? dinorahX+8 : px+8) - (e->x + half);
    s16 dy = (DINORAH_alive() && !e->aggroPlayer ? dinorahY+8 : py+8) - (e->y + half);
    u32 dist = getApproximatedDistance(dx, dy);
    if (dist == 0) dist = 1;
    // Authored worlds keep the divisor below32768 and the200fp dash
    // quotient safely within s16. DIVS retains the original signed truncation.
    e->vx = dist<=32767 ? divs((s32)dx*speedFp,dist) : (s16)(((s32)dx*speedFp)/(s32)dist);
    e->vy = dist<=32767 ? divs((s32)dy*speedFp,dist) : (s16)(((s32)dy*speedFp)/(s32)dist);
}

void ENEMYORANGE_update(Enemy *e, const EnemyDef *def)
{
    switch (e->mode)
    {
        case M_APPROACH:
            ENEMIES_chase(e, def->speedFp);
            if (e->tA) e->tA--;
            else
            {
                aimAt(e, DASH_SPEED_FP);         // mira e prepara o bote
                e->mode = M_TELEGRAPH;
                e->tB = 2 * fps / 10;            // ~0,2 s telegrafando
            }
            break;

        case M_TELEGRAPH:
            if (e->tB) e->tB--;
            else
            {
                // Meteoro: pisca para perto do jogador e remira
                if (def->extra == EXTRA_TELEPORT)
                {
                    e->x = px + ((random() & 1) ? 72 : -72);
                    e->y = py + ((random() & 1) ? 72 : -72);
                    e->fx = (s32) e->x << 6;
                    e->fy = (s32) e->y << 6;
                    aimAt(e, DASH_SPEED_FP);
                }
                e->mode = M_DASH;
                e->tA = 5 * fps / 10;            // ~0,5 s de investida
            }
            break;

        case M_DASH:
            ENEMIES_integrate(e);               // segue reto na direção travada
            if (e->tA) e->tA--;
            else
            {
                e->vx = 0; e->vy = 0;
                e->mode = M_APPROACH;
                e->tA = def->timerA * fps / 10; // cooldown entre investidas
            }
            break;
    }
}
