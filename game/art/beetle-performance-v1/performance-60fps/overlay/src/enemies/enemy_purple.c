// Comportamento COR ROXA — blindado: persegue e ergue escudo em ciclos.
// Enquanto blindado (e->shielded) os tiros são bloqueados (ver damageBox).
// timerA = duração sem escudo; timerB = duração com escudo (décimos de s).
// Pentágono (extra SUMMON): invoca lacaios enquanto está blindado.

#include "enemies/enemies.h"
#include "core/game.h"

void ENEMYPURPLE_update(Enemy *e, const EnemyDef *def)
{
    ENEMIES_chase(e, def->speedFp);

    // ciclo de escudo
    if (e->tA) e->tA=e->tA>4 ? e->tA-4 : 0;
    else
    {
        e->shielded = !e->shielded;
        e->tA = (e->shielded ? def->timerB : def->timerA) * fps / 10;
    }

    // Fortaleza: invoca um perseguidor rápido a cada ~1,5 s enquanto blindado
    if (def->extra == EXTRA_SUMMON && e->shielded)
    {
        if (e->tB) e->tB=e->tB>4 ? e->tB-4 : 0;
        else
        {
            ENEMIES_spawnAt(ENEMY_TRI_YEL, e->x, e->y);
            e->tB = 15 * fps / 10;
        }
    }
}
