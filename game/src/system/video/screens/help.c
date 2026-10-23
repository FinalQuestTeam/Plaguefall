#include "system/video/screens/help.h"
#include "system/video/screens/panel.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "enemies/enemies.h"
#include "insects.h"
#include "help_copy.h"
#define PAGES HELP_PAGE_COUNT
static u8 helpPage;
static void icon(u16 *row,u16 x,u16 tile)
{
    row[x]=TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+tile);
}
static void item(u16 *row,u16 y,u16 top,u16 tile)
{
    if(y>=top && y<top+2)
        for(u16 x=0;x<2;x++)icon(row,2+x,tile+x*2+y-top);
}
static void enemy(u16 *row,u16 y,u8 type,u16 top,u16 slot)
{
    const u16 nt=(ENEMY_DEFS[type]->size>32 ? 32 : ENEMY_DEFS[type]->size)/8;
    if(y>=top && y<top+nt)
        for(u16 x=0;x<nt;x++)row[2+x]=TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,PANEL_scratch()+slot*16+x*nt+y-top);
}
static void drawPage(bool full)
{
    // Queue the complete new overlay for VBlank. BG_B, the title and footer
    // stay visible while changing pages; no display blanking or extra heap.
    if(helpPage==3)
    {
        static const u8 types[]={ENEMY_SQ_RED,ENEMY_TRI_RED,ENEMY_PEN_RED};
        for(u16 i=0;i<3;i++)
            VDP_loadTileData((const u32 *)insect_icons+types[i]*128,PANEL_scratch()+i*16,16,DMA_QUEUE);
    }
    for(u16 y=0;y<28;y++)
    {
        if(!full && y!=2 && (y<5 || y>23))continue;
        u16 row[40]={0};
        for(u16 i=0;i<HELP_LINE_COUNT[helpPage];i++)
        {
            const HelpLine *l=&HELP_LINES[helpPage][i];
            if(l->y==y)for(u16 x=0;l->text[x] && l->x+x<40;x++)
                row[l->x+x]=TILE_ATTR_FULL(l->palette,TRUE,FALSE,FALSE,TILE_FONT_INDEX+l->text[x]-32);
        }
        if(helpPage==1){item(row,y,8,TILE_HEART);item(row,y,12,TILE_BULLET);item(row,y,16,TILE_BOOT);}
        if(helpPage==2){item(row,y,7,TILE_BOMB);item(row,y,10,TILE_SHIELD);item(row,y,13,TILE_CHAIN);item(row,y,16,TILE_ICE);item(row,y,19,TILE_FIRE);}
        if(helpPage==7)item(row,y,11,TILE_BAG);
        if(helpPage==3 || helpPage==4)
        {
            static const u16 colors[]={TILE_ICON_RED,TILE_ICON_YEL,TILE_ICON_PUR,TILE_ICON_ORG};
            for(u16 i=0;i<4;i++)if(y==8+i*(helpPage==3 ? 2 : 3))icon(row,2,colors[i]);
        }
        if(helpPage==3)
        {
            enemy(row,y,ENEMY_SQ_RED,17,0);enemy(row,y,ENEMY_TRI_RED,19,1);enemy(row,y,ENEMY_PEN_RED,21,2);
        }
        VDP_setTileMapDataRow(BG_A,row,y,0,40,DMA_QUEUE_COPY);
    }
}
void HELP_open(void)
{
    helpPage=0;PANEL_page("COMO JOGAR",NULL);
    PAL_setColors(PAL1*16,(const u16 *)insect_palette,16,DMA);
    drawPage(TRUE);
}
bool HELP_update(u16 pressed)
{
    if(pressed&(BUTTON_B|BUTTON_START))return TRUE;
    if(pressed&(BUTTON_RIGHT|BUTTON_A)){helpPage=(helpPage+1)%PAGES;drawPage(FALSE);}
    else if(pressed&BUTTON_LEFT){helpPage=(helpPage+PAGES-1)%PAGES;drawPage(FALSE);}
    return FALSE;
}
void HELP_run(void)
{
    if(!PANEL_begin())return;
    HELP_open();u16 prev=JOY_readJoypad(JOY_1);
    while(TRUE)
    {
        const u16 joy=JOY_readJoypad(JOY_1),pressed=joy&~prev;prev=joy;
        AUDIO_frameBegin();MUSIC_update();AUDIO_frameEnd();
        if(HELP_update(pressed))break;
        SYS_doVBlankProcess();
    }
    PANEL_end();
}
