// Fases: dispatcher (carga/desenho, atualização dos elementos, HUD de condições).
// A CURVA de dificuldade está em levels/defs/level01.c .. level15.c (uma por
// arquivo); os terrenos reutilizáveis em levels/layouts.c.

#include "levels/levels.h"
#include "levels/graph.h"
#include "system/video/sprites/tiles.h"
#include "system/video/enemygfx.h"
#include "core/game.h"
#include "core/objective.h"        // OBJECTIVE_prepText (texto da meta na preparação)
#include "elements/lava.h"
#include "elements/mud.h"

u8 currentLevel = 1;
u8 testStage = 1;

// o registro das fases é o GRAFO da campanha (levels/graph.c): aqui o número
// da fase n é o número do NÓ (GRAPH[n]), e a def vem do nó

// dados das fases teste (TEST_def / TEST2_def) vivem em levels/defs/test.c

// def da fase teste pelo estágio atual (independe de currentLevel — usado também
// pelo LEVEL_loadGfx, que roda ANTES de currentLevel virar 0)
static const LevelDef *testDef(void)
{
    switch (testStage)
    {
        case 6:  return &TEST6_def;
        case 5:  return &TEST5_def;
        case 4:  return &TEST4_def;
        case 3:  return &TEST3_def;
        case 2:  return &TEST2_def;
        default: return &TEST_def;
    }
}

const LevelDef *LEVEL_current(void)
{
    if (currentLevel == 0) return testDef();
    return GRAPH[currentLevel].def;
}

static void drawBorder(void)
{
    const u16 attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_USER_INDEX + TILE_WALL);
    VDP_fillTileMapRect(BG_A, attr, ARENA_TILE_X, ARENA_TILE_Y, ARENA_TILES_W, 1);
    VDP_fillTileMapRect(BG_A, attr, ARENA_TILE_X, ARENA_TILE_Y + ARENA_TILES_H - 1, ARENA_TILES_W, 1);
    VDP_fillTileMapRect(BG_A, attr, ARENA_TILE_X, ARENA_TILE_Y, 1, ARENA_TILES_H);
    VDP_fillTileMapRect(BG_A, attr, ARENA_TILE_X + ARENA_TILES_W - 1, ARENA_TILE_Y, 1, ARENA_TILES_H);
}

void LEVEL_draw(u8 n)
{
    currentLevel = n;

    // limpa o interior da arena (apaga elementos anteriores e textos)
    VDP_fillTileMapRect(BG_A, TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, 0),
        ARENA_TILE_X + 1, ARENA_TILE_Y + 1, ARENA_TILES_W - 2, ARENA_TILES_H - 2);

    drawBorder();

    const LevelDef *def = LEVEL_current();
    if (def->lava) LAVA_draw(def->lava, def->lavaCount);
    if (def->mud) MUD_draw(def->mud, def->mudCount);

    // (o rótulo da fase no HUD saiu: o inventário ocupa a linha 0; a fase é
    //  mostrada na tela de preparação e na pausa)
}

// (o descarte de arte de inimigo por vida útil usa GRAPH_reachableTypes, em
//  levels/graph.c — alcançabilidade real no grafo, e não o número do nó)

// carrega na VRAM a arte (8 direções) só dos inimigos que aparecem na fase n
// (0 = fase teste, pelo testStage atual). Reuso + descarte no ENEMYGFX.
void LEVEL_loadGfx(u8 n)
{
    // usa testDef() (por testStage), não LEVEL_current(): currentLevel ainda não
    // é 0 aqui (LEVEL_load só o zera depois), o que faria carregar o roster errado
    const LevelDef *def = (n == 0) ? testDef() : GRAPH[n].def;
    // fase teste roda "fora da campanha": 0xFF libera o descarte de qualquer tipo
    ENEMYGFX_loadForPhase(n == 0 ? 0xFF : n, def->enemyTypes, def->enemyTypeCount);
}

void LEVEL_load(u8 n)
{
    LEVEL_loadGfx(n);       // arte dos inimigos desta fase (por etapas, com cache)
    LEVEL_draw(n);
    LEVEL_reset();
}

void LEVEL_update(void)
{
    const LevelDef *def = LEVEL_current();
    if (def->lava) LAVA_update(def->lava, def->lavaCount);
    if (def->mud) MUD_update(def->mud, def->mudCount);
}

void LEVEL_reset(void)
{
    LAVA_reset();
    MUD_reset();
}

// desenha o inimigo (inseto) alinhado pela BASE em rowBase — assim tamanhos
// diferentes (16/24/32) ficam numa mesma linha de "chão". O desenho em si é o
// ENEMYGFX_drawOnMap (compartilhado com a tela de ajuda).
static void drawEnemyOnMap(u8 type, u16 col, u16 rowBase, u8 size)
{
    const u16 nt = size / 8;                    // tiles por lado (2/3/4)
    ENEMYGFX_drawOnMap(type, col, rowBase + 1 - nt);
}

void LEVEL_drawInfo(u8 n, u16 x, u16 y)
{
    const LevelDef *def = (n == 0) ? LEVEL_current() : GRAPH[n].def;
    char buf[40];

    OBJECTIVE_prepText(buf, def);           // "META: ..." conforme o objetivo da fase
    VDP_drawText(buf, x, y);

    sprintf(buf, "INTERVALO DE SPAWN: %d S", def->spawnSeconds);
    VDP_drawText(buf, x, y + 2);

    // "INIMIGOS:" seguido dos SPRITES (insetos) dos tipos distintos da fase,
    // alinhados pela base logo abaixo do rótulo
    VDP_drawText("INIMIGOS:", x, y + 4);
    const u16 rowBase = y + 8;
    u16 col = x;
    u16 shown = 0;                              // tipos já mostrados (bitmask)
    for (u16 i = 0; i < def->enemyTypeCount; i++)
    {
        const u8 t = def->enemyTypes[i];
        if (shown & (1 << t)) continue;
        shown |= (1 << t);
        const EnemyDef *e = ENEMY_DEFS[t];
        if (e->size > 32) continue;             // chefe (48px, layout em quadrantes)
        const u8 nt = e->size / 8;
        if (col + nt > x + 30) break;           // não estoura a linha
        drawEnemyOnMap(t, col, rowBase, e->size);
        col += nt + 1;                          // largura + folga
    }
}
