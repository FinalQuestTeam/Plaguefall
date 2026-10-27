// Engine dos inimigos: vetor global, spawn, morte (drop/sangue/divisão),
// movimento (perseguição + integração 26.6), separação anti-empilhamento e o
// dano recebido (tiro, raio em cadeia, bomba). Os comportamentos por cor ficam
// em enemy_*.c; os dados de cada tipo (EnemyDef) em defs/*.c.

#include "enemies/enemies.h"
#include "enemies/enemy_boss.h"
#include "actors/player.h"
#include "actors/dinorah.h"
#include "actors/shots.h"          // ICE_FREEZE_SEC / FIRE_BURN_SEC / FIRE_TICK_SEC
#include "core/game.h"
#include "levels/levels.h"
#include "levels/campaign_resistance.h"
#include "items/items.h"
#include "system/video/chainfx.h"
#include "system/video/blood.h"
#include "system/video/combatgfx.h"
#include "levels/test.h"

static void enemyDie(Enemy *e);     // fwd: usado pela queimadura antes de definido

Enemy enemies[MAX_ENEMIES];

// alvo (centro) da perseguição: por padrão o jogador; o objetivo PROTEGER aponta
// para o NPC. Atualizado por quadro em flow.c antes de ENEMIES_update.
s16 chaseX, chaseY;
void ENEMIES_setChaseTarget(s16 cx, s16 cy) { chaseX = cx; chaseY = cy; }

static u8 aggroSplit;       // PROTEGER: 1/aggroSplit dos inimigos persegue o jogador
void ENEMIES_setAggroSplit(u8 n) { aggroSplit = n; }

// configurações dos inimigos — uma por arquivo em enemies/defs/
extern const EnemyDef
    ENEMYDEF_sq_red,  ENEMYDEF_sq_yellow,  ENEMYDEF_sq_purple,  ENEMYDEF_sq_orange,
    ENEMYDEF_tri_red, ENEMYDEF_tri_yellow, ENEMYDEF_tri_purple, ENEMYDEF_tri_orange,
    ENEMYDEF_pen_red, ENEMYDEF_pen_yellow, ENEMYDEF_pen_purple, ENEMYDEF_pen_orange,
    ENEMYDEF_dummy,   ENEMYDEF_target,     ENEMYDEF_boss;

const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES] =
{
    &ENEMYDEF_sq_red,   &ENEMYDEF_sq_yellow,   &ENEMYDEF_sq_purple,   &ENEMYDEF_sq_orange,
    &ENEMYDEF_tri_red,  &ENEMYDEF_tri_yellow,  &ENEMYDEF_tri_purple,  &ENEMYDEF_tri_orange,
    &ENEMYDEF_pen_red,  &ENEMYDEF_pen_yellow,  &ENEMYDEF_pen_purple,  &ENEMYDEF_pen_orange,
    &ENEMYDEF_dummy,    &ENEMYDEF_target,      &ENEMYDEF_boss,
};

u16 ENEMIES_activeCount(void)
{
    u16 c = 0;
    for (u16 i = 0; i < MAX_ENEMIES; i++) if (enemies[i].active) c++;
    return c;
}

void ENEMIES_clear(void)
{
    memset(enemies, 0, sizeof(enemies));
    COMBATGFX_clear();
    CHAINFX_reset();        // sem arcos de raio pendentes ao (re)carregar
}

// inicializa um slot já escolhido, na posição (x,y)
static void initEnemy(Enemy *e, u8 type, s16 x, s16 y)
{
    memset(e, 0, sizeof(Enemy));
    e->x = x;
    e->y = y;
    e->fx = (s32) x << 6;
    e->fy = (s32) y << 6;
    e->type = type;
    e->hp = ENEMY_DEFS[type]->hp;
    e->fireTimer = ENEMY_CD / 2 + (random() % fps);
    // aggro dividido (PROTEGER): parte dos inimigos persegue o jogador, não o aliado
    e->aggroPlayer = aggroSplit && ((random() % aggroSplit) == 0);
    e->active = TRUE;
}

