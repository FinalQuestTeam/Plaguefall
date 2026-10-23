#include "system/video/screens/pause.h"
#include "system/video/screens/panel.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/help.h"
#include "core/game.h"
#include "core/objective.h"
#include "core/inventory.h"
#include "core/stats.h"
#include "levels/levels.h"
#include "levels/graph.h"
#include "actors/player.h"
#include "actors/bomb.h"
#include "actors/npc.h"
#include "actors/dinorah.h"
#include "actors/shots.h"
#include "enemies/enemies.h"
#include "items/items.h"
#include "levels/test.h"
static u16 pauseKills;
static u8 choice,pauseView,exitChoice;
static const char *itemName(u8 item)
{
    switch(item){case ITEM_BOMB:return "BOMBA";case ITEM_SHIELD:return "ESCUDO";case ITEM_CHAIN:return "RAIO";case ITEM_ICE:return "GELO";case ITEM_FIRE:return "FOGO";default:return "VAZIO";}
}
static void drawSelection(void)
{
    if(!currentLevel){TEST_pauseSelection(choice);return;}
    static const char *const options[]={"CONTINUAR","COMO JOGAR","VOLTAR AO TÍTULO"};
    char buf[32];
    PANEL_selection(17+choice*2);
    for(u16 i=0;i<3;i++){sprintf(buf,"%c %s",i==choice ? '>' : ' ',options[i]);PANEL_text(buf,2,17+i*2,i==choice ? PANEL_LIGHT : PANEL_BODY);}
}
static void drawMenu(void)
{
    if(!currentLevel){TEST_pauseDraw(choice);return;}
    char right[20],buf[64];
    if(currentLevel)sprintf(right,"FASE %s",GRAPH[currentLevel].name);
    else sprintf(right,"FASE TESTE %u",testStage);
    PANEL_page("PAUSADO",right);PANEL_text(MISSION_name(currentLevel),2,5,PANEL_ACCENT);
    PANEL_text("OBJETIVO",2,7,PANEL_ACCENT);MISSION_goal(buf,currentLevel);PANEL_wrap(buf,2,8,36,1,PANEL_BODY);
    PANEL_text("EM ANDAMENTO",2,11,PANEL_ACCENT);
    const LevelDef *def=LEVEL_current();
    if(currentLevel && GRAPH_isFinal(currentLevel))
    {
        u16 life=0;for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active && enemies[i].type==ENEMY_BOSS)life=enemies[i].hp;
        sprintf(buf,"ESCORPIÃO: %u DE %u DE VIDA",life,ENEMY_DEFS[ENEMY_BOSS]->hp);
    }
    else if(def->objective==OBJ_REACH)sprintf(buf,"TRAVESSIA: %u%% / SIGA A SETA",OBJECTIVE_progress());
    else if(def->objective==OBJ_ESCORT)sprintf(buf,"DINORAH: %u/100 / %s",dinorahHp,DINORAH_status());
    else if(def->objective==OBJ_PROTECT)sprintf(buf,"FALTAM %u S / SINAL: %u DE %u",OBJECTIVE_secondsLeft(),npcHp<0 ? 0 : npcHp,npcHpMax);
    else if(def->objective==OBJ_SURVIVE)sprintf(buf,"FALTAM %u SEGUNDOS",OBJECTIVE_secondsLeft());
    else if(def->objective==OBJ_COLLECT)sprintf(buf,"COLETADOS: %u DE %u",OBJECTIVE_collected(),def->objTarget);
    else if(currentLevel==N_9)sprintf(buf,"INIMIGOS: %u/%u / DANO NA FASE: %u",pauseKills,def->killTarget,phaseStats.damageTaken);
    else if(currentLevel==N_12)sprintf(buf,"INIMIGOS: %u/%u / TEMPO: %u S",pauseKills,def->killTarget,STATS_seconds());
    else sprintf(buf,"INIMIGOS: %u DE %u",pauseKills,def->killTarget);
    PANEL_wrap(buf,2,12,36,1,PANEL_BODY);
    sprintf(buf,"VIDA: %03u/100     BOMBAS: %u",hp<0 ? 0 : hp,BOMB_count());PANEL_text(buf,2,14,PANEL_BODY);
    u8 type,count;INV_view(INV_selected(),&type,&count);
    if(type==INV_EMPTY && SHOTS_modeCharges())
    {
        const char *mode=SHOTS_mode()==SHOTMODE_ICE ? "GELO" : SHOTS_mode()==SHOTMODE_FIRE ? "FOGO" : "RAIO";
        sprintf(buf,"TIRO ATIVO: %s (%u DISPAROS)",mode,SHOTS_modeCharges());
    }
    else if(type==INV_EMPTY)strcpy(buf,"ITEM SELECIONADO: VAZIO");
    else sprintf(buf,"ITEM SELECIONADO: %s (%u)",itemName(type),count);
    PANEL_text(buf,2,15,PANEL_BODY);
    drawSelection();
    PANEL_text("CIMA/BAIXO: ESCOLHER",2,24,PANEL_BODY);
    PANEL_right("A: CONFIRMAR   B/START: RETOMAR",26,PANEL_LIGHT);
}
static void drawExitSelection(void)
{
    PANEL_selection(exitChoice ? 19 : 16);
    PANEL_text(exitChoice ? "  CONTINUAR JOGANDO" : "> CONTINUAR JOGANDO",2,16,exitChoice ? PANEL_BODY : PANEL_LIGHT);
    PANEL_text(exitChoice ? "> SAIR PARA O TÍTULO" : "  SAIR PARA O TÍTULO",2,19,exitChoice ? PANEL_LIGHT : PANEL_BODY);
}
static void drawExit(void)
{
    PANEL_page("SAIR DA PARTIDA?",NULL);
    PANEL_text("O PROGRESSO DESTA PARTIDA",2,8,PANEL_BODY);PANEL_text("SERÁ PERDIDO.",2,10,PANEL_BODY);
    drawExitSelection();
    PANEL_text("CIMA/BAIXO: ESCOLHER",2,24,PANEL_BODY);
    PANEL_right("A: CONFIRMAR   B/START: CANCELAR",26,PANEL_LIGHT);
}
bool PAUSE_show(u16 kills)
{
    if(!PANEL_begin())return FALSE;
    pauseKills=kills;choice=pauseView=exitChoice=0;drawMenu();return TRUE;
}
u8 PAUSE_update(u16 pressed)
{
    if(pauseView==1){if(HELP_update(pressed)){pauseView=0;drawMenu();}return PAUSE_STAY;}
    if(pauseView==2)
    {
        if(pressed&(BUTTON_B|BUTTON_START)){pauseView=0;drawMenu();}
        else if(pressed&(BUTTON_UP|BUTTON_DOWN)){exitChoice^=1;drawExitSelection();}
        else if(pressed&BUTTON_A)
        {
            if(exitChoice){PANEL_end();return PAUSE_EXIT;}
            pauseView=0;drawMenu();
        }
        return PAUSE_STAY;
    }
    if(pressed&(BUTTON_B|BUTTON_START)){PANEL_end();return PAUSE_RESUME;}
    const u8 options=currentLevel ? 3 : 6;
    if(pressed&BUTTON_UP){choice=(choice+options-1)%options;drawSelection();}
    else if(pressed&BUTTON_DOWN){choice=(choice+1)%options;drawSelection();}
    else if(pressed&BUTTON_A)
    {
        if(!choice){PANEL_end();return PAUSE_RESUME;}
        if(!currentLevel) {
            if(choice<=3){PANEL_end();return choice==1 ? PAUSE_TEST_CONFIG : choice==2 ? PAUSE_TEST_RESTART : PAUSE_TEST_ROOM;}
            if(choice==4){pauseView=1;HELP_open();}
            else{pauseView=2;exitChoice=0;drawExit();}
            return PAUSE_STAY;
        }
        if(choice==1){pauseView=1;HELP_open();}
        else{pauseView=2;exitChoice=0;drawExit();}
    }
    return PAUSE_STAY;
}
