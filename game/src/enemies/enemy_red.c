// Comportamento COR VERMELHA — atirador: dispara mirado no jogador.
// Quadrado: fixo. Triângulo: persegue enquanto atira (agressivo).
// Pentágono: leque de tiros (extra SPREAD). Cadência vem de def->timerA.

#include "enemies/enemies.h"
#include "actors/shots.h"
#include "core/game.h"
#include "actors/player.h"
#include "actors/dinorah.h"

void ENEMYRED_update(Enemy *e, const EnemyDef *def)
{
    if (def->speedFp > 0) ENEMIES_chase(e, def->speedFp);   // formas que se movem

    if (e->fireTimer) e->fireTimer--;
    else
    {
        SHOTS_enemyTarget(DINORAH_alive() && !e->aggroPlayer ? dinorahX+8 : px+8,
                          DINORAH_alive() && !e->aggroPlayer ? dinorahY+8 : py+8);
        const u8 style=e->type==ENEMY_SQ_RED ? 1 : e->type==ENEMY_TRI_RED ? 2 : 3;
        if (def->extra == EXTRA_SPREAD) fireEnemySpread(e->x, e->y, 3, style);
        else fireEnemyShot(e->x, e->y, style);
        e->fireTimer = def->timerA * fps / 10;              // décimos de s -> frames
    }
}