void ENEMIES_spawnAt(u8 type, s16 x, s16 y)
{
    if (ENEMIES_activeCount() >= (LEVEL_current()->enemyCap ? LEVEL_current()->enemyCap : ENEMY_CAP)) return;     // teto: espera abrir vaga

    const s16 size = ENEMY_DEFS[type]->size;
    // mantém dentro da arena
    if (x < INNER_MIN_X) x = INNER_MIN_X;
    if (x > INNER_MAX_X - (size - 1)) x = INNER_MAX_X - (size - 1);
    if (y < INNER_MIN_Y) y = INNER_MIN_Y;
    if (y > INNER_MAX_Y - (size - 1)) y = INNER_MAX_Y - (size - 1);

    if (ARENA_blocked(x, y, size, size)) return;
    for (u16 i = 0; i < MAX_ENEMIES; i++)
        if (!enemies[i].active) { initEnemy(&enemies[i], type, x, y); return; }
}

void ENEMIES_trySpawn(const u8 *types, u8 typeCount)
{
    if (ENEMIES_activeCount() >= (LEVEL_current()->enemyCap ? LEVEL_current()->enemyCap : ENEMY_CAP)) return;     // teto: espera abrir vaga

    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        if (enemies[i].active) continue;

        const u8 type = types[random() % typeCount];
        const s16 size = ENEMY_DEFS[type]->size;

        // Sample the active sector directly, including the distant half of
        // a2048px world. Rejection sampling the entire map thins the waves.
        s16 minX=INNER_MIN_X,maxX=INNER_MAX_X-(size-1);
        if(LEVEL_current()->route) {
            const s16 focus=DINORAH_alive() ? dinorahX : px;
            if(minX<focus-136)minX=focus-136;
            if(maxX>focus+216)maxX=focus+216;
        }
        // procura posição a uma distância razoável do jogador
        for (u16 attempt = 0; attempt < 12; attempt++)
        {
            s16 x = minX + (random() % (maxX-minX+1));
            s16 y = INNER_MIN_Y + (random() % (INNER_MAX_Y - INNER_MIN_Y - (size - 1)));
            if(LEVEL_current()->route) {
                // Spawn in the current combat sector, never on either actor
                // or the landing. Retire distant pursuers below as we advance.
                const s16 focus=DINORAH_alive() ? dinorahX : px;
                if(x<focus-136 || x>focus+216)continue;
                const ArenaRect *r=&LEVEL_current()->route->exit;
                if(x<r->x+r->w && x+size>r->x && y<r->y+r->h && y+size>r->y)continue;
                if(DINORAH_alive() && getApproximatedDistance(x-dinorahX,y-dinorahY)<64)continue;
            }
            if (getApproximatedDistance(x - px, y - py) < 64) continue;
            if (ARENA_blocked(x, y, size, size)) continue;

            initEnemy(&enemies[i], type, x, y);
            return;
        }
        return;     // sem posição boa neste frame; tenta no próximo período
    }
}

// integra vx/vy (26.6) e mantém o inimigo dentro da arena
void ENEMIES_integrate(Enemy *e)
{
    const s16 size = ENEMY_SIZE(e);

    ARENA_move(&e->fx, &e->fy, e->vx*ENEMY_UPDATE_STEP(e), e->vy*ENEMY_UPDATE_STEP(e), size);

    e->x = (s16) (e->fx >> 6);
    e->y = (s16) (e->fy >> 6);
}

void ENEMIES_chase(Enemy *e, u16 speedFp)
{
    const u16 step=ENEMY_UPDATE_STEP(e);
    const s16 half = ENEMY_SIZE(e) / 2;

    // lentidão aplicada por elementos da fase (ex.: lama)
    if (e->slowPct) speedFp = divu((u32) speedFp * (100 - e->slowPct), 100);

    // recuando após colisão: mantém a velocidade de recuo
    if (e->stun)
    {
        e->stun=e->stun>step ? e->stun-step : 0;
        if (e->stun == 0) e->retarget = 0;  // ao acabar, volta a mirar já
        ENEMIES_integrate(e);
        return;
    }

    // recalcula a direção periodicamente
    if (e->retarget) e->retarget=e->retarget>step ? e->retarget-step : 0;
    else
    {
        // alvo: o aliado (chaseX/Y) ou o JOGADOR (aggro dividido no PROTEGER)
        const s16 tx = e->aggroPlayer ? (s16) (px + 8) : chaseX;
        const s16 ty = e->aggroPlayer ? (s16) (py + 8) : chaseY;
        s16 dx = tx - (e->x + half);
        s16 dy = ty - (e->y + half);
        u32 dist = getApproximatedDistance(dx, dy);
        if (dist == 0) dist = 1;
        // Arena distances are <512 and speeds <=90: the signed quotient
        // fits 16 bits, so DIVS preserves C truncation without a software divide.
        e->vx = divs((s32) dx * speedFp, (s16) dist);
        e->vy = divs((s32) dy * speedFp, (s16) dist);
        e->retarget = RETARGET_FRAMES;
    }

    ENEMIES_integrate(e);
}

