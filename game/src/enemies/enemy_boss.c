// Escorpião: timed phase1, then a latched fury phase at12/25HP.
// Fury:0.8s announcement, approach, two warned charges,1.2s recovery,
//3s ranged pattern alternating wide/narrow fans; no periodic invulnerability.
#include "enemies/enemy_boss.h"
#include "actors/shots.h"
#include "core/game.h"
#include "system/audio/sfx.h"

#define BOSS_MINION ENEMY_TRI_YEL
#define BOSS_SHOT_DMG 13
#define BOSS_SHOT_COUNT 5
#define BOSS_DASH_FP 210

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

// Count live hunters before each request: repeated summons fill vacancies,
// never add a third hunter, including in training rooms with a larger cap.
static void summon(Enemy *e,const EnemyDef *def)
{
    u16 count=0;
    for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active && enemies[i].type==BOSS_MINION)count++;
    if(count>=2)return;
    ENEMIES_spawnAt(BOSS_MINION,e->x-12,e->y+def->size/2);
    count=0;
    for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active && enemies[i].type==BOSS_MINION)count++;
    if(count<2)ENEMIES_spawnAt(BOSS_MINION,e->x+def->size,e->y+def->size/2);
}

static void warnCharge(Enemy *e,s16 half)
{
    aim(e,half,BOSS_DASH_FP,+1);
    e->mode=BOSS_TELEGRAPH;e->retarget=7*fps/20; //0.35s, direction locked
}

static void fury(Enemy *e,const EnemyDef *def)
{
    const s16 half=def->size/2;
    switch(e->mode) {
        case BOSS_TRANSITION:
            // Local sprite palette flash; no room/ally palette changes.
            e->hitFlash=(e->retarget/(fps/10))&1 ? 2 : 0;
            if(e->retarget && --e->retarget)return;
            e->hitFlash=0;e->mode=BOSS_APPROACH;e->retarget=3*fps/5;
            return;
        case BOSS_APPROACH:
            aim(e,half,def->speedFp,+1);ENEMIES_integrate(e);
            if(e->retarget && --e->retarget)return;
            warnCharge(e,half);return;
        case BOSS_TELEGRAPH:
            if(e->retarget && --e->retarget)return;
            e->mode=BOSS_DASH;e->retarget=fps/2;return;
        case BOSS_DASH:
            ENEMIES_integrate(e);
            if(e->retarget && --e->retarget)return;
            if(!(e->tB&BOSS_SECOND_DASH)) {
                e->tB|=BOSS_SECOND_DASH;warnCharge(e,half);
            }else {
                e->tB&=~BOSS_SECOND_DASH;e->vx=e->vy=0;
                e->mode=BOSS_RECOVER;e->retarget=6*fps/5;
            }
            return;
        case BOSS_RECOVER:
            if(e->retarget && --e->retarget)return;
            e->mode=BOSS_RANGED;e->retarget=3*fps;e->fireTimer=0;return;
        case BOSS_RANGED:
            aim(e,half,def->speedFp,-1);ENEMIES_integrate(e);
            if(e->fireTimer)e->fireTimer--;
            else if(SHOTS_enemyHasRoom(BOSS_SHOT_COUNT)) {
                SHOTS_enemyTarget(px+8,py+8);
                fireEnemySpreadDmgWidth(e->x,e->y,BOSS_SHOT_COUNT,BOSS_SHOT_DMG,4,
                                       e->tB&BOSS_NARROW_FAN ? 6 : 2);
                e->tB^=BOSS_NARROW_FAN;e->fireTimer=6*fps/5;
            }
            if(e->retarget && --e->retarget)return;
            e->mode=BOSS_APPROACH;e->retarget=3*fps/5;return;
        default:
            e->mode=BOSS_APPROACH;e->retarget=3*fps/5;return;
    }
}

void ENEMYBOSS_update(Enemy *e, const EnemyDef *def)
{
    const s16 half = def->size / 2;
    e->tA++;                             // contador mestre (frames)

    if(!(e->tB&BOSS_FURY) && e->hp<=BOSS_FURY_HP) {
        e->tB=BOSS_FURY;e->mode=BOSS_TRANSITION;e->retarget=4*fps/5;
        e->vx=e->vy=0;e->stun=0;e->fireTimer=0;
        SFX_countPulse(TRUE);
    }
    e->shielded=!(e->tB&BOSS_FURY) && (e->tA%(15*fps)>=12*fps);
    if(e->tA && e->tA%(10*fps)==0)summon(e,def);
    if(e->tB&BOSS_FURY){fury(e,def);return;}

    const bool aggressive = (((e->tA / (u16) (4 * fps)) & 1) == 0);

    // recuo após colidir com o jogador (mesma mecânica dos demais)
    if (e->stun) { e->stun--; ENEMIES_integrate(e); return; }

    if (aggressive)
    {
        // sub-máquina de INVESTIDA: aproxima → telegrafa → dash reto
        switch (e->mode)
        {
            case BOSS_APPROACH:
                aim(e, half, def->speedFp, +1);
                ENEMIES_integrate(e);
                if (e->retarget) e->retarget--;
                else { aim(e, half, BOSS_DASH_FP, +1); e->mode = BOSS_TELEGRAPH; e->retarget = (u16) (3 * fps / 10); }
                break;

            case BOSS_TELEGRAPH:
                if (e->retarget) e->retarget--;     // parado, mira travada (~0,3 s)
                else { e->mode = BOSS_DASH; e->retarget = (u16) (5 * fps / 10); }
                break;

            case BOSS_DASH:
                ENEMIES_integrate(e);               // segue reto na direção travada (~0,5 s)
                if (e->retarget) e->retarget--;
                else { e->vx = 0; e->vy = 0; e->mode = BOSS_APPROACH; e->retarget = (u16) (6 * fps / 10); }
                break;
        }
    }
    else
    {
        // À DISTÂNCIA: recua e dispara rajadas; deixa a investida pronta p/ depois
        e->mode = BOSS_APPROACH; e->retarget = (u16) (6 * fps / 10);
        aim(e, half, def->speedFp, -1);
        ENEMIES_integrate(e);
        if (e->fireTimer) e->fireTimer--;
        else if (SHOTS_enemyHasRoom(BOSS_SHOT_COUNT))
        {
            // Wait for the whole fan; never erase live shots or clip one side
            // when an earlier volley or a minion occupies the enemy pool.
            SHOTS_enemyTarget(px+8,py+8);
            fireEnemySpreadDmg(e->x, e->y, BOSS_SHOT_COUNT, BOSS_SHOT_DMG, 4);
            e->fireTimer = (u16) (12 * fps / 10);   // ~1,2 s entre rajadas
        }
    }
}
