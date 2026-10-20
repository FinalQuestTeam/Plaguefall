// Efeito visual do raio em cadeia: cada acerto encadeado vira um arco elétrico
// desenhado como uma fileira de "nós" (TILE_SPARK) em ziguezague, ligando o
// ponto do tiro ao inimigo. Cintila por alguns quadros e some.

#include "system/video/chainfx.h"
#include "system/video/spritelist.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "system/video/projection.h"

#define MAX_ARCS    6       // arcos simultâneos (chain atinge até 3 por tiro)
#define ARC_LIFE    9       // ~0,15 s de duração
#define ARC_SPARKS  4       // nós desenhados ao longo de cada arco
#define ARC_AMP     4       // amplitude do ziguezague (px)
#define SPRITE_CAP  78      // não estoura a lista de sprites de hardware

typedef struct { s16 x0, y0, x1, y1; u8 life; } Arc;
static Arc arcs[MAX_ARCS];

void CHAINFX_reset(void)
{
    for (u16 i = 0; i < MAX_ARCS; i++) arcs[i].life = 0;
}

void CHAINFX_add(s16 x0, s16 y0, s16 x1, s16 y1)
{
    for (u16 i = 0; i < MAX_ARCS; i++)
    {
        if (arcs[i].life) continue;
        arcs[i].x0 = x0; arcs[i].y0 = y0;
        arcs[i].x1 = x1; arcs[i].y1 = y1;
        arcs[i].life = ARC_LIFE;
        return;
    }
}

void CHAINFX_update(void)
{
    for (u16 i = 0; i < MAX_ARCS; i++)
        if (arcs[i].life) arcs[i].life--;
}

u16 CHAINFX_draw(u16 n)
{
    for (u16 i = 0; i < MAX_ARCS; i++)
    {
        Arc *a = &arcs[i];
        if (!a->life) continue;
        if (a->life & 1) continue;          // cintila: desenha em quadros alternados

        const s16 dx = a->x1 - a->x0;
        const s16 dy = a->y1 - a->y0;
        u32 len = getApproximatedDistance(dx, dy);
        if (len == 0) len = 1;

        // perpendicular unitário (× ARC_AMP), para o desvio do ziguezague
        const s16 offX = (s16) ((-(s32) dy * ARC_AMP) / (s32) len);
        const s16 offY = (s16) (( (s32) dx * ARC_AMP) / (s32) len);

        for (u16 s = 1; s <= ARC_SPARKS; s++)
        {
            if (n >= SPRITE_CAP) return n;

            // ponto sobre a reta + desvio alternado (nó do raio, centrado 8x8)
            const s16 sign = (s & 1) ? 1 : -1;
            const s16 sx = a->x0 + (s16) ((s32) dx * s / (ARC_SPARKS + 1)) + offX * sign - 4;
            const s16 sy = a->y0 + (s16) ((s32) dy * s / (ARC_SPARKS + 1)) + offY * sign - 4;

            SPRITES_emit(&n, sx, VIDEO_PROJECT_Y(sy), SPRITE_SIZE(1, 1),
                TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, TILE_USER_INDEX + TILE_SPARK));
        }
    }
    return n;
}