// recíproco fixo (64/d) para normalizar (dx,dy) SEM divisão. Base 64 (e não 256)
// para os produtos caberem em 16 bits → o gcc emite muls.w (~70 ciclos) em vez do
// __mulsi3 (~250). Índice = distância em px, sempre < 32 (maior minDist = 24).
static const u8 SEP_RECIP[32] =
{
     0, 64, 32, 21, 16, 13, 11,  9,  8,  7,  6,  6,  5,  5,  5,  4,
     4,  4,  4,  3,  3,  3,  3,  3,  3,  3,  2,  2,  2,  2,  2,  2,
};

// Incremental separation: each body receives its accumulated repulsion once
// every four frames. Four cohorts bound the worst per-frame work. The 2x
// displacement preserves the previous per-second displacement cap. Compact
// bodies and eight push directions avoid repeated lookups and normalization.
__attribute__((noinline)) static void ENEMIES_separate(void)
{
    static u8 tick;tick++;
    typedef struct {s16 x,y;u8 slot,half;} Body;
    Body bodies[MAX_ENEMIES],*end=bodies;
    for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active) {
        const Enemy *e=&enemies[i];const u16 half=ENEMY_SIZE(e)/2;
        *end++=(Body){e->x+half,e->y+half,i,half};
    }
    for(Body *a=bodies;a<end;a++) {
        if((a->slot+tick)&3)continue;
        if(ENEMYBOSS_stationary(&enemies[a->slot]))continue;
        s16 pushX=0,pushY=0;
        for(Body *b=bodies;b<end;b++) {
            if(a==b)continue;
            s16 dx=b->x-a->x,dy=b->y-a->y;
            const s16 minDist=((a->half+b->half)*SEP_MIN_NUM)>>SEP_MIN_SHIFT;
            s16 ax=dx<0?-dx:dx,ay=dy<0?-dy:dy;
            if(ax>=minDist || ay>=minDist)continue;
            s16 dist=ax>=ay ? ax+(ay>>1) : ay+(ax>>1);
            if(!dist) {
                const u8 lo=a->slot<b->slot?a->slot:b->slot,hi=a->slot<b->slot?b->slot:a->slot;
                ax=1+(lo&3);ay=1+(hi&3);
                dx=a->slot<b->slot?ax:-ax;dy=a->slot<b->slot?ay:-ay;
                dist=ax>=ay?ax+(ay>>1):ay+(ax>>1);
            } else if(dist>=minDist)continue;
            s16 push=(minDist-dist)*SEP_STRENGTH;
            if(push>SEP_MAX)push=SEP_MAX;
            s16 vx=0,vy=0;
            if(ax>=ay*2)vx=push;
            else if(ay>=ax*2)vy=push;
            else vx=vy=(push*3)>>2;
            if(dx<0)vx=-vx;if(dy<0)vy=-vy;
            pushX-=vx;pushY-=vy;
        }
        if(!(pushX|pushY))continue;
        if(pushX>SEP_MAX)pushX=SEP_MAX;else if(pushX<-SEP_MAX)pushX=-SEP_MAX;
        if(pushY>SEP_MAX)pushY=SEP_MAX;else if(pushY<-SEP_MAX)pushY=-SEP_MAX;
        Enemy *e=&enemies[a->slot];
        ARENA_move(&e->fx,&e->fy,pushX*2,pushY*2,a->half*2);
        e->x=e->fx>>6;e->y=e->fy>>6;
    }
}

