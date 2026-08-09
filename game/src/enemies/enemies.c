// Engine dos inimigos: vetor global, spawn, morte (drop/sangue/divisão),
// movimento (perseguição + integração 26.6), separação anti-empilhamento e o
// dano recebido (tiro, raio em cadeia, bomba). Os comportamentos por cor ficam
// em enemy_*.c; os dados de cada tipo (EnemyDef) em defs/*.c.

#include "enemies/enemies.h"
#include "actors/player.h"
#include "actors/shots.h"          // ICE_FREEZE_SEC / FIRE_BURN_SEC / FIRE_TICK_SEC
#include "core/game.h"
#include "items/items.h"
#include "system/video/chainfx.h"
#include "system/video/blood.h"

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
    if (ENEMIES_activeCount() >= ENEMY_CAP) return;     // teto: espera abrir vaga

    const s16 size = ENEMY_DEFS[type]->size;
    // mantém dentro da arena
    if (x < INNER_MIN_X) x = INNER_MIN_X;
    if (x > INNER_MAX_X - (size - 1)) x = INNER_MAX_X - (size - 1);
    if (y < INNER_MIN_Y) y = INNER_MIN_Y;
    if (y > INNER_MAX_Y - (size - 1)) y = INNER_MAX_Y - (size - 1);

    for (u16 i = 0; i < MAX_ENEMIES; i++)
        if (!enemies[i].active) { initEnemy(&enemies[i], type, x, y); return; }
}

