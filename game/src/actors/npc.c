// Aliado (NPC) do objetivo PROTEGER — ver npc.h.

#include "actors/npc.h"
#include "core/game.h"
#include "enemies/enemies.h"
#include "system/video/flash.h"     // FLASH_trigger (onda de choque)
#include "system/video/screens/hud.h"

#define NPC_CONTACT_DMG  12         // dano por encostão de inimigo
#define NPC_INV_TENTHS   50         // invencibilidade após dano (0,1 s) -> 5,0 s
#define NPC_SHOCK_RANGE  56         // alcance (px) da onda de choque ao levar dano

s16 npcX, npcY;
s16 npcHp;
s16 npcHpMax;
static bool active;
static u16  invTimer;

void NPC_spawn(s16 x, s16 y, u16 hp)
{
    // 0,0 -> centro da arena interna (aliado 24x24); hp 0 -> vida padrão
    npcX = x ? x : (INNER_MIN_X + INNER_MAX_X) / 2 - NPC_SIZE / 2;
    npcY = y ? y : (INNER_MIN_Y + INNER_MAX_Y) / 2 - NPC_SIZE / 2;
    npcHpMax = hp ? (s16) hp : NPC_DEFAULT_HP;
    npcHp = npcHpMax;
    invTimer = 0;
    active = TRUE;
}

void NPC_clear(void)      { active = FALSE; npcHp = 0; invTimer = 0; }
bool NPC_active(void)     { return active; }
bool NPC_alive(void)      { return active && npcHp > 0; }
bool NPC_hidden(void)     { return invTimer && ((invTimer >> 2) & 1); }

// onda de choque ao levar dano: empurra TODOS os inimigos num raio + flash de tela
static void shockwave(s16 cx, s16 cy)
{
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;
        const s16 half = ENEMY_SIZE(e) / 2;
        s16 dx = (e->x + half) - cx, dy = (e->y + half) - cy;
        const s16 adx = dx < 0 ? -dx : dx, ady = dy < 0 ? -dy : dy;
        const s16 dist = (adx >= ady) ? (s16) (adx + (ady >> 1)) : (s16) (ady + (adx >> 1));
        if (dist < NPC_SHOCK_RANGE) ENEMIES_knockbackFrom(e, cx, cy);
    }
    FLASH_trigger();
}

void NPC_update(void)
{
    if (!active) return;

    const s16 cx = npcX + NPC_SIZE / 2, cy = npcY + NPC_SIZE / 2;
    const bool vulnerable = (invTimer == 0);
    if (invTimer) invTimer--;

    // todos os inimigos que encostam QUICAM (recuo) — não acampam sobre a antena,
    // nem durante a invulnerabilidade; a fase vira ondas em vez de um monte grudado
    bool contact = FALSE;
    for (u16 i = 0; i < MAX_ENEMIES; i++)
    {
        Enemy *e = &enemies[i];
        if (!e->active) continue;
        const EnemyDef *d = ENEMY_DEF(e);
        if (!d->contactDmg) continue;           // alvos/dummies não machucam

        if ((e->x < npcX + NPC_SIZE) && (e->x + d->size > npcX) &&
            (e->y < npcY + NPC_SIZE) && (e->y + d->size > npcY))
        {
            ENEMIES_knockbackFrom(e, cx, cy);   // #1: recuo ao encostar
            contact = TRUE;
        }
    }

    // dano só quando vulnerável; ao sofrer, dispara a onda de choque (#2)
    if (contact && vulnerable)
    {
        npcHp -= NPC_CONTACT_DMG;
        if (npcHp < 0) npcHp = 0;
        invTimer = (u16) (NPC_INV_TENTHS * fps / 10);
        shockwave(cx, cy);
    }
}