// empurra o inimigo PARA LONGE de (fromX,fromY) a 2x a velocidade, com stun.
// Reusado no contato com o jogador, no recuo ao encostar no aliado (PROTEGER) e
// na onda de choque da antena. Fixos (speedFp 0) não recuam. Sem divisão (tabela).
void ENEMIES_knockbackFrom(Enemy *e, s16 fromX, s16 fromY)
{
    const EnemyDef *def = ENEMY_DEF(e);
    if (def->speedFp == 0) return;
    // Fury has its own warnings and recovery. Player contact cannot cancel
    // the combo or push the boss out of its promised stationary opening.
    if(e->type==ENEMY_BOSS && (e->tB&BOSS_FURY))return;

    const s16 half = ENEMY_SIZE(e) / 2;
    s16 dx = (e->x + half) - fromX;
    s16 dy = (e->y + half) - fromY;
    s16 adx = dx < 0 ? -dx : dx;
    s16 ady = dy < 0 ? -dy : dy;
    s16 dist = (adx >= ady) ? (s16) (adx + (ady >> 1)) : (s16) (ady + (adx >> 1));
    if (dist == 0) { dx = 1; dist = 1; }
    else if (dist > 31) dist = 31;              // limite do índice da tabela

    const u16 kbSpeed = 2 * def->speedFp;       // recua a 2x a velocidade
    const s16 k = (s16) (kbSpeed * SEP_RECIP[dist]);
    e->vx = (s16) (((s32) dx * k) >> 6);
    e->vy = (s16) (((s32) dy * k) >> 6);
    e->stun = fps / 3;
    e->mode = 0;                                // cancela dash em curso
}

static u16 updateStaticTraining(void)
{
    u16 dead=0;
    for(u16 i=0;i<MAX_ENEMIES;i++) {
        Enemy *e=&enemies[i];if(!e->active)continue;
        if(e->hitFlash)e->hitFlash--;
        if(e->burnFlash)e->burnFlash--;
        if(e->burn) {
            e->burn--;
            if(e->burnTick)e->burnTick--;
            if(!e->burnTick) {
                e->burnTick=FIRE_TICK_SEC*fps;
                if(!--e->hp){enemyDie(e);dead++;continue;}
                e->burnFlash=HIT_FLASH_FRAMES;
            }
        }
        if(e->frozen)e->frozen--;
    }
    return dead;
}
__attribute__((noinline)) u16 ENEMIES_update(void)
{
    if(currentLevel==0 && TEST_staticEnemies())return updateStaticTraining();
    static u8 aiTick;aiTick++;
    u16 burnKills = 0;
    const bool routeActive=LEVEL_current()->route!=NULL;

    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;
        if(routeActive) {
            const s16 focus=DINORAH_alive() ? dinorahX : px;
            if((e->x<focus-240 || e->x>focus+400) && (e->x+ENEMY_SIZE(e)<cameraX || e->x>cameraX+320)) {
                e->active=FALSE;continue; // out of the active sector; no kill/drop
            }
        }

        const EnemyDef *def = ENEMY_DEF(e);
        const u16 step=ENEMY_UPDATE_STEP(e);
        if(step==4 && ((i+aiTick)&3))continue;

        if (e->hitFlash) e->hitFlash=e->hitFlash>step ? e->hitFlash-step : 0;     // decai o brilho branco do dano
        if (e->burnFlash) e->burnFlash=e->burnFlash>step ? e->burnFlash-step : 0;   // decai o pulso vermelho do fogo

        // queimadura (fogo): 1 de dano a cada FIRE_TICK_SEC, por FIRE_BURN_SEC
        if (e->burn)
        {
            e->burn=e->burn>step ? e->burn-step : 0;
            if (e->burnTick) e->burnTick=e->burnTick>step ? e->burnTick-step : 0;
            if (e->burnTick == 0)
            {
                e->burnTick = FIRE_TICK_SEC * fps;
                if (--e->hp == 0) { enemyDie(e); burnKills++; continue; }
                e->burnFlash = HIT_FLASH_FRAMES;    // pulso vermelho: tomou dano do fogo
            }
        }

        // congelado (gelo): parado, sem comportamento nem dano de contato
        if (e->frozen) { e->frozen=e->frozen>step ? e->frozen-step : 0; continue; }

        def->behavior(e, def);      // comportamento pela cor (via config)

        // encostar no jogador causa dano (respeitando a invencibilidade);
        // inimigos com dano 0 (ex.: dummy) não afetam o jogador
        const s16 size = def->size;
        if (def->contactDmg &&
            (e->x < px + 16) && (e->x + size > px) &&
            (e->y < py + 16) && (e->y + size > py))
        {
            damagePlayer(def->contactDmg);
            if (gameOver) return burnKills;

            // inimigos que se movem recuam após a colisão (evita dano contínuo);
            // os fixos (speedFp 0, ex.: Torreão) não recuam
            ENEMIES_knockbackFrom(e, px + 8, py + 8);
        }
    }

    ENEMIES_separate();
    return burnKills;
}

#define BOMB_BOSS_DMG   4       // dano da bomba no chefe (não o mata)

