#include "system/video/screens/loading.h"
// Shared opaque artwork + transparent text. Restore borrowed VRAM byte-for-byte;
// never reset a level, actor cache or simulation timer when leaving a panel.
#include "system/video/screens/panel.h"
#include "system/video/screens/panel_data.h"
#include "system/video/sprites/tiles.h"
#include "system/video/spritelist.h"
#include "system/video/tilegen.h"
#include "interface_data.h"
#include "radio_panel.h"
#include "system/video/screens/radio_panel_data.h"
#include "system/video/screens/radio_colors.h"
#include "insects.h"
#include "text_data.h"
#include "enemies/enemies.h"
#define BASE (TILE_USER_INDEX + NUM_TILES)
#define SCRATCH (BASE + PANEL_TILE_COUNT)
#define SCRATCH_TILES 112
#define PATTERN_WORDS ((PANEL_TILE_COUNT + SCRATCH_TILES)*16)
#define MAP_WORDS (64*32)
#define FONT_WORDS (96*16)
#define SAVE_WORDS (PATTERN_WORDS + MAP_WORDS*2 + FONT_WORDS)
#define MISSION_BASE 832
#define MISSION_SCRATCH (MISSION_BASE+RADIO_PANEL_TILE_COUNT)
typedef char panel_fits[(SCRATCH+SCRATCH_TILES <= 1440) ? 1 : -1];
typedef char mission_fits[(MISSION_SCRATCH+SCRATCH_TILES <= 1440) ? 1 : -1];
static u16 *saved;
static u16 *missionMap;
static u16 missionColors[64];
static bool missionBackdrop;
static bool displayAfterPage;
static u16 palette[64], scroll[4], oldPalette, oldPriority;
static VDPPlane oldPlane;
static u8 oldWindowX,oldWindowY,oldAuto;
static u16 selection;
static void readWords(u16 addr,u16 *dest,u16 count,u32 command)
{
    volatile u16 *data=(u16 *)VDP_DATA_PORT;
    volatile u32 *ctrl=(u32 *)VDP_CTRL_PORT;
    SYS_disableInts();VDP_setAutoInc(2);*ctrl=command;
    u16 address=addr;
    const bool vram=command==VDP_READ_VRAM_ADDR(addr);
    if(!vram){while(count--)*dest++=*data;SYS_enableInts();return;}
    while(count) {
        const u16 chunk=count>128 ? 128 : count;
        for(u16 i=0;i<chunk;i++)*dest++=*data;
        count-=chunk;SYS_enableInts();LOADING_poll();
        // VBlank/DMA may change the VDP address and auto-increment.
        address+=chunk*2;
        if(count){SYS_disableInts();VDP_setAutoInc(2);*ctrl=VDP_READ_VRAM_ADDR(address);}
    }
}
bool PANEL_begin(void)
{
    if(saved)return TRUE;
    u16 *memory=MEM_alloc(SAVE_WORDS*2);
    if(!memory)return FALSE;
    displayAfterPage=VDP_getEnable();
    while(PAL_isDoingFade())SYS_doVBlankProcess();
    SPRITES_hide();SYS_doVBlankProcess();LOADING_setEnable(FALSE);
    saved=memory;
    oldWindowX=VDP_getReg(17);oldWindowY=VDP_getReg(18);oldAuto=VDP_getReg(15);
    oldPlane=VDP_getTextPlane();oldPalette=VDP_getTextPalette();oldPriority=VDP_getTextPriority();
    LOADING_getColors(0,palette,64);
    readWords(TILE_FONT_INDEX*32,saved+PATTERN_WORDS+MAP_WORDS*2,FONT_WORDS,VDP_READ_VRAM_ADDR(TILE_FONT_INDEX*32));
    // Same 96 tiles as gameplay; transparent Portuguese glyphs require no
    // temporary unpack allocation after reserving the panel snapshot.
    VDP_loadFontData((const u32 *)text_font,FONT_LENGTH,DMA);
    readWords(BASE*32,saved,PATTERN_WORDS,VDP_READ_VRAM_ADDR(BASE*32));
    readWords(VDP_BG_A,saved+PATTERN_WORDS,MAP_WORDS,VDP_READ_VRAM_ADDR(VDP_BG_A));
    readWords(VDP_BG_B,saved+PATTERN_WORDS+MAP_WORDS,MAP_WORDS,VDP_READ_VRAM_ADDR(VDP_BG_B));
    readWords(VDP_HSCROLL_TABLE,scroll,2,VDP_READ_VRAM_ADDR(VDP_HSCROLL_TABLE));
    readWords(0,scroll+2,2,VDP_READ_VSRAM_ADDR(0));
    LOADING_windowOff();VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_setTextPlane(BG_A);VDP_setTextPriority(TRUE);
    LOADING_tiles((const u32 *)interface_tiles,BASE,PANEL_TILE_COUNT,DMA);
    LOADING_setColors(PAL3*16,(const u16 *)interface_palette,16,DMA);
    LOADING_setColor(15,RGB24_TO_VDPCOLOR(0x301C10));
    LOADING_setColor(PAL2*16+15,RGB24_TO_VDPCOLOR(0x6D2400));
    selection=0;
    return TRUE;
}
bool PANEL_isMission(void){return missionMap!=NULL;}
bool PANEL_beginMission(const u16 *returnColors)
{
    if(missionMap)return TRUE;
    missionMap=MEM_alloc(40*28*2+512);
    if(!missionMap)return FALSE;
    if(returnColors)memcpy(palette,returnColors,sizeof palette);
    else LOADING_getColors(0,palette,64);
    memcpy(missionColors,palette,sizeof palette);
    memcpy(missionColors+16,insect_palette,32);
    memcpy(missionColors+32,interface_palette,32);
    memcpy(missionColors+48,radio_panel_palette,32);
    missionColors[15]=RADIO_BODY_COLOR;
    missionColors[47]=RADIO_TITLE_COLOR;
    missionColors[63]=RADIO_TITLE_COLOR;
    missionBackdrop=FALSE;
    // The old radio uses tiles below 808. This font and the new background
    // can be prepared without changing a single pixel of its visible cover.
    LOADING_tiles((const u32 *)text_font,TILE_FONT_INDEX,FONT_LENGTH,DMA);
    VDP_setTextPlane(BG_A);VDP_setTextPriority(TRUE);
    return TRUE;
}
void PANEL_end(void)
{
    if(missionMap)
    {
        // The loading WINDOW already covers the mission. Restore only the
        // destination palette; the incoming arena replaces its own graphics.
        MEM_free(missionMap);missionMap=NULL;missionBackdrop=FALSE;
        LOADING_setColors(0,palette,64,DMA);
        TILEGEN_palette();
        return;
    }
    if(!saved)return;
    const bool enabled=VDP_getEnable();
    SYS_doVBlankProcess();LOADING_setEnable(FALSE);
    LOADING_copyVRAM(saved,BASE*32,PATTERN_WORDS);
    LOADING_copyVRAM(saved+PATTERN_WORDS,VDP_BG_A,MAP_WORDS);
    LOADING_copyVRAM(saved+PATTERN_WORDS+MAP_WORDS,VDP_BG_B,MAP_WORDS);
    LOADING_copyVRAM(saved+PATTERN_WORDS+MAP_WORDS*2,TILE_FONT_INDEX*32,FONT_WORDS);
    LOADING_setColors(0,palette,64,DMA);
    VDP_setHorizontalScroll(BG_A,(s16)scroll[0]);VDP_setHorizontalScroll(BG_B,(s16)scroll[1]);
    VDP_setVerticalScroll(BG_A,(s16)scroll[2]);VDP_setVerticalScroll(BG_B,(s16)scroll[3]);
    if(!LOADING_active()){VDP_setReg(17,oldWindowX);VDP_setReg(18,oldWindowY);}
    VDP_setAutoInc(oldAuto);
    VDP_setTextPlane(oldPlane);VDP_setTextPalette(oldPalette);VDP_setTextPriority(oldPriority);
    MEM_free(saved);saved=NULL;selection=0;LOADING_setEnable(enabled);
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
    LOADING_setEnable(FALSE);VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    artRows(0,28);selection=0;
    PANEL_text(title,2,2,PANEL_ACCENT);
    if(right)PANEL_right(right,2,PANEL_BODY);
    LOADING_setEnable(displayAfterPage);
}
void PANEL_radioPage(const char *title,const char *right)
{
    if(!missionMap)return;
    memset(missionMap,0,40*28*2);
    if(!missionBackdrop)
    {
        LOADING_tiles((const u32 *)radio_panel_tiles,MISSION_BASE,RADIO_PANEL_TILE_COUNT,DMA);
        const u16 *map=(const u16 *)radio_panel_map;
        for(u16 y=0;y<28;y++)
        {
            u16 row[40];
            for(u16 x=0;x<40;x++)row[x]=TILE_ATTR_FULL(PAL3,FALSE,FALSE,FALSE,MISSION_BASE+map[y*40+x]);
            VDP_setTileMapDataRow(BG_B,row,y,0,40,CPU);LOADING_poll();
        }
        missionBackdrop=TRUE;
    }
    selection=0;
    PANEL_text(title,2,2,PANEL_ACCENT);
    if(right)PANEL_right(right,2,PANEL_BODY);
}
void PANEL_radioCell(u16 attr,u16 x,u16 y)
{
    if(missionMap && x<40 && y<28)missionMap[y*40+x]=attr;
}
void PANEL_radioPortrait(const u32 *source)
{
    if(!missionMap)return;
    u32 *opaque=(u32 *)(missionMap+40*28);
    // Object colour A is exactly the old portrait backing (paper colour E).
    // Resolve transparent pixels into that same brown at upload time, so the
    // visible portrait remains pixel-identical without changing BG_B per page.
    for(u16 i=0;i<128;i++)
    {
        u32 row=source[i];
        for(u16 shift=0;shift<32;shift+=4)if(!(row&(15UL<<shift)))row|=10UL<<shift;
        opaque[i]=row;
    }
    VDP_loadTileData(opaque,MISSION_SCRATCH,16,DMA_QUEUE);
}
void PANEL_radioCommit(void)
{
    if(!missionMap)return;
    // Persistent source rows and ROM portrait data are submitted together.
    // Under 3 KiB per page: the old content remains until this single VBlank.
    for(u16 y=0;y<28;y++)VDP_setTileMapDataRow(BG_A,missionMap+y*40,y,0,40,DMA_QUEUE);
    PAL_setColors(0,missionColors,64,DMA_QUEUE);
    SYS_doVBlankProcess();
    VDP_setWindowOff();
}
void PANEL_text(const char *text,u16 x,u16 y,u16 pal)
{
    if(missionMap)
    {
        for(u16 i=0;text[i] && x+i<40;i++)
            PANEL_radioCell(TILE_ATTR_FULL(pal,TRUE,FALSE,FALSE,TILE_FONT_INDEX+(u8)text[i]-32),x+i,y);
        return;
    }
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
u16 PANEL_scratch(void){return missionMap ? MISSION_SCRATCH : SCRATCH;}
void PANEL_enemy(u8 type,u16 x,u16 y,u16 slot)
{
    const u16 tile=SCRATCH+slot*16;
    LOADING_tiles((const u32 *)insect_icons+type*128,tile,16,DMA);
    const u16 nt=(ENEMY_DEFS[type]->size>32 ? 32 : ENEMY_DEFS[type]->size)/8;
    for(u16 col=0;col<nt;col++)for(u16 row=0;row<nt;row++)
        VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,tile+col*nt+row),x+col,y+row);
}
