#include "text_data.h"
#include "system/video/screens/loading.h"
// Regional atlas: static BG_B art, graph-driven BG_A, one persistent pin.
#include "system/video/screens/routemap.h"
#include "levels/graph.h"
#include "routemap_copy.h"
#include "core/game.h"
#include "system/video/tilegen.h"
#include "system/video/floor.h"
#include "system/video/enemygfx.h"
#include "system/video/spritelist.h"
#include "routemap_data.h"
#include "intro_data.h" // shared opaque font: labels remain readable over the art

#define ART_TILES 800
#define ART_BASE (TILE_USER_INDEX + NUM_TILES)
#define OVERLAY_BASE (ART_BASE + ART_TILES)
#define OVERLAY_TILES 192
#define PIN_BASE (OVERLAY_BASE + OVERLAY_TILES)
#define ART_Y 16
typedef char map_vram_fits[(PIN_BASE + 4 <= 1440) ? 1 : -1];

static u32 visited;
static u8 departedTo[NODE_MAX], lastVisited;
static u8 currentNode, nextNode, region;
static u16 clockTick, travelTick, overlayCount, savedPalette[64];
static bool active;
// 1,280 bytes, reused per row. No full-screen RAM framebuffer.
static u32 rowPixels[40 * 8];
static u16 rowTop;
typedef struct {
    u32 tiles[OVERLAY_TILES*8];
    u16 rows[22][40];
    u16 count;
} PreparedMap;
static PreparedMap *prepared;
static u8 preparedCurrent,preparedNext;

static const u16 COLUMN_X[16] = {32,96,160,224,56,152,248,48,120,200,280,48,104,160,216,272};
static const char *const REGION_NAMES[4] = {"COMUNIDADE","EVACUAÇÃO","BASE INDUSTRIAL","NINHOS"};
static const char *const PLACE[NODE_MAX] = {"","PÁTIO DA IGREJA","IGREJA PRESERVADA","IGREJA DESTRUÍDA","RUA ATÉ O GALPÃO","INTERIOR DO GALPÃO","SINAL NA SANTA","ESGOTOS","ESGOTOS SOB PRESSÃO","ABRIGO ÚLTIMO CHÃO","TRANSMISSORES","CAMINHO DA FÁBRICA","OVOS NA FÁBRICA","VÁLVULAS DA FÁBRICA","ESCOLTA AO SINDICATO","SINDICATO: DINORAH VIVA","SINDICATO: LUTO","ENERGIA DO ESTALEIRO","RÁDIO DE IGNIÇÃO","ESCORPIÃO"};
static const u16 MAP_PALETTE[16] = {
 RGB24_TO_VDPCOLOR(0x000000), RGB24_TO_VDPCOLOR(0x101820),
 RGB24_TO_VDPCOLOR(0x8CABA8), RGB24_TO_VDPCOLOR(0xFFDBB6),
 RGB24_TO_VDPCOLOR(0xFFB649), RGB24_TO_VDPCOLOR(0xFFDB92),
 RGB24_TO_VDPCOLOR(0x486060),0,0,0,0,0,0,0,0,RGB24_TO_VDPCOLOR(0xFFDBB6)
};