u16 ENEMIES_killAll(void)
{
    u16 count = 0;
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        if (!enemies[i].active) continue;

        // Mission transmitters survive bombs; ordinary Torreoes, including
        // reinforcements reusing a completed target's slot, remain vulnerable.
        if (CAMPAIGN_RESISTANCE_priorityEnemy(i)) continue;

        // CHEFE resiste à bomba: não morre; leva um dano fixo (se não blindado)
        if (enemies[i].type == ENEMY_BOSS)
        {
            if (!enemies[i].shielded)
                enemies[i].hp = (enemies[i].hp > BOMB_BOSS_DMG)
                              ? (u8) (enemies[i].hp - BOMB_BOSS_DMG) : 1;
            continue;
        }

        COMBATGFX_spawn(enemies[i].type,enemies[i].x,enemies[i].y);
        BLOOD_splat(enemies[i].x+ENEMY_SIZE(&enemies[i])/2,enemies[i].y+ENEMY_SIZE(&enemies[i])/2);
        enemies[i].active = FALSE;      // sem drop: a bomba não sorteia itens
        count++;
    }
    return count;
}

// truque do pentágono amarelo: ao morrer, gera 2 perseguidores rápidos menores
static void splitInto(Enemy *e)
{
    const s16 cx = e->x + ENEMY_SIZE(e) / 2, cy = e->y + ENEMY_SIZE(e) / 2;
    ENEMIES_spawnAt(ENEMY_TRI_YEL, cx - 16, cy);
    ENEMIES_spawnAt(ENEMY_TRI_YEL, cx + 4, cy);
}

// morte comum: divide (se for o caso), desativa, deixa a poça e sorteia o drop
static void enemyDie(Enemy *e)
{
    const s16 half = ENEMY_SIZE(e) / 2;
    COMBATGFX_spawn(e->type,e->x,e->y);
    if (e->type == ENEMY_BOSS) bossDefeated = TRUE;     // chefe morto → encerra a fase 16
    if (!TEST_staticEnemies() && ENEMY_DEF(e)->extra == EXTRA_SPLIT) splitInto(e);
    e->active = FALSE;
    BLOOD_splat(e->x + half, e->y + half);      // poça de sangue verde no local
    if(!TEST_staticEnemies() && (currentLevel || testStage!=6))ITEMS_tryDrop(e->x + half, e->y + half, e->type);
}

bool ENEMIES_testKill(u16 index)
{
    if(currentLevel || index>=MAX_ENEMIES || !enemies[index].active)return FALSE;
    enemyDie(&enemies[index]);return TRUE;
}

u16 ENEMIES_damageBox(s16 x, s16 y, s16 w, s16 h, u8 status)
{
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;

        const s16 size = ENEMY_SIZE(e);
        if ((x < e->x + size) && (x + w > e->x) &&
            (y < e->y + size) && (y + h > e->y))
        {
            // escudo erguido: o tiro é bloqueado (consumido, sem dano)
            if (e->shielded) return ENEMY_HIT_DAMAGED;

            if (--e->hp == 0) { enemyDie(e); return ENEMY_HIT_KILLED; }

            e->hitFlash = HIT_FLASH_FRAMES;     // brilho branco: sobreviveu ao dano

            // sobreviveu: aplica o status do modo de tiro (gelo/fogo)
            if (status == ENEMY_STATUS_FREEZE)
                e->frozen = ICE_FREEZE_SEC * fps;
            else if (status == ENEMY_STATUS_BURN)
            {
                e->burn = FIRE_BURN_SEC * fps;
                e->burnTick = FIRE_TICK_SEC * fps;
            }
            return ENEMY_HIT_DAMAGED;
        }
    }
    return ENEMY_HIT_NONE;
}

u16 ENEMIES_chainDamage(s16 cx, s16 cy, u8 maxTargets, u16 range)
{
    u16 kills = 0;
    u8 hits = 0;
    for (u16 i = 0; (i < MAX_ENEMIES) && (hits < maxTargets); i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active || e->shielded) continue;

        const s16 half = ENEMY_SIZE(e) / 2;
        if (getApproximatedDistance((e->x + half) - cx, (e->y + half) - cy) > range) continue;

        hits++;
        CHAINFX_add(cx, cy, e->x + half, e->y + half);  // arco elétrico até o alvo
        if (--e->hp == 0) { enemyDie(e); kills++; }
        else e->hitFlash = HIT_FLASH_FRAMES;            // brilho branco se sobreviveu
    }
    return kills;
}
