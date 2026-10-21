// Comportamento do CHEFE (Escorpiao) — inimigo bônus da última fase.
//  - alterna a cada 4 s entre AGRESSIVO e À DISTÂNCIA;
//  - AGRESSIVO: aproxima, telegrafa e dá DASH reto (investida) repetidamente;
//  - À DISTÂNCIA: recua e dispara rajadas de 5 tiros;
//  - fica blindado (invulnerável) 3 s a cada ciclo de 15 s;
//  - invoca 2 lacaios a cada 10 s.
// e->tA = contador mestre (frames desde o nascimento); e->mode/retarget = a
// sub-máquina do dash na fase agressiva.

#include "enemies/enemies.h"
#include "actors/shots.h"
#include "core/game.h"

#define BOSS_MINION     ENEMY_TRI_YEL   // lacaios invocados
#define BOSS_SHOT_DMG   13
#define BOSS_SHOT_COUNT 5
#define BOSS_DASH_FP    210             // velocidade da investida (rápida)

#define B_APPROACH  0
#define B_TELEGRAPH 1
#define B_DASH      2

// trava a velocidade na direção do jogador (sinal +1 avança, -1 recua)
static void aim(Enemy *e, s16 half, u16 speedFp, s16 sign)
{
    s16 dx = (px + 8) - (e->x + half);
    s16 dy = (py + 8) - (e->y + half);
    u32 dist = getApproximatedDistance(dx, dy);
    if (dist == 0) dist = 1;
    e->vx = (s16) ((sign * (s32) dx * speedFp) / (s32) dist);
    e->vy = (s16) ((sign * (s32) dy * speedFp) / (s32) dist);
}

void ENEMYBOSS_update(Enemy *e, const EnemyDef *def)
{
    const s16 half = def->size / 2;
    e->tA++;                             // contador mestre (frames)

    // blindado (invulnerável) nos últimos 3 s de cada ciclo de 15 s
    e->shielded = ((e->tA % (u16) (15 * fps)) >= (u16) (12 * fps));

    // invoca 2 lacaios a cada 10 s (nas laterais)
    if (e->tA > 0 && (e->tA % (u16) (10 * fps)) == 0)
    {
        ENEMIES_spawnAt(BOSS_MINION, e->x - 12, e->y + half);
        ENEMIES_spawnAt(BOSS_MINION, e->x + def->size, e->y + half);
    }

    const bool aggressive = (((e->tA / (u16) (4 * fps)) & 1) == 0);

    // recuo após colidir com o jogador (mesma mecânica dos demais)
    if (e->stun) { e->stun--; ENEMIES_integrate(e); return; }

    if (aggressive)
    {
        // sub-máquina de INVESTIDA: aproxima → telegrafa → dash reto
        switch (e->mode)
        {
            case B_APPROACH:
                aim(e, half, def->speedFp, +1);
                ENEMIES_integrate(e);
                if (e->retarget) e->retarget--;
                else { aim(e, half, BOSS_DASH_FP, +1); e->mode = B_TELEGRAPH; e->retarget = (u16) (3 * fps / 10); }
                break;

            case B_TELEGRAPH:
                if (e->retarget) e->retarget--;     // parado, mira travada (~0,3 s)
                else { e->mode = B_DASH; e->retarget = (u16) (5 * fps / 10); }
                break;

            case B_DASH:
                ENEMIES_integrate(e);               // segue reto na direção travada (~0,5 s)
                if (e->retarget) e->retarget--;
                else { e->vx = 0; e->vy = 0; e->mode = B_APPROACH; e->retarget = (u16) (6 * fps / 10); }
                break;
        }
    }
    else
    {
        // À DISTÂNCIA: recua e dispara rajadas; deixa a investida pronta p/ depois
        e->mode = B_APPROACH; e->retarget = (u16) (6 * fps / 10);
        aim(e, half, def->speedFp, -1);
        ENEMIES_integrate(e);
        if (e->fireTimer) e->fireTimer--;
        else
        {
            fireEnemySpreadDmg(e->x, e->y, BOSS_SHOT_COUNT, BOSS_SHOT_DMG);
            e->fireTimer = (u16) (12 * fps / 10);   // ~1,2 s entre rajadas
        }
    }
}
