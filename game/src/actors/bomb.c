// Bomba: cargas do jogador e o ataque que limpa a tela (som + flash + mata
// todos os inimigos). O item de coleta (items/item_bomb.c) chama BOMB_add.

#include "actors/bomb.h"
#include "levels/campaign_factory.h"
#include "core/stats.h"
#include "levels/arena.h"
#include "system/video/screens/hud.h"
#include "system/audio/sfx.h"
#include "system/video/flash.h"
#include "enemies/enemies.h"

// BOMB_MAX em actors/bomb.h (bloco CONFIG)

static u16 bombs;

void BOMB_clear(void) { bombs = 0; }

void BOMB_reset(void)
{
    bombs = BOMB_MAX - 1;
}

void BOMB_add(void)
{
    if (bombs < BOMB_MAX) bombs++;      // HUD: mostrado no inventário (pos 0)
}

u16 BOMB_use(void)
{
    if (bombs == 0) return 0;

    bombs--;
    phaseStats.bombsUsed++;     // condições de saída do grafo (SEM/USOU_BOMBA)
    ARENA_damageChurch();
    CF_bomb();
    SFX_bombBlast();
    FLASH_trigger();

    return ENEMIES_killAll();   // sem drop: a bomba não sorteia itens
}

u16 BOMB_count(void)
{
    return bombs;
}
