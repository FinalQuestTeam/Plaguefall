// Two fixed console portraits; the authored side determines the lit speaker.
#include "system/video/screens/story.h"
#include "system/video/screens/radio.h"
#include "system/video/screens/mission.h"
#include "system/audio/music.h"
#include "system/audio/sfx.h"
#include "core/game.h"
#include "levels/graph.h"
static u32 seen[2];
static const StoryEntry *cur;
static u8 lineIdx,wrapLines;
static char wrapBuf[4][27];
static u8 radioRemote;
static u16 typed,typeTotal;
void STORYSCR_reset(void){seen[0]=seen[1]=0;}
static void wrapText(const char *text)
{
    wrapLines=0;typeTotal=0;
    while(*text && wrapLines<4)
    {
        while(*text==' ')text++;
        u16 len=0,space=0;
        while(text[len] && len<26){if(text[len]==' ')space=len;len++;}
        if(text[len] && text[len]!=' ' && space)len=space;
        memcpy(wrapBuf[wrapLines],text,len);wrapBuf[wrapLines][len]=0;
        typeTotal+=len;wrapLines++;text+=len;
    }
}
static void command(void)
{
    const char *text=typed<typeTotal ? "A: MOSTRAR TEXTO" : lineIdx+1<cur->count ? "A: AVANÇAR" : cur->when==ANTES ? "A: VER MISSÃO" : "A: CONCLUIR";
    RADIO_command(text);
}
static void startLine(void)
{
    const StoryLine *line=&cur->lines[lineIdx];
    if(line->side==LADO_DIR)radioRemote=line->portrait;
    RADIO_line(line->side,radioRemote,lineIdx+1,cur->count);
    wrapText(cur->lines[lineIdx].text);typed=0;
    command();
}
static void typeOne(void)
{
    u16 n=typed;
    for(u16 row=0;row<wrapLines;row++)
    {
        const u16 len=strlen(wrapBuf[row]);
        if(n<len){char glyph[2]={wrapBuf[row][n],0};RADIO_glyph(glyph[0],n,row);typed++;return;}
        n-=len;
    }
}
bool STORYSCR_start(u8 node,u8 when)
{
    const StoryEntry *entry=STORY_find(node,when);
    if(!entry || (seen[when]&((u32)1<<node)))return FALSE;
    const bool enabled=VDP_getEnable();
    if(!RADIO_begin(node))return FALSE;
    radioRemote=P_COMANDO;
    for(u16 i=0;i<entry->count;i++)if(entry->lines[i].side==LADO_DIR){radioRemote=entry->lines[i].portrait;break;}
    cur=entry;lineIdx=0;seen[when]|=(u32)1<<node;MUSIC_setEnemies(0);startLine();VDP_setEnable(enabled);return TRUE;
}
bool STORYSCR_update(u16 pressed)
{
    if(pressed&BUTTON_START)return TRUE;
    if(typed<typeTotal)
    {
        if(pressed&BUTTON_A)while(typed<typeTotal)typeOne();
        else{for(u16 i=0;i<2 && typed<typeTotal;i++)typeOne();if(typed && (typed&7)==0)SFX_radioTick();}
        if(typed==typeTotal)command();
        return FALSE;
    }
    if(pressed&BUTTON_A)
    {
        if(lineIdx+1>=cur->count)return TRUE;
        lineIdx++;
        startLine();
    }
    return FALSE;
}
void STORYSCR_close(void){RADIO_end();}
bool STORYSCR_closeToMission(void){return RADIO_handoffMission();}
