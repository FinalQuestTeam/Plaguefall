// One stable portrait and reading area on the approved resistance panel.
#include "system/video/screens/story.h"
#include "system/video/screens/panel.h"
#include "system/video/screens/mission.h"
#include "system/video/sprites/portraits_data.h"
#include "system/audio/music.h"
#include "system/audio/sfx.h"
#include "core/game.h"
#include "levels/graph.h"
static u32 seen[2];
static const StoryEntry *cur;
static u8 lineIdx,wrapLines;
static char wrapBuf[4][35];
static u16 typed,typeTotal;
void STORYSCR_reset(void){seen[0]=seen[1]=0;}
static void portrait(u8 which)
{
    PAL_setColors(PAL1*16,PORTRAIT_PAL[which],16,DMA);
    const char *const *art=PORTRAIT_ART[which];
    for(u16 tr=0;tr<6;tr++)for(u16 tc=0;tc<6;tc++)
    {
        u32 data[8]={0};
        for(u16 y=0;y<8;y++)for(u16 x=0;x<8;x++)
        {
            const char ch=art[tr*8+y][tc*8+x];
            const u16 color=ch<='9' ? ch-'0' : ch-'a'+10;
            data[y]|=(u32)color<<((7-x)*4);
        }
        const u16 tile=PANEL_scratch()+tr*6+tc;
        VDP_loadTileData(data,tile,1,DMA);
        VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,tile),2+tc,6+tr);
    }
}
static void wrapText(const char *text)
{
    wrapLines=0;typeTotal=0;
    while(*text && wrapLines<4)
    {
        while(*text==' ')text++;
        u16 len=0,space=0;
        while(text[len] && len<34){if(text[len]==' ')space=len;len++;}
        if(text[len] && text[len]!=' ' && space)len=space;
        memcpy(wrapBuf[wrapLines],text,len);wrapBuf[wrapLines][len]=0;
        typeTotal+=len;wrapLines++;text+=len;
    }
}
static void command(void)
{
    VDP_clearTextArea(2,24,36,1);
    const char *text=typed<typeTotal ? "A: MOSTRAR TEXTO" : lineIdx+1<cur->count ? "A: AVANCAR" : cur->when==ANTES ? "A: VER MISSAO" : "A: CONCLUIR";
    PANEL_text(text,2,24,PANEL_ACCENT);
}
static void startLine(void)
{
    char right[16],phase[16];sprintf(right,"%u/%u",lineIdx+1,cur->count);
    PANEL_page(MISSION_name(cur->node),right);
    const u8 who=cur->lines[lineIdx].portrait;portrait(who);
    PANEL_text(who==P_COMANDO ? "PADRE / RADIO" : PORTRAIT_NAME[who],10,7,PANEL_ACCENT);
    sprintf(phase,"FASE %s",GRAPH[cur->node].name);PANEL_text(phase,10,9,PANEL_BODY);
    wrapText(cur->lines[lineIdx].text);typed=0;
    command();PANEL_right("START: PULAR CENA",26,PANEL_LIGHT);
}
static void typeOne(void)
{
    u16 n=typed;
    for(u16 row=0;row<wrapLines;row++)
    {
        const u16 len=strlen(wrapBuf[row]);
        if(n<len){char glyph[2]={wrapBuf[row][n],0};PANEL_text(glyph,2+n,14+row*2,PANEL_BODY);typed++;return;}
        n-=len;
    }
}
bool STORYSCR_start(u8 node,u8 when)
{
    const StoryEntry *entry=STORY_find(node,when);
    if(!entry || (seen[when]&((u32)1<<node)))return FALSE;
    ARENA_leave();if(!PANEL_begin())return FALSE;
    cur=entry;lineIdx=0;seen[when]|=(u32)1<<node;MUSIC_setEnemies(0);startLine();return TRUE;
}
bool STORYSCR_update(u16 pressed)
{
    if(pressed&BUTTON_START){PANEL_end();return TRUE;}
    if(typed<typeTotal)
    {
        if(pressed&BUTTON_A)while(typed<typeTotal)typeOne();
        else{for(u16 i=0;i<2 && typed<typeTotal;i++)typeOne();if((typed&7)==0)sfxItemPickup();}
        if(typed==typeTotal)command();
        return FALSE;
    }
    if(pressed&BUTTON_A)
    {
        if(++lineIdx>=cur->count){PANEL_end();return TRUE;}
        startLine();
    }
    return FALSE;
}
