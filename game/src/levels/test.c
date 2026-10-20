// Fase teste (sandbox): portas entre os estágios, a manutenção dos inimigos de
// cada estágio e a caixa de infos do jogador. Fica aqui (e não em main.c) para
// seguir o padrão das demais fases — main.c cuida só da máquina de estados.
//
//   1: dummy resistente (testa tiros/lava/lama).   2: alvos frágeis (raio em cadeia).
//   3: chefe.   4: SOBREVIVER.   5: COLETAR.   6: PROTEGER.
// Os estágios 4/5/6 demonstram os objetivos novos: inimigos surgem continuamente
// e a meta/HUD é avaliada em core/flow.c (reinicia o estágio ao concluir/falhar).

#include "levels/test.h"
#include "system/video/sprites/tiles.h"
#include "levels/levels.h"
#include "core/game.h"
#include "enemies/enemies.h"
#include "items/items.h"
#include "actors/shots.h"
#include "actors/player.h"
#include "core/objective.h"     // OBJECTIVE_prepText (meta dos estágios 4/5/6)

// posições fixas dos 3 alvos da teste 2 (canto sup. esq. do sprite 24x24)
static const struct { s16 x, y; } SPOTS[3] = { { 130, 64 }, { 160, 64 }, { 190, 64 } };

// portas (em tiles): cadeia linear 1..6 (esquerda = anterior, direita = próximo)
#define DOOR_W          3
#define DOOR_H          4
#define DOOR_Y          10          // linha do topo da porta
#define DOOR1_X         35          // porta à direita (→ próximo estágio)
#define DOOR2_X         2           // porta à esquerda (→ estágio anterior)

#define TEST2_SPAWN_S   2           // intervalo de aparição dos alvos (teste 2)
#define OBJ_ENEMY_CAP   8           // teto de inimigos nos estágios de objetivo

// nome curto de cada estágio (índice = testStage)
static const char *const STAGE_NAME[7] =
    { "", "TESTE 1", "TESTE 2", "CHEFE", "SOBREVIVER", "COLETAR", "PROTEGER" };

static u16 spawnTimer;              // reaparecer alvos (teste 2)
static u8 infoTicks;
static u8 infoPower=255,infoBonus=255;
static u16 objSpawnTimer;           // aparição de inimigos (estágios 4/5/6)

// o jogador (16x16 em px,py) encosta no retângulo de tiles [tx,ty]+[tw,th]?
static bool playerOnTiles(u16 tx, u16 ty, u16 tw, u16 th)
{
    const s16 x1 = tx * 8, y1 = ty * 8;
    const s16 x2 = (tx + tw) * 8, y2 = (ty + th) * 8;
    return (px < x2) && (px + 16 > x1) && (py < y2) && (py + 16 > y1);
}

void TEST_draw(void)
{
    infoTicks=0;infoPower=infoBonus=255;
    const u16 attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_USER_INDEX + TILE_DOOR);
    char buf[32];
    spawnTimer = TEST2_SPAWN_S * fps;
    objSpawnTimer = fps;

    // validação no início: a meta do estágio de objetivo (4/5/6)
    if (testStage >= 4)
    {
        OBJECTIVE_prepText(buf, LEVEL_current());
        VDP_drawText(buf, 2, 6);
    }

    // porta à esquerda (estágio anterior)
    if (testStage > 1)
    {
        VDP_fillTileMapRect(BG_A, attr, DOOR2_X, DOOR_Y, DOOR_W, DOOR_H);
        sprintf(buf, "<- %s", STAGE_NAME[testStage - 1]);
        VDP_drawText(buf, 2, 8);
    }
    // porta à direita (próximo estágio)
    if (testStage < 6)
    {
        VDP_fillTileMapRect(BG_A, attr, DOOR1_X, DOOR_Y, DOOR_W, DOOR_H);
        sprintf(buf, "%s ->", STAGE_NAME[testStage + 1]);
        VDP_drawText(buf, 26, 8);
    }
}

u8 TEST_update(void)
{
    // portas: pisar na área de passagem troca de estágio (cadeia 1..6)
    if (testStage > 1 && playerOnTiles(DOOR2_X, DOOR_Y, DOOR_W, DOOR_H)) return testStage - 1;
    if (testStage < 6 && playerOnTiles(DOOR1_X, DOOR_Y, DOOR_W, DOOR_H)) return testStage + 1;

    // inimigos / itens de cada estágio
    if (testStage == 2)
    {
        // alvos frágeis: quando todos caem, reaparecem após o intervalo
        if (ENEMIES_activeCount() == 0)
        {
            if (spawnTimer) spawnTimer--;
            else
            {
                for (u16 i = 0; i < 3; i++)
                    ENEMIES_spawnAt(ENEMY_TARGET, SPOTS[i].x, SPOTS[i].y);
                spawnTimer = TEST2_SPAWN_S * fps;
            }
        }
        ITEMS_testEnsure();
    }
    else if (testStage == 3)
    {
        if (ENEMIES_activeCount() == 0) ENEMIES_spawnAt(ENEMY_BOSS, 144, 48);
    }
    else if (testStage >= 4)
    {
        // objetivos: inimigos surgem continuamente até o teto
        if (ENEMIES_activeCount() < OBJ_ENEMY_CAP)
        {
            if (objSpawnTimer) objSpawnTimer--;
            else
            {
                const LevelDef *d = LEVEL_current();
                ENEMIES_trySpawn(d->enemyTypes, d->enemyTypeCount);
                objSpawnTimer = fps;
            }
        }
        if (testStage == 5) ITEMS_testEnsure();     // itens para coletar
    }
    else
    {
        if (ENEMIES_activeCount() == 0) ENEMIES_spawnAt(ENEMY_DUMMY, 148, 80);
        ITEMS_testEnsure();
    }

    // Text/decimal formatting and direct VRAM writes were repeated every frame.
    // Refresh unchanged info at10Hz; pickups update it immediately. Periodic
    // refresh also repairs any floor/decal drawing underneath this overlay.
    const u8 power=SHOTS_power(),bonus=PLAYER_speedBonus();
    if(infoTicks && power==infoPower && bonus==infoBonus){infoTicks--;return 0;}
    infoTicks=fps==50 ? 4 : 5;infoPower=power;infoBonus=bonus;
    char buf[20];
    VDP_drawText("-- JOGADOR --", 2, 3);
    sprintf(buf, "BALAS:    %d", power);
    VDP_drawText(buf, 2, 4);
    sprintf(buf, "VELOC: +%3d%%", bonus);
    VDP_drawText(buf, 2, 5);
    return 0;
}

void TEST_drawPauseText(void)
{
    char buf[24];
    sprintf(buf, "PAUSA - %s", STAGE_NAME[testStage]);
    VDP_drawText(buf, 10, 9);
}
