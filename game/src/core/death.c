// Penalidade da campanha; treino conserva seu reinício independente.
#include "core/death.h"
#include "core/game.h"
#include "core/inventory.h"
#include "actors/player.h"
#include "actors/shots.h"
#include "actors/bomb.h"
#include "items/items.h"
#include "levels/graph.h"

static u8 retryNode;
static s16 bagX, bagY;
static bool captured, spawnPending, recoverable;
static struct {
    u8 shots, speed, mode, charges;
    u16 bombs, shield;
    InvSlot item[INV_ITEMS];
} loot;

u8 DEATH_rule(u8 node)
{
    if (node <= N_5) return DEATH_KEEP;
    if (node <= N_11) return DEATH_REDUCE;
    return DEATH_BAG;
}

void DEATH_reset(void)
{
    retryNode = 0;
    captured = spawnPending = recoverable = FALSE;
    memset(&loot, 0, sizeof loot);
}

void DEATH_capture(u8 node, s16 x, s16 y)
{
    if (!node || node >= NODE_MAX) return;
    const u8 rule = DEATH_rule(node);
    retryNode = node;
    bagX = x; bagY = y;
    captured = TRUE;
    spawnPending = recoverable = FALSE; // a queda substitui a bolsa anterior
    loot.shots = SHOTS_power() - 1; // guarda melhorias; o projétil básico é gratuito
    loot.speed = PLAYER_speedBonus() / PLAYER_SPEED_STEP;
    loot.mode = SHOTS_mode();loot.charges = SHOTS_modeCharges();
    loot.bombs = BOMB_count();loot.shield = PLAYER_shieldRemaining();
    for (u8 i = 0; i < INV_ITEMS; i++)
        INV_view(i + 1, &loot.item[i].type, &loot.item[i].charges);
    if (rule == DEATH_REDUCE)
    {
        if (loot.shots) loot.shots--;
        if (loot.speed) loot.speed--;
        bool removed = FALSE;
        for (u8 i = INV_ITEMS; i > 0; i--)
            if (loot.item[i - 1].type != INV_EMPTY)
            {
                loot.item[i - 1].type = INV_EMPTY;
                loot.item[i - 1].charges = 0;
                removed = TRUE;break;
            }
        if (!removed && loot.bombs) loot.bombs--;
    }
    else if (rule == DEATH_BAG)
    {
        // No estágio final só volta uma melhoria que realmente existia.
        loot.shots = loot.shots ? 1 : 0;
        loot.speed = loot.speed ? 1 : 0;
        loot.bombs = loot.shield = 0;
        loot.mode = loot.charges = 0;
        for (u8 i = 0; i < INV_ITEMS; i++)
        { loot.item[i].type = INV_EMPTY;loot.item[i].charges = 0; }
    }
}

void DEATH_retry(u8 node, s16 x, s16 y)
{
    if (!node || node >= NODE_MAX) return;
    // Direct callers may prepare a retry without the campaign death animation.
    if (!captured || retryNode != node) DEATH_capture(node, x, y);
    captured = FALSE;spawnPending = TRUE;
    PLAYER_fullHp();SHOTS_resetPower();PLAYER_resetSpeed();
    SHOTS_resetChain();INV_clear();BOMB_clear();PLAYER_restoreShield(0);
}

u8 DEATH_recover(void)
{
    if (!recoverable) return DEATH_RECOVER_DONE;
    bool changed = loot.shots || loot.speed || loot.bombs || loot.charges || loot.shield;
    // Somente as quantidades da fotografia; coletas novas continuam no jogador.
    for (u8 i = 0; i < loot.shots; i++) SHOTS_addPower();
    for (u8 i = 0; i < loot.speed; i++) PLAYER_addSpeed();
    for (u16 i = 0; i < loot.bombs; i++) BOMB_add();
    loot.shots = loot.speed = 0;loot.bombs = 0;
    bool remaining = FALSE;
    for (u8 i = 0; i < INV_ITEMS; i++)
        if (loot.item[i].type != INV_EMPTY)
        {
            if (INV_store(loot.item[i].type, loot.item[i].charges))
            { loot.item[i].type = INV_EMPTY;loot.item[i].charges = 0;changed = TRUE; }
            else remaining = TRUE;
        }
    if (loot.charges) SHOTS_setMode(loot.mode, loot.charges);
    if (loot.shield > PLAYER_shieldRemaining()) PLAYER_restoreShield(loot.shield);
    loot.mode = loot.charges = 0;loot.shield = 0;
    if (remaining) return changed ? DEATH_RECOVER_PARTIAL : DEATH_RECOVER_BLOCKED;
    DEATH_reset();
    return DEATH_RECOVER_DONE;
}

static bool safeSpot(s16 x, s16 y)
{
    if (ARENA_blocked(x, y, 16, 16)) return FALSE;
    // Do not hide the recovery in lava or collect it automatically at spawn.
    if (x < px + 16 && x + 16 > px && y < py + 16 && y + 16 > py) return FALSE;
    const LevelDef *def = LEVEL_current();
    for (u16 i = 0; i < def->lavaCount; i++)
    {
        const TileRect *r = &def->lava[i];
        if (x < (r->x + r->w) * 8 && x + 16 > r->x * 8 &&
            y < (r->y + r->h) * 8 && y + 16 > r->y * 8) return FALSE;
    }
    return TRUE;
}

void DEATH_startPhase(u8 node)
{
    if (retryNode != node) { DEATH_reset(); return; }
    if (!spawnPending) return;
    spawnPending = FALSE;

    // Search near the fall, then the safe stage entrance if necessary.
    for (u8 origin = 0; origin < 2; origin++)
    {
        const s16 cx = origin ? px : bagX, cy = origin ? py : bagY;
        for (s16 radius = 0; radius <= 96; radius += 8)
            for (s16 dy = -radius; dy <= radius; dy += 8)
                for (s16 dx = -radius; dx <= radius; dx += 8)
                {
                    if (abs(dx) != radius && abs(dy) != radius) continue;
                    const s16 x = cx + dx, y = cy + dy;
                    if (safeSpot(x, y)) {
                        ITEMS_spawnAt(ITEM_BAG, x, y);recoverable = TRUE;return;
                    }
                }
    }
}
