// Tela do mapa de rotas — ver routemap.h. Tudo em texto (fonte padrão, PAL0):
// custo zero de VRAM e de arte. A grade vem de GRAPH[n].mapCol/mapRow (colunas
// espaçadas de 2 tiles, linhas idem); as ligações vêm das saídas de cada nó,
// então bifurcações novas aparecem aqui sem tocar nesta tela.

#include "system/video/screens/routemap.h"
#include "levels/graph.h"

// canto da grade na tela (colunas 0..15 → x 4..34; linhas 0..2 → y 8..12)
#define MAP_X       4
#define MAP_Y       8
#define MAP_STEP    2       // tiles entre colunas (e entre linhas) do grafo

#define BLINK_FRAMES 16     // meia-fase do pisca do marcador da próxima fase

static u32 visited;         // bit n = nó n já jogado neste run (1..NODE_COUNT)
static u8  nextNode;        // nó destacado (destino do jogador)
static u16 blinkTimer;
static bool blinkOn;

void ROUTEMAP_reset(void)
{
    visited = 0;
}

void ROUTEMAP_markVisited(u8 n)
{
    visited |= (u32) 1 << n;
}

static u16 nodeX(u8 n) { return MAP_X + GRAPH[n].mapCol * MAP_STEP; }
static u16 nodeY(u8 n) { return MAP_Y + GRAPH[n].mapRow * MAP_STEP; }

// marcador do nó: caminho percorrido "O", próxima fase "*", resto "."
static void drawNode(u8 n)
{
    const char *mark = ".";
    if (visited & ((u32) 1 << n)) mark = "O";
    if (n == nextNode)            mark = "*";
    VDP_drawText(mark, nodeX(n), nodeY(n));
}

// ligação do nó a com o destino b da saída: "-" na mesma linha, "/" e "\"
// entre linhas vizinhas (as colunas do grafo são sempre adjacentes)
static void drawLink(u8 a, u8 b)
{
    const s16 dr = (s16) GRAPH[b].mapRow - (s16) GRAPH[a].mapRow;
    const u16 x = nodeX(a) + 1;
    if (dr == 0)      VDP_drawText("-",  x, nodeY(a));
    else if (dr > 0)  VDP_drawText("\\", x, nodeY(a) + 1);
    else              VDP_drawText("/",  x, nodeY(a) - 1);
}

void ROUTEMAP_show(u8 next)
{
    nextNode = next;
    blinkTimer = BLINK_FRAMES;
    blinkOn = TRUE;

    VDP_drawText("MAPA DA CAMPANHA", 12, 4);

    for (u8 n = 1; n <= NODE_COUNT; n++)
    {
        const LevelNode *node = &GRAPH[n];
        for (u8 i = 0; i < node->exitCount; i++)
            drawLink(n, node->exits[i].next);
        drawNode(n);
    }

    char buf[24];
    sprintf(buf, "PROXIMA: FASE %s", GRAPH[next].name);
    VDP_drawText(buf, 12, 17);
    VDP_drawText("O SEU CAMINHO  * PROXIMA", 8, 20);
    VDP_drawText("APERTE A PARA CONTINUAR", 8, 23);
}

void ROUTEMAP_update(void)
{
    if (blinkTimer) { blinkTimer--; return; }
    blinkTimer = BLINK_FRAMES;
    blinkOn = !blinkOn;
    VDP_drawText(blinkOn ? "*" : " ", nodeX(nextNode), nodeY(nextNode));
}
