#include "text_data.h"
#include "system/video/screens/loading.h"
// Radio has its own screen-space compositor; menu paper stays in panel.c.
#include "system/video/screens/radio.h"
#include "system/video/screens/panel.h"
#include "system/video/screens/radio_layout.h"
#include "system/video/screens/result_font.h"
#include "system/video/sprites/portraits_data.h"
#include "system/video/floor.h"
#include "system/video/tilegen.h"
#include "system/video/enemygfx.h"
#include "system/video/spritelist.h"
#include "levels/story.h"
#include "core/game.h"
#include "radio_data.h"
#define BASE (TILE_USER_INDEX + NUM_TILES)
#define PORTRAITS (BASE+RADIO_TILE_COUNT)
#define DYNAMIC (PORTRAITS+PORTRAIT_COUNT*36)
#define DYNAMIC_CAP 400
// The console borrows world/cache tiles, preserving base art and resident font.
typedef char radio_fits[(DYNAMIC+DYNAMIC_CAP<=1440)?1:-1];
static u32 *pixels;
static u16 *grid,used,contentFirst;
static bool radioActive,lineReady,linePending;
static u8 shownRemote,nextRemote;
static u16 lineColors[32],portraitMaps[2][36];
static u16 savedRadioPal[64];
static void portraitPalette(u8 who,u16 *colors,bool speaking)
{
    for(u16 i=0;i<16;i++)
    {
        const u16 c=PORTRAIT_PAL[who][i];
        // Dim each CRAM channel independently, keeping all source pixels exact.
        colors[i]=speaking ? c : (((((c>>1)&7)+1)/3)<<1)|(((((c>>5)&7)+1)/3)<<5)|(((((c>>9)&7)+1)/3)<<9);
    }
}
static void loadPortraits(void)
{
    // Load every possible interlocutor once while entering the console. A
    // speaker change then needs only a palette and (occasionally) map change.
    for(u16 who=0;who<PORTRAIT_COUNT;who++)for(u16 r=0;r<6;r++)for(u16 c=0;c<6;c++)
    {
        u32 data[8]={0};
        for(u16 py=0;py<8;py++)for(u16 px=0;px<8;px++)
        {
            char ch=PORTRAIT_ART[who][r*8+py][c*8+px];u16 colour=ch<='9' ? ch-'0' : ch-'a'+10;
            data[py]|=(u32)colour<<((7-px)*4);
        }
        LOADING_tiles(data,PORTRAITS+who*36+r*6+c,1,DMA);
        LOADING_poll();
    }
}
static void portraitMap(u8 who,u8 slot,TransferMethod tm)
{
    // Persistent buffers are required because DMA_QUEUE reads them at VBlank.
    for(u16 i=0;i<36;i++)portraitMaps[slot][i]=TILE_ATTR_FULL(slot+1,TRUE,FALSE,FALSE,PORTRAITS+who*36+i);
    for(u16 y=0;y<6;y++)VDP_setTileMapDataRow(BG_A,portraitMaps[slot]+y*6,18+y,slot ? 22 : 2,6,tm);
}
// Copy-on-write UI tiles keep the console background immutable. Portrait cells
// never enter this cache; both source pixel arrays remain unchanged.
static u32 *edit(u16 x,u16 y)
{
    const u16 cell=y*40+x;u16 tile=grid[cell];
    if(tile<DYNAMIC)
    {
        if(used==DYNAMIC_CAP)return NULL;
        const u16 next=DYNAMIC+used++;
        if(tile>=BASE && tile<BASE+RADIO_TILE_COUNT)memcpy(pixels+(next-DYNAMIC)*8,((const u32 *)radio_tiles)+(tile-BASE)*8,32);
        else for(u16 i=0;i<8;i++)pixels[(next-DYNAMIC)*8+i]=0x11111111UL;
        grid[cell]=next;tile=next;
    }
    return pixels+(tile-DYNAMIC)*8;
}
static void label(const char *s,u16 x,u16 y,u16 colour)
{
    for(u16 i=0;s[i];i++)
    {
        LOADING_poll();
        u8 glyph=(u8)s[i]-32;if(glyph>=96)continue;
        for(u16 gy=0;gy<8;gy++)
        {
            u32 *dest=edit((x+i*8)>>3,(y+gy)>>3);if(!dest)continue;
            u32 bits=RESULT_FONT[glyph*8+gy];
            bits=(bits|(bits<<12))&0x000f000fUL;bits=(bits|(bits<<6))&0x03030303UL;bits=(bits|(bits<<3))&0x11111111UL;
            u16 ry=(y+gy)&7;dest[ry]=(dest[ry]&~(bits*15))|(bits*colour);
        }
    }
}
static void clearRow(u16 x,u16 y,u16 width)
{
    for(u16 i=0;i<width;i++)
    {
        LOADING_poll();
        u32 *dest=edit(x+i,y);
        if(dest)for(u16 row=0;row<8;row++)dest[row]=0x11111111UL;
    }
}
static void clearContent(void)
{
    // Pin these text cells for the entire conversation. Their VRAM indices
    // never change, and the surrounding frame/map is never cleared or resent.
    clearRow(3,5,14);clearRow(34,5,4);
    for(u16 row=0;row<4;row++)clearRow(3,7+row*2,26);
    for(u16 x=9;x<=29;x+=20)
    {
        clearRow(x,18,9);clearRow(x,20,9);clearRow(x,23,3);
    }
    clearRow(2,26,22);
}
static void flush(void)
{
    LOADING_tiles(pixels,DYNAMIC,used,DMA);
    for(u16 y=0;y<28;y++)
    {
        u16 row[40];for(u16 x=0;x<40;x++)row[x]=grid[y*40+x] ? TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,grid[y*40+x]) : 0;
        VDP_setTileMapDataRow(BG_A,row,y,0,40,CPU);LOADING_poll();
    }
}
bool RADIO_begin(u8 node)
{
    (void)node;
    pixels=MEM_alloc(DYNAMIC_CAP*32);grid=MEM_alloc(1120*2);
    if(!pixels || !grid){if(pixels)MEM_free(pixels);if(grid)MEM_free(grid);return FALSE;}
    SPRITES_hide();SYS_doVBlankProcess();LOADING_getColors(0,savedRadioPal,64);
    LOADING_setEnable(FALSE);VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    LOADING_tiles((const u32 *)radio_tiles,BASE,RADIO_TILE_COUNT,DMA);
    loadPortraits();
    LOADING_setColors(0,(const u16 *)radio_palette,16,DMA);
    LOADING_windowOff();VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);
    VDP_setHorizontalScroll(BG_B,0);VDP_setVerticalScroll(BG_B,0);
    const u16 *map=(const u16 *)radio_map;
    for(u16 i=0;i<1120;i++)grid[i]=map[i] ? BASE+map[i] : 0;
    used=0;lineReady=FALSE;linePending=FALSE;shownRemote=255;
    label("RÁDIO / COMUNIDADE",88,16,15);label("START: PULAR",208,208,15);
    contentFirst=used;
    VDP_setTextPlane(BG_A);VDP_setTextPriority(TRUE);radioActive=TRUE;
    return TRUE;
}
void RADIO_line(u8 side,u8 remote,u8 page,u8 total)
{
    clearContent();
    const char *name=remote==P_COMANDO ? "PADRE" : PORTRAIT_NAME[remote];char buf[40];
    sprintf(buf,"%u/%u",page,total);
    const bool left=side==LADO_ESQ;
    char who[32];sprintf(who,"%s / %s",left ? "TX" : "RX",left ? "DAMIÃO" : name);
    label(who,24,40,15);label(buf,272,40,15);
    label("DAMIÃO",72,144,left ? 15 : 9);label(name,232,144,left ? 9 : 15);
    label(left ? "FALANDO" : "ESCUTANDO",72,160,left ? 15 : 9);
    label(left ? "ESCUTANDO" : "FALANDO",232,160,left ? 9 : 15);
    label(left ? ">>>" : "...",72,184,left ? 13 : 9);
    label(left ? "..." : "<<<",232,184,left ? 9 : 13);
    portraitPalette(P_DAMIAO,lineColors,left);portraitPalette(remote,lineColors+16,!left);
    nextRemote=remote;linePending=TRUE;
    // RADIO_command commits text, prompt and speaker together after startLine
    // has finished preparing them. Keep the current picture on screen meanwhile.
}
void RADIO_glyph(char glyph,u8 col,u8 row)
{
    char one[2]={glyph,0};u16 x=24+col*8,y=56+row*16;
    label(one,x,y,13);
    // The text map is pinned from the first line; reveal only the changed tile.
    for(u16 ty=y>>3;ty<=(y+7)>>3;ty++)
    {
        u16 tile=grid[ty*40+(x>>3)];if(tile<DYNAMIC || tile>=DYNAMIC+used)continue;
        LOADING_tiles(pixels+(tile-DYNAMIC)*8,tile,1,DMA);
    }
}
void RADIO_command(const char *command)
{
    // The footer's text sits in an opaque flat display row, so clearing cells
    // does not alter the metal frame or the right-aligned skip instruction.
    clearRow(2,26,22);
    label(command,16,208,15);
    if(!lineReady)
    {
        // Full composition only on scene entry, while RADIO_begin's screen is
        // still disabled. Later lines never turn video off or rewrite chrome.
        flush();portraitMap(P_DAMIAO,0,CPU);portraitMap(nextRemote,1,CPU);
        LOADING_setColors(16,lineColors,32,DMA);lineReady=TRUE;shownRemote=nextRemote;
    }
    else if(linePending)
    {
        // 186 text tiles + palettes + optional portrait map = at most 6088
        // bytes, below the NTSC 7200-byte VBlank DMA budget. Sources persist.
        LOADING_tiles(pixels+contentFirst*8,DYNAMIC+contentFirst,used-contentFirst,DMA_QUEUE);
        LOADING_setColors(16,lineColors,32,DMA_QUEUE);
        if(nextRemote!=shownRemote){portraitMap(nextRemote,1,DMA_QUEUE);shownRemote=nextRemote;}
    }
    else
    {
        const u16 first=grid[26*40+2];
        LOADING_tiles(pixels+(first-DYNAMIC)*8,first,22,DMA_QUEUE);
    }
    linePending=FALSE;
}
void RADIO_end(void)
{
    if(!radioActive)return;
    const bool enabled=VDP_getEnable();
    SPRITES_hide();SYS_doVBlankProcess();LOADING_setEnable(FALSE);
    MEM_free(pixels);MEM_free(grid);pixels=NULL;grid=NULL;radioActive=FALSE;
    ARENA_leave();VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    LOADING_setColors(0,savedRadioPal,64,DMA);TILEGEN_palette();ENEMYGFX_reset();
    LOADING_windowOff();VDP_setTextPlane(BG_A);VDP_setTextPriority(FALSE);LOADING_setEnable(enabled);
}
bool RADIO_handoffMission(void)
{
    if(!radioActive || !PANEL_beginMission(savedRadioPal))return FALSE;
    // Freeze the outgoing radio through WINDOW, referencing its existing
    // patterns. The new monitor is built elsewhere in VRAM under this cover.
    for(u16 y=0;y<28;y++)
    {
        u16 row[40];
        for(u16 x=0;x<40;x++)
        {
            row[x]=grid[y*40+x] ? TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,grid[y*40+x]) : 0;
            if(y>=18 && y<24)
            {
                if(x>=2 && x<8)row[x]=portraitMaps[0][(y-18)*6+x-2];
                if(x>=22 && x<28)row[x]=portraitMaps[1][(y-18)*6+x-22];
            }
        }
        VDP_setTileMapDataRow(WINDOW,row,y,0,40,CPU);LOADING_poll();
    }
    SYS_doVBlankProcess();VDP_setWindowFullScreen();
    MEM_free(pixels);MEM_free(grid);pixels=NULL;grid=NULL;radioActive=FALSE;
    return TRUE;
}
