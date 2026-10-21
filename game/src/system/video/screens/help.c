#include "system/video/screens/help.h"
#include "system/video/screens/panel.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "enemies/enemies.h"
#include "insects.h"
#include "help_copy.h"
#define PAGES 6
static u8 helpPage;
static void icon(u16 x,u16 y,u16 tile)
{
    VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+tile),x,y);
}
static void item(u16 y,u16 tile)
{
    for(u16 x=0;x<2;x++)for(u16 row=0;row<2;row++)icon(2+x,y+row,tile+x*2+row);
}
static void drawPage(void)
{
    PANEL_page("COMO JOGAR",NULL);
    PAL_setColors(PAL1*16,(const u16 *)insect_palette,16,DMA);
    for(u16 i=0;i<HELP_LINE_COUNT[helpPage];i++)
    {
        const HelpLine *l=&HELP_LINES[helpPage][i];PANEL_text(l->text,l->x,l->y,l->palette);
    }
    if(helpPage==1){item(8,TILE_HEART);item(12,TILE_BULLET);item(16,TILE_BOOT);}
    if(helpPage==2){item(7,TILE_BOMB);item(10,TILE_SHIELD);item(13,TILE_CHAIN);item(16,TILE_ICE);item(19,TILE_FIRE);}
    if(helpPage==3)
    {
        static const u16 colors[]={TILE_ICON_RED,TILE_ICON_YEL,TILE_ICON_PUR,TILE_ICON_ORG};
        for(u16 i=0;i<4;i++)icon(2,8+i*2,colors[i]);
        PANEL_enemy(ENEMY_SQ_RED,2,17,0);PANEL_enemy(ENEMY_TRI_RED,2,19,1);PANEL_enemy(ENEMY_PEN_RED,2,21,2);
    }
    if(helpPage==4)
    {
        static const u16 colors[]={TILE_ICON_RED,TILE_ICON_YEL,TILE_ICON_PUR,TILE_ICON_ORG};
        for(u16 i=0;i<4;i++)icon(2,8+i*3,colors[i]);
    }
}
void HELP_open(void){helpPage=0;drawPage();}
bool HELP_update(u16 pressed)
{
    if(pressed&(BUTTON_B|BUTTON_START))return TRUE;
    if(pressed&(BUTTON_RIGHT|BUTTON_A)){helpPage=(helpPage+1)%PAGES;drawPage();}
    else if(pressed&BUTTON_LEFT){helpPage=(helpPage+PAGES-1)%PAGES;drawPage();}
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
