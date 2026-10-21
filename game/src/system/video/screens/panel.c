// Shared opaque artwork + transparent text. Restore borrowed VRAM byte-for-byte;
// never reset a level, actor cache or simulation timer when leaving a panel.
#include "system/video/screens/panel.h"
#include "system/video/screens/panel_data.h"
#include "system/video/sprites/tiles.h"
#include "system/video/spritelist.h"
#include "interface_data.h"
#include "insects.h"
#include "enemies/enemies.h"
#define BASE (TILE_USER_INDEX + NUM_TILES)
#define SCRATCH (BASE + PANEL_TILE_COUNT)
#define SCRATCH_TILES 112
#define PATTERN_WORDS ((PANEL_TILE_COUNT + SCRATCH_TILES)*16)
#define MAP_WORDS (64*32)
#define FONT_WORDS (96*16)
#define SAVE_WORDS (PATTERN_WORDS + MAP_WORDS*2 + FONT_WORDS)
typedef char panel_fits[(SCRATCH+SCRATCH_TILES <= 1440) ? 1 : -1];
static u16 *saved;
static u16 palette[64], scroll[4], oldPalette, oldPriority;
static VDPPlane oldPlane;
static u8 oldWindowX,oldWindowY,oldAuto;
static u16 selection;
static void readWords(u16 addr,u16 *dest,u16 count,u32 command)
{
    volatile u16 *data=(u16 *)VDP_DATA_PORT;
    volatile u32 *ctrl=(u32 *)VDP_CTRL_PORT;
    SYS_disableInts();VDP_setAutoInc(2);*ctrl=command;
    (void)addr;
    while(count--)*dest++=*data;
    SYS_enableInts();
}
bool PANEL_begin(void)
{
    if(saved)return TRUE;
    u16 *memory=MEM_alloc(SAVE_WORDS*2);
    if(!memory)return FALSE;
    while(PAL_isDoingFade())SYS_doVBlankProcess();
    SPRITES_hide();SYS_doVBlankProcess();VDP_setEnable(FALSE);
    saved=memory;
    oldWindowX=VDP_getReg(17);oldWindowY=VDP_getReg(18);oldAuto=VDP_getReg(15);
    oldPlane=VDP_getTextPlane();oldPalette=VDP_getTextPalette();oldPriority=VDP_getTextPriority();
    PAL_getColors(0,palette,64);
    readWords(BASE*32,saved,PATTERN_WORDS,VDP_READ_VRAM_ADDR(BASE*32));
    readWords(VDP_BG_A,saved+PATTERN_WORDS,MAP_WORDS,VDP_READ_VRAM_ADDR(VDP_BG_A));
    readWords(VDP_BG_B,saved+PATTERN_WORDS+MAP_WORDS,MAP_WORDS,VDP_READ_VRAM_ADDR(VDP_BG_B));
    readWords(TILE_FONT_INDEX*32,saved+PATTERN_WORDS+MAP_WORDS*2,FONT_WORDS,VDP_READ_VRAM_ADDR(TILE_FONT_INDEX*32));
    readWords(VDP_HSCROLL_TABLE,scroll,2,VDP_READ_VRAM_ADDR(VDP_HSCROLL_TABLE));
    readWords(0,scroll+2,2,VDP_READ_VSRAM_ADDR(0));
    VDP_setWindowOff();VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_setTextPlane(BG_A);VDP_setTextPriority(TRUE);
    VDP_loadDefaultFont(DMA);
    VDP_loadTileData((const u32 *)interface_tiles,BASE,PANEL_TILE_COUNT,DMA);
    PAL_setColors(PAL3*16,(const u16 *)interface_palette,16,DMA);
    PAL_setColor(15,RGB24_TO_VDPCOLOR(0x301C10));
    PAL_setColor(PAL2*16+15,RGB24_TO_VDPCOLOR(0x6D2400));
    selection=0;
    return TRUE;
}
void PANEL_end(void)
{
    if(!saved)return;
    SYS_doVBlankProcess();VDP_setEnable(FALSE);
    DMA_doDma(DMA_VRAM,saved,BASE*32,PATTERN_WORDS,2);
    DMA_doDma(DMA_VRAM,saved+PATTERN_WORDS,VDP_BG_A,MAP_WORDS,2);
    DMA_doDma(DMA_VRAM,saved+PATTERN_WORDS+MAP_WORDS,VDP_BG_B,MAP_WORDS,2);
    DMA_doDma(DMA_VRAM,saved+PATTERN_WORDS+MAP_WORDS*2,TILE_FONT_INDEX*32,FONT_WORDS,2);
    PAL_setColors(0,palette,64,DMA);
    VDP_setHorizontalScroll(BG_A,(s16)scroll[0]);VDP_setHorizontalScroll(BG_B,(s16)scroll[1]);
    VDP_setVerticalScroll(BG_A,(s16)scroll[2]);VDP_setVerticalScroll(BG_B,(s16)scroll[3]);
    VDP_setReg(17,oldWindowX);VDP_setReg(18,oldWindowY);VDP_setAutoInc(oldAuto);
    VDP_setTextPlane(oldPlane);VDP_setTextPalette(oldPalette);VDP_setTextPriority(oldPriority);
    MEM_free(saved);saved=NULL;selection=0;VDP_setEnable(TRUE);
}
static void artRows(u16 top,u16 count)
{
    for(u16 y=top;y<top+count;y++)
    {
        u16 row[40];
        for(u16 x=0;x<40;x++)row[x]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,BASE+((const u16 *)interface_map)[y*40+x]);
        VDP_setTileMapDataRow(BG_B,row,y,0,40,CPU);
    }
}
void PANEL_page(const char *title,const char *right)
{
    VDP_setEnable(FALSE);VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    artRows(0,28);selection=0;
    PANEL_text(title,2,2,PANEL_ACCENT);
    if(right)PANEL_right(right,2,PANEL_BODY);
    VDP_setEnable(TRUE);
}
void PANEL_text(const char *text,u16 x,u16 y,u16 pal)
{
    VDP_setTextPalette(pal);VDP_drawText(text,x,y);VDP_setTextPalette(PAL0);
}
void PANEL_right(const char *text,u16 y,u16 pal)
{
    PANEL_text(text,38-strlen(text),y,pal);
}
void PANEL_wrap(const char *text,u16 x,u16 y,u16 width,u16 step,u16 pal)
{
    if(!text)return;
    while(*text && y<24)
    {
        while(*text==' ')text++;
        u16 len=0,space=0;char line[37];
        while(text[len] && len<width){if(text[len]==' ')space=len;len++;}
        if(text[len] && text[len]!=' ' && space)len=space;
        memcpy(line,text,len);line[len]=0;PANEL_text(line,x,y,pal);
        text+=len;y+=step;
    }
}
void PANEL_selection(u16 row)
{
    if(selection)artRows(selection-1,2);
    selection=row;
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,TILE_SYSTEM_INDEX+PANEL_RUST_INDEX),1,row-1,38,2);
}
u16 PANEL_scratch(void){return SCRATCH;}
void PANEL_enemy(u8 type,u16 x,u16 y,u16 slot)
{
    const u16 tile=SCRATCH+slot*16;
    VDP_loadTileData((const u32 *)insect_icons+type*128,tile,16,DMA);
    const u16 nt=(ENEMY_DEFS[type]->size>32 ? 32 : ENEMY_DEFS[type]->size)/8;
    for(u16 col=0;col<nt;col++)for(u16 row=0;row<nt;row++)
        VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,tile+col*nt+row),x+col,y+row);
}
