#include "system/video/screens/signal.h"
#include "system/video/screens/panel.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/loading.h"
#include "system/audio/audio.h"
#include "system/audio/music.h"
#include "core/game.h"
#include "levels/graph.h"
#include "signal_icons.h"

static const char *const names[SIGNAL_SYMBOLS]={
    "MANDACARU","ENGRENAGEM","SANTA","SAÚVA",
    "CHAPÉU","RÁDIO","CAPELA","MUTUCA",
    "BARRO","FOGUETE","EX-VOTO","ESCORPIÃO",
    "CORDEL","ALICATE","SINO","SINDICATO"
};
static u8 entered[SIGNAL_LENGTH],selected;
static u8 signalView; //0 editing,1 invalid,2 resume confirmation (observable in emulator)
static void text(const char *s,u16 row,u16 pal)
{PANEL_text(s,(40-strlen(s))/2,row,pal);}
static void page(const char *title)
{
    if(PANEL_isMission())PANEL_radioPage(title,NULL);
    else PANEL_page(title,NULL);
}
static void present(void){if(PANEL_isMission())PANEL_radioCommit();}
static void symbols(const u8 *code,bool editing)
{
    for(u8 i=0;i<SIGNAL_LENGTH;i++)
    {
        const u16 x=i&1 ? 26 : 8,y=6+(i/2)*6;
        const char *name=names[code[i]];
        char number[3];sprintf(number,"%u",i+1);PANEL_text(number,x-3,y+1,PANEL_BODY);
        PANEL_icon32((const u32 *)signal_icons+code[i]*128,x,y,i);
        PANEL_text(name,x+2-strlen(name)/2,y+4,editing && i==selected ? PANEL_LIGHT : PANEL_ACCENT);
        if(editing && i==selected)PANEL_text(">",x-2,y+2,PANEL_LIGHT);
    }
}
bool SIGNALSCR_checkpoint(void)
{
    SignalProgress p;u8 code[SIGNAL_LENGTH];
    if(!SIGNAL_checkpoint(&p) || !SIGNAL_encode(&p,code))return FALSE;
    page("SINAL DO ÚLTIMO CHÃO");text("FOTOGRAFE OU ANOTE A SEQUÊNCIA",4,PANEL_BODY);
    symbols(code,FALSE);
    char line[40];sprintf(line,"FASE %s / INÍCIO DA FASE",GRAPH[p.node].name);text(line,24,PANEL_BODY);
    text(PANEL_isMission() ? "A/START: VER MISSÃO" : "A/B/START: VOLTAR",26,PANEL_LIGHT);
    present();return TRUE;
}
static void drawInput(void)
{
    page("SINTONIZAR");
    text(signalView==1 ? "SINAL INVÁLIDO. CONFIRA A SEQUÊNCIA." : "MONTE A SEQUÊNCIA DO SEU SINAL",4,signalView==1 ? PANEL_ACCENT : PANEL_BODY);
    symbols(entered,TRUE);
    text("ESQ/DIR: POSIÇÃO  CIMA/BAIXO: SINAL",24,PANEL_BODY);
    text("A: CONFERIR   B: VOLTAR",26,PANEL_LIGHT);present();
}
static void drawConfirm(const SignalProgress *p)
{
    char line[40];page("SINAL RECONHECIDO");
    PANEL_icon32((const u32 *)signal_icons+5*128,18,6,0);
    sprintf(line,"FASE %s / ETAPA %u DE 16",GRAPH[p->node].name,GRAPH[p->node].mapCol+1);text(line,12,PANEL_ACCENT);
    text(MISSION_name(p->node),14,PANEL_BODY);
    text("RETOMAR DO INÍCIO DA FASE",17,PANEL_ACCENT);
    text("VIDA CHEIA E DUAS BOMBAS",19,PANEL_BODY);
    sprintf(line,"TIRO: %u / VELOCIDADE: +%u%s",p->power,p->speed*20,"%");text(line,21,PANEL_BODY);
    text("A/START: CONTINUAR   B: EDITAR",26,PANEL_LIGHT);present();
}
bool SIGNALSCR_read(SignalProgress *progress)
{
    if(!progress || !PANEL_beginMission(NULL))return FALSE;
    for(u8 i=0;i<SIGNAL_LENGTH;i++)entered[i]=0;
    selected=signalView=0;drawInput();VDP_setEnable(TRUE);
    u16 previous=JOY_readJoypad(JOY_1),lock=fps*3/10;SignalProgress decoded;
    bool accepted=FALSE,done=FALSE;
    while(!done)
    {
        const u16 joy=JOY_readJoypad(JOY_1),pressed=joy&~previous;previous=joy;
        AUDIO_frameBegin();MUSIC_update();AUDIO_frameEnd();
        if(lock)lock--;
        else if(signalView==2)
        {
            if(pressed&BUTTON_B){signalView=0;drawInput();}
            else if(pressed&(BUTTON_A|BUTTON_START)){*progress=decoded;accepted=done=TRUE;}
        }
        else if(pressed&BUTTON_B)done=TRUE;
        else if(pressed&(BUTTON_A|BUTTON_START))
        {
            if(SIGNAL_decode(entered,&decoded)){signalView=2;drawConfirm(&decoded);}
            else{signalView=1;drawInput();}
        }
        else if(pressed&(BUTTON_LEFT|BUTTON_RIGHT|BUTTON_UP|BUTTON_DOWN))
        {
            signalView=0;
            if(pressed&BUTTON_LEFT)selected=(selected+SIGNAL_LENGTH-1)%SIGNAL_LENGTH;
            else if(pressed&BUTTON_RIGHT)selected=(selected+1)%SIGNAL_LENGTH;
            else if(pressed&BUTTON_UP)entered[selected]=(entered[selected]+SIGNAL_SYMBOLS-1)%SIGNAL_SYMBOLS;
            else entered[selected]=(entered[selected]+1)%SIGNAL_SYMBOLS;
            drawInput();
        }
        SYS_doVBlankProcess();
    }
    VDP_setEnable(FALSE);PANEL_end();VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);VDP_setEnable(TRUE);
    return accepted;
}