void ENEMIES_trySpawn(const u8 *types, u8 typeCount)
{
    if (ENEMIES_activeCount() >= ENEMY_CAP) return;     // teto: espera abrir vaga

    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        if (enemies[i].active) continue;

        const u8 type = types[random() % typeCount];
        const s16 size = ENEMY_DEFS[type]->size;

        // procura posição a uma distância razoável do jogador
        for (u16 attempt = 0; attempt < 12; attempt++)
        {
            s16 x = INNER_MIN_X + (random() % (INNER_MAX_X - INNER_MIN_X - (size - 1)));
            s16 y = INNER_MIN_Y + (random() % (INNER_MAX_Y - INNER_MIN_Y - (size - 1)));
            if (getApproximatedDistance(x - px, y - py) < 56) continue;

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

    e->fx += e->vx;
    e->fy += e->vy;

    if (e->fx < (s32) INNER_MIN_X << 6) e->fx = (s32) INNER_MIN_X << 6;
    if (e->fx > (s32) (INNER_MAX_X - (size - 1)) << 6) e->fx = (s32) (INNER_MAX_X - (size - 1)) << 6;
    if (e->fy < (s32) INNER_MIN_Y << 6) e->fy = (s32) INNER_MIN_Y << 6;
    if (e->fy > (s32) (INNER_MAX_Y - (size - 1)) << 6) e->fy = (s32) (INNER_MAX_Y - (size - 1)) << 6;

    e->x = (s16) (e->fx >> 6);
    e->y = (s16) (e->fy >> 6);
}

void ENEMIES_chase(Enemy *e, u16 speedFp)
{
    const s16 half = ENEMY_SIZE(e) / 2;

    // lentidão aplicada por elementos da fase (ex.: lama)
    if (e->slowPct) speedFp = (u16) (((u32) speedFp * (100 - e->slowPct)) / 100);

    // recuando após colisão: mantém a velocidade de recuo
    if (e->stun)
    {
        e->stun--;
        if (e->stun == 0) e->retarget = 0;  // ao acabar, volta a mirar já
        ENEMIES_integrate(e);
        return;
    }

    // recalcula a direção periodicamente
    if (e->retarget) e->retarget--;
    else
    {
        // alvo: o aliado (chaseX/Y) ou o JOGADOR (aggro dividido no PROTEGER)
        const s16 tx = e->aggroPlayer ? (s16) (px + 8) : chaseX;
        const s16 ty = e->aggroPlayer ? (s16) (py + 8) : chaseY;
        s16 dx = tx - (e->x + half);
        s16 dy = ty - (e->y + half);
        u32 dist = getApproximatedDistance(dx, dy);
        if (dist == 0) dist = 1;
        e->vx = (s16) (((s32) dx * speedFp) / (s32) dist);
        e->vy = (s16) (((s32) dy * speedFp) / (s32) dist);
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

// Separação anti-empilhamento: cada par de inimigos ativos cujos centros estão
// mais perto que a distância mínima (derivada dos tamanhos → permite sobreposição
// parcial, nunca total) recebe um pequeno empurrão em direções opostas. O total
// por inimigo é limitado a SEP_MAX por quadro → afastamento lento. Aplica-se a
// TODOS os inimigos (inclusive os atiradores parados). SEM divisões no laço.
static void ENEMIES_separate(void)
{
    // gentil: roda em quadros alternados (30 Hz) — metade do custo O(N²) e o
    // afastamento lento não precisa de precisão a 60 Hz.
    static u8 tick = 0;
    if (++tick & 1) return;

    s32 pushX[MAX_ENEMIES];
    s32 pushY[MAX_ENEMIES];
    memset(pushX, 0, sizeof(pushX));
    memset(pushY, 0, sizeof(pushY));

    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *a = &enemies[i];
        if (!a->active) continue;

        const s16 ha = ENEMY_SIZE(a) / 2;
        const s16 acx = a->x + ha, acy = a->y + ha;

        for (u16 j = i + 1; j < MAX_ENEMIES; j++)
        {
            Enemy *b = &enemies[j];
            if (!b->active) continue;

            const s16 hb = ENEMY_SIZE(b) / 2;
            s16 dx = (b->x + hb) - acx;
            s16 dy = (b->y + hb) - acy;

            // distância mínima entre os centros (sobreposição parcial). Fração
            // com denominador potência de 2 → mult + shift, SEM divisão no laço.
            const s16 minDist = (s16) (((ha + hb) * SEP_MIN_NUM) >> SEP_MIN_SHIFT);

            // caixa + distância aproximada INLINE (max + min/2), sem chamar o
            // getApproximatedDistance (caro no 68000). Rejeita a maioria dos pares.
            s16 adx = dx < 0 ? -dx : dx;
            s16 ady = dy < 0 ? -dy : dy;
            if ((adx >= minDist) || (ady >= minDist)) continue;

            s16 dist = (adx >= ady) ? (s16) (adx + (ady >> 1)) : (s16) (ady + (adx >> 1));

            // centros coincidentes: empurra num eixo determinístico (destrava)
            if (dist == 0)
            {
                dx = adx = (s16) (1 + (i & 3));
                dy = ady = (s16) (1 + (j & 3));
                dist = (adx >= ady) ? (s16) (adx + (ady >> 1)) : (s16) (ady + (adx >> 1));
            }
            else if (dist >= minDist) continue;

            // empurrão proporcional à sobreposição, com teto (afastamento lento)
            s16 push = (s16) ((minDist - dist) * SEP_STRENGTH);
            if (push > SEP_MAX) push = SEP_MAX;

            // normaliza por tabela: pv = d * push * (64/dist) / 64  ≈  (d/dist) * push
            const s16 k = (s16) (push * SEP_RECIP[dist]);
            const s32 pvx = ((s32) dx * k) >> 6;
            const s32 pvy = ((s32) dy * k) >> 6;
            pushX[i] -= pvx; pushY[i] -= pvy;   // i afasta de j
            pushX[j] += pvx; pushY[j] += pvy;   // j afasta de i
        }
    }

    // aplica os empurrões (26.6), com teto por inimigo, contendo na arena
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;
        if ((pushX[i] | pushY[i]) == 0) continue;

        if (pushX[i] >  SEP_MAX) pushX[i] =  SEP_MAX;
        if (pushX[i] < -SEP_MAX) pushX[i] = -SEP_MAX;
        if (pushY[i] >  SEP_MAX) pushY[i] =  SEP_MAX;
        if (pushY[i] < -SEP_MAX) pushY[i] = -SEP_MAX;

        const s16 size = ENEMY_SIZE(e);
        e->fx += pushX[i];
        e->fy += pushY[i];

        if (e->fx < (s32) INNER_MIN_X << 6) e->fx = (s32) INNER_MIN_X << 6;
        if (e->fx > (s32) (INNER_MAX_X - (size - 1)) << 6) e->fx = (s32) (INNER_MAX_X - (size - 1)) << 6;
        if (e->fy < (s32) INNER_MIN_Y << 6) e->fy = (s32) INNER_MIN_Y << 6;
        if (e->fy > (s32) (INNER_MAX_Y - (size - 1)) << 6) e->fy = (s32) (INNER_MAX_Y - (size - 1)) << 6;

        e->x = (s16) (e->fx >> 6);
        e->y = (s16) (e->fy >> 6);
    }
}

// empurra o inimigo PARA LONGE de (fromX,fromY) a 2x a velocidade, com stun.
// Reusado no contato com o jogador, no recuo ao encostar no aliado (PROTEGER) e
// na onda de choque da antena. Fixos (speedFp 0) não recuam. Sem divisão (tabela).
void ENEMIES_knockbackFrom(Enemy *e, s16 fromX, s16 fromY)
{
    const EnemyDef *def = ENEMY_DEF(e);
    if (def->speedFp == 0) return;

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

u16 ENEMIES_update(void)
{
    u16 burnKills = 0;

    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;

        const EnemyDef *def = ENEMY_DEF(e);

        if (e->hitFlash) e->hitFlash--;     // decai o brilho branco do dano
        if (e->burnFlash) e->burnFlash--;   // decai o pulso vermelho do fogo

        // queimadura (fogo): 1 de dano a cada FIRE_TICK_SEC, por FIRE_BURN_SEC
        if (e->burn)
        {
            e->burn--;
            if (e->burnTick) e->burnTick--;
            if (e->burnTick == 0)
            {
                e->burnTick = FIRE_TICK_SEC * fps;
                if (--e->hp == 0) { enemyDie(e); burnKills++; continue; }
                e->burnFlash = HIT_FLASH_FRAMES;    // pulso vermelho: tomou dano do fogo
            }
        }

        // congelado (gelo): parado, sem comportamento nem dano de contato
        if (e->frozen) { e->frozen--; continue; }

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

    ENEMIES_separate();     // afasta devagar quem empilhou (anti-overlap)
    return burnKills;
}

#define BOMB_BOSS_DMG   4       // dano da bomba no chefe (não o mata)

u16 ENEMIES_killAll(void)
{
    u16 count = 0;
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        if (!enemies[i].active) continue;

        // CHEFE resiste à bomba: não morre; leva um dano fixo (se não blindado)
        if (enemies[i].type == ENEMY_BOSS)
        {
            if (!enemies[i].shielded)
                enemies[i].hp = (enemies[i].hp > BOMB_BOSS_DMG)
                              ? (u8) (enemies[i].hp - BOMB_BOSS_DMG) : 1;
            continue;
        }

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
    if (e->type == ENEMY_BOSS) bossDefeated = TRUE;     // chefe morto → encerra a fase 16
    if (ENEMY_DEF(e)->extra == EXTRA_SPLIT) splitInto(e);
    e->active = FALSE;
    BLOOD_splat(e->x + half, e->y + half);      // poça de sangue verde no local
    ITEMS_tryDrop(e->x + half, e->y + half, e->type);
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