static u8 regionOf(u8 n)
{
    const u8 col = GRAPH[n].mapCol;
    return col < 4 ? 0 : col < 7 ? 1 : col < 11 ? 2 : 3;
}
static void point(u8 n, s16 *x, s16 *y)
{
    *x = regionOf(n) == region ? COLUMN_X[GRAPH[n].mapCol & 15] :
         GRAPH[n].mapCol < GRAPH[nextNode].mapCol ? 8 : 312;
    *y = ART_Y + (GRAPH[n].mapRow == 0 ? 32 : GRAPH[n].mapRow == 2 ? 136 : 88);
    if (regionOf(n) != region) *y = ART_Y + 88;
}
static void pixel(s16 x, s16 y, u16 color)
{
    if (x < 0 || x >= 320 || y < rowTop || y >= rowTop + 8) return;
    const u16 word = (x >> 3) * 8 + y - rowTop, shift = (7 - (x & 7)) * 4;
    rowPixels[word] = (rowPixels[word] & ~((u32)15 << shift)) | ((u32)color << shift);
}
static void line(s16 x, s16 y, s16 endX, s16 endY, u16 color, bool dashed, bool outline)
{
    if ((y < rowTop - 1 && endY < rowTop - 1) ||
        (y > rowTop + 8 && endY > rowTop + 8)) return;
    const s16 dx = x < endX ? endX - x : x - endX;
    const s16 dy = y < endY ? y - endY : endY - y;
    const s16 sx = x < endX ? 1 : -1, sy = y < endY ? 1 : -1;
    s16 error = dx + dy;
    u16 step = 0;
    while (TRUE)
    {
        // Clip before the nine outline pixel calls, retaining the original
        // Bresenham and dash steps so the raster stays byte-for-byte identical.
        if (y >= rowTop-1 && y <= rowTop+8 && (!dashed || (step % 7) < 4))
        {
            if (outline)
                for (s16 oy = -1; oy <= 1; oy++)
                    for (s16 ox = -1; ox <= 1; ox++) pixel(x + ox, y + oy, 1);
            else pixel(x, y, color);
        }
        if (x == endX && y == endY) break;
        const s16 twice = error * 2;
        if (twice >= dy) { error += dy; x += sx; }
        if (twice <= dx) { error += dx; y += sy; }
        step++;if((step&31)==0)LOADING_poll();
    }
}
static u16 edgeColor(u8 a, u8 b)
{
    if (a == currentNode && b == nextNode) return 4;
    if (departedTo[a] == b) return 3;
    return GRAPH[b].mapCol < GRAPH[nextNode].mapCol ? 6 : 2;
}
static void disk(s16 x, s16 y, s16 radius, u16 color, bool hollow)
{
    if (y + radius < rowTop || y - radius >= rowTop + 8) return;
    for (s16 oy = -radius; oy <= radius; oy++) {
        for (s16 ox = -radius; ox <= radius; ox++)
        {
            const s16 d = ox * ox + oy * oy;
            if (d <= radius * radius && (!hollow || d >= (radius - 1) * (radius - 1)))
                pixel(x + ox, y + oy, color);
        }
        LOADING_poll();
    }
}
static bool visible(u8 n)
{
    if (regionOf(n) == region || n == currentNode) return TRUE;
    for (u8 a = 1; a <= NODE_COUNT; a++)
        if (regionOf(a) == region)
            for (u8 e = 0; e < GRAPH[a].exitCount; e++)
                if (GRAPH[a].exits[e].next == n) return TRUE;
    return FALSE;
}
static void paintRow(void)
{
    memset(rowPixels, 0, sizeof rowPixels);
    // Global diagram: all live graph edges; names stay in the footer.
    for (u8 a = 1; a <= NODE_COUNT; a++)
    {
        const LevelNode *node = &GRAPH[a];
        const s16 x = 80 + node->mapCol * 10, y = 12 + ((s16)node->mapRow - 1) * 3;
        for (u8 e = 0; e < node->exitCount; e++)
        {
            const u8 b = node->exits[e].next;
            line(x,y,80 + GRAPH[b].mapCol * 10,12 + ((s16)GRAPH[b].mapRow - 1) * 3,edgeColor(a,b),FALSE,FALSE);
        }
        LOADING_poll();
        disk(x,y,a == currentNode || a == nextNode ? 1 : 0,
             a == currentNode ? 4 : a == nextNode ? 5 : (visited & ((u32)1 << a)) ? 3 : 6,FALSE);
    }
    for (u8 a = 1; a <= NODE_COUNT; a++)
    {
        const LevelNode *node = &GRAPH[a];
        for (u8 e = 0; e < node->exitCount; e++)
        {
            const u8 b = node->exits[e].next;
            if (regionOf(a) != region && !(a == currentNode && b == nextNode)) continue;
            s16 x,y,bx,by;point(a,&x,&y);point(b,&bx,&by);
            const u16 color = edgeColor(a,b);
            line(x,y,bx,by,color,color == 2 || color == 6,TRUE);
            line(x,y,bx,by,color,color == 2 || color == 6,FALSE);
            LOADING_poll();
        }
    }
    for (u8 n = 1; n <= NODE_COUNT; n++) if (visible(n))
    {
        s16 x,y;point(n,&x,&y);
        disk(x,y,5,1,FALSE);
        disk(x,y,3,n == currentNode ? 4 : (visited & ((u32)1 << n)) ? 3 : 2,
             !(visited & ((u32)1 << n)) && n != currentNode);
        if (n == nextNode) { disk(x,y,8,4,TRUE);disk(x,y,10,5,TRUE); }
    }
}
static const RouteCopy *routeCopy(void)
{
    for (u16 i = 0; i < sizeof ROUTE_COPY / sizeof ROUTE_COPY[0]; i++)
        if (ROUTE_COPY[i].from == currentNode && ROUTE_COPY[i].to == nextNode)
            return &ROUTE_COPY[i];
    return NULL;
}
static void centeredText(const char *text, u16 row)
{
    VDP_drawText(text,(40-strlen(text))/2,row);
}
static void drawAction(bool traveling)
{
    char text[40];
    if (traveling) strcpy(text,"A / START: PULAR VIAGEM");
    else sprintf(text,"A / START: SEGUIR PARA A FASE %s",GRAPH[nextNode].name);
    VDP_fillTileMapRect(BG_A,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_SYSTEM_INDEX+1),0,26,40,1);
    VDP_setTextPalette(PAL3);
    VDP_drawText(text,39-strlen(text),26);
    VDP_setTextPalette(PAL0);
}
static void drawPin(s16 x, s16 y)
{
    VDP_setSpriteFull(0,x-8,y-17,SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,PIN_BASE),0);
    VDP_updateSprites(1,DMA_QUEUE);
}
void ROUTEMAP_reset(void)
{
    if(prepared){MEM_free(prepared);prepared=NULL;}
    visited = 0;lastVisited = 0;memset(departedTo,0,sizeof departedTo);
}
void ROUTEMAP_markVisited(u8 n)
{
    if (!n || n > NODE_COUNT) return;
    if (lastVisited && lastVisited != n)
        for (u8 e = 0; e < GRAPH[lastVisited].exitCount; e++)
            if (GRAPH[lastVisited].exits[e].next == n) departedTo[lastVisited] = n;
    lastVisited = n;visited |= (u32)1 << n;
}
void ROUTEMAP_restore(u32 completedNodes)
{
    ROUTEMAP_reset();
    for(u8 node=1;node<NODE_MAX;node++)
        if(completedNodes&((u32)1<<node))ROUTEMAP_markVisited(node);
}
// Rasterize while the completed result/radio is still visible. The following
// fade only uploads prepared tiles, instead of hiding a long CPU raster pass.
void ROUTEMAP_prepare(u8 current,u8 next)
{
    if(prepared && preparedCurrent==current && preparedNext==next)return;
    if(prepared){MEM_free(prepared);prepared=NULL;}
    prepared=MEM_alloc(sizeof(PreparedMap));
    if(!prepared)return; // the show path retains a cooperative low-memory fallback
    preparedCurrent=current;preparedNext=next;
    currentNode=current;nextNode=next;region=regionOf(next);
    prepared->count=0;LOADING_workBegin();
    for(u16 y=0;y<22;y++) {
        rowTop=y*8;paintRow();
        for(u16 x=0;x<40;x++) {
            u32 used=0;for(u16 i=0;i<8;i++)used|=rowPixels[x*8+i];
            prepared->rows[y][x]=0;
            if(used && prepared->count<OVERLAY_TILES) {
                memcpy(prepared->tiles+prepared->count*8,rowPixels+x*8,32);
                prepared->rows[y][x]=TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,OVERLAY_BASE+prepared->count++);
            }
        }
        LOADING_poll();
    }
    LOADING_workEnd();
}
void ROUTEMAP_show(u8 current, u8 next)
{
    const bool enabled=VDP_getEnable();
    currentNode = current;nextNode = next;region = regionOf(next);
    clockTick = travelTick = overlayCount = 0;
    while (PAL_isDoingFade()) SYS_doVBlankProcess();
    SYS_doVBlankProcess();PAL_getColors(0,savedPalette,64);
    VDP_setEnable(FALSE);VDP_setWindowOff();
    VDP_setScrollingMode(HSCROLL_PLANE,VSCROLL_PLANE);
    VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    VDP_setTextPlane(BG_A);VDP_setTextPalette(PAL0);VDP_setTextPriority(TRUE);
    VDP_loadFontData((const u32 *)intro_font,96,DMA);
    PAL_setColors(0,MAP_PALETTE,16,DMA);
    u16 highlight[16];memcpy(highlight,MAP_PALETTE,sizeof highlight);
    highlight[15] = MAP_PALETTE[4];PAL_setColors(PAL3*16,highlight,16,DMA);
    PAL_setColors(PAL1*16,(const u16 *)routemap_palettes + region*32,32,DMA);
    LOADING_tiles((const u32 *)routemap_tiles + (u32)region*ART_TILES*8,ART_BASE,ART_TILES,DMA);
    for (u16 y = 0; y < 20; y++)
    {
        u16 row[40];
        for (u16 x = 0; x < 40; x++)
        {
            const u16 tile = y*40+x;
            row[x] = TILE_ATTR_FULL(PAL1+routemap_groups[(u32)region*ART_TILES+tile],FALSE,FALSE,FALSE,ART_BASE+tile);
        }
        VDP_setTileMapDataRow(BG_B,row,y+2,0,40,CPU);
    }
    if(prepared && preparedCurrent==current && preparedNext==next) {
        overlayCount=prepared->count;
        LOADING_tiles(prepared->tiles,OVERLAY_BASE,overlayCount,DMA);
        for(u16 y=0;y<22;y++)VDP_setTileMapDataRow(BG_A,prepared->rows[y],y,0,40,CPU);
        MEM_free(prepared);prepared=NULL;
    } else {
    // Bounded fallback if no temporary preparation buffer was available.
    for (u16 y = 0; y < 22; y++)
    {
        u16 row[40];rowTop = y*8;paintRow();LOADING_poll();
        for (u16 x = 0; x < 40; x++)
        {
            u32 used = 0;for (u16 i = 0; i < 8; i++) used |= rowPixels[x*8+i];
            row[x] = 0;
            if (used && overlayCount < OVERLAY_TILES)
            {
                LOADING_tiles(rowPixels+x*8,OVERLAY_BASE+overlayCount,1,DMA);
                row[x] = TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,OVERLAY_BASE+overlayCount++);
            }
        }
        VDP_setTileMapDataRow(BG_A,row,y,0,40,CPU);
    }
    }
    u32 pin[32] = {0};
    for (u16 y = 0; y < 16; y++) for (u16 x = 0; x < 16; x++)
    {
        const u16 half = (16-y)/2;
        if (x >= 8-half && x <= 7+half)
        {
            const u16 color = x == 8-half || x == 7+half || y == 0 ? 1 : 4;
            pin[((x/8)*2+y/8)*8+y%8] |= (u32)color << ((7-x%8)*4);
        }
    }
    LOADING_tiles(pin,PIN_BASE,4,DMA);
    for (u8 n = 1; n <= NODE_COUNT; n++) if (visible(n))
    {
        s16 x,y;point(n,&x,&y);u16 col=x/8-strlen(GRAPH[n].name)/2;
        const u16 len=strlen(GRAPH[n].name);if (col+len>40) col=40-len;
        VDP_drawText(GRAPH[n].name,col,(y+8)/8);
    }
    VDP_drawText(REGION_NAMES[region],1,0);
    char buf[40];sprintf(buf,"ETAPA %u/16",GRAPH[next].mapCol+1);VDP_drawText(buf,28,0);
    VDP_fillTileMapRect(BG_A,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,TILE_SYSTEM_INDEX+1),0,22,40,6);
    VDP_setTextPalette(PAL3);centeredText(PLACE[next],22);VDP_setTextPalette(PAL0);
    const RouteCopy *copy = routeCopy();
    if (copy) { centeredText(copy->cause,23);centeredText(copy->result,24); }
    drawAction(FALSE);
    s16 x,y;point(current,&x,&y);drawPin(x,y);
    active = TRUE;VDP_setEnable(enabled);
}
bool ROUTEMAP_update(u16 pressed)
{
    clockTick++;
    const u16 phase=(clockTick*32/fps)&31;
    PAL_setColor(5,phase<16 ? MAP_PALETTE[5] : MAP_PALETTE[4]);
    if (pressed & (BUTTON_A | BUTTON_START))
    {
        if (travelTick) return TRUE;
        travelTick = 1;
        drawAction(TRUE);
    }
    s16 x,y;point(currentNode,&x,&y);
    if (travelTick)
    {
        s16 bx,by;point(nextNode,&bx,&by);
        const u16 duration=fps;
        x += ((s32)(bx-x)*travelTick)/duration;
        y += ((s32)(by-y)*travelTick)/duration;
        if (++travelTick > duration) return TRUE;
    }
    drawPin(x,y);return FALSE;
}
void ROUTEMAP_release(void)
{
    if (!active) return;
    const bool enabled=VDP_getEnable();
    SPRITES_hide();SYS_doVBlankProcess();VDP_setEnable(FALSE);
    VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    PAL_setColors(0,savedPalette,64,DMA);TILEGEN_palette();ENEMYGFX_reset();
    LOADING_tiles((const u32 *)text_font,TILE_FONT_INDEX,FONT_LENGTH,DMA);
    VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_setWindowOff();VDP_setTextPlane(BG_A);VDP_setTextPalette(PAL0);VDP_setTextPriority(FALSE);
    active = FALSE;VDP_setEnable(enabled);
}
