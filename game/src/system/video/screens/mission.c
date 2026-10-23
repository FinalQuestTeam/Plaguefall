#include "system/video/screens/mission.h"
#include "system/video/screens/panel.h"
#include "levels/graph.h"
#include "core/objective.h"
#include "core/game.h"
#include "mission_copy.h"
#include "enemies/enemies.h"
#include "levels/test.h"
#include "insects.h"
#include "mission_art.h"
#include "mission_guide.h"

static u8 missionNode,guidePage;
static bool guideOpen;

// One portrait uses scratch slot 0. Six decorative tiles occupy the last
// slot of the existing panel loan, so help and gameplay keep their own art.
#define DECOR (PANEL_scratch()+96)
static const u32 missionDecor[6][8] = {
    {0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE},
    {0xFFFFFFFF,0xFCCCCCCC,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE},
    {0xFFFFFFFF,0xCCCCCCCC,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE,0xEEEEEEEE},
    {0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE,0xFCEEEEEE},
    {0,0,0,0xCCCCCCCC,0xFFFFFFFF,0,0,0},
    {0,0x000CC000,0x0CCCCCC0,0x0CFFFFC0,0x0CFFFFC0,0x00CFFC00,0x000CC000,0},
};
static void decor(u16 tile,u16 x,u16 y,bool flipX,bool flipY)
{
    PANEL_radioCell(TILE_ATTR_FULL(PAL2,TRUE,flipY,flipX,DECOR+tile),x,y);
}
static void rule(u16 y)
{
    for(u16 x=2;x<38;x++)PANEL_radioCell(TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,DECOR+4),x,y);
}
static void portraitArt(u8 type,u16 top)
{
    PANEL_radioPortrait((const u32 *)mission_portraits+type*128);
    for(u16 x=0;x<4;x++)for(u16 y=0;y<4;y++)
        PANEL_radioCell(TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,PANEL_scratch()+x*4+y),3+x,top+1+y);
}
static void portrait(u8 type,u16 top)
{
    for(u16 y=top;y<top+6;y++)for(u16 x=2;x<8;x++)
        PANEL_radioCell(TILE_ATTR_FULL(PAL2,TRUE,FALSE,FALSE,DECOR),x,y);
    for(u16 i=1;i<5;i++)
    {
        decor(2,2+i,top,FALSE,FALSE);decor(2,2+i,top+5,FALSE,TRUE);
        decor(3,2,top+i,FALSE,FALSE);decor(3,7,top+i,TRUE,FALSE);
    }
    decor(1,2,top,FALSE,FALSE);decor(1,7,top,TRUE,FALSE);
    decor(1,2,top+5,FALSE,TRUE);decor(1,7,top+5,TRUE,TRUE);
    portraitArt(type,top);
}
static void page(const char *title,const char *right)
{
    PANEL_radioPage(title,right);
    VDP_loadTileData((const u32 *)missionDecor,DECOR,6,DMA);
    PANEL_text(MISSION_name(missionNode),2,5,PANEL_ACCENT);
}
static void enemyCard(u8 type,u16 top)
{
    const EnemyLesson *lesson=&ENEMY_LESSONS[type];
    portrait(type,top);
    PANEL_text(lesson->name,10,top,PANEL_ACCENT);
    if(ENEMY_DEFS[type]->color==COLOR_PURPLE || type==ENEMY_BOSS)
    {
        PANEL_radioCell(TILE_ATTR_FULL(PAL3,TRUE,FALSE,FALSE,DECOR+5),10,top+2);
        PANEL_text(lesson->behavior,12,top+2,PANEL_BODY);
    }
    else PANEL_text(lesson->behavior,10,top+2,PANEL_BODY);
    PANEL_wrap(lesson->tactic,10,top+4,28,1,PANEL_BODY);
}
// Deduplicate the real roster rather than maintaining a second enemy list.
static u8 guideEnemies(u8 *types)
{
    const LevelDef *def=GRAPH[missionNode].def;
    u16 seen=0;u8 count=0;
    for(u16 i=0;i<def->enemyTypeCount;i++)
    {
        const u8 type=def->enemyTypes[i];
        if(seen&(1<<type))continue;
        seen|=1<<type;types[count++]=type;
    }
    return count;
}
const char *MISSION_name(u8 node){return node ? MISSION_COPY[node].name : "ÁREA DE TREINAMENTO";}
void MISSION_goal(char *text,u8 node)
{
    if(!node){TEST_goal(text);return;}
    const LevelDef *def=node ? GRAPH[node].def : LEVEL_current();
    if(node && GRAPH_isFinal(node))strcpy(text,"DERROTE O ESCORPIÃO.");
    else if(def->objective==OBJ_PROTECT)sprintf(text,"PROTEJA O SINALIZADOR POR %u S.",def->objTarget);
    else if(def->objective==OBJ_KILL)sprintf(text,"ELIMINE %u INIMIGOS.",def->killTarget);
    else OBJECTIVE_prepText(text,def);
}
static void drawMission(void)
{
    char title[16],right[20],goal[48];
    const MissionCopy *copy=&MISSION_COPY[missionNode];
    sprintf(title,"FASE %s",GRAPH[missionNode].name);
    sprintf(right,"ETAPA %u/16",GRAPH[missionNode].mapCol+1);
    page(title,right);
    PANEL_text("SUA MISSÃO",2,7,PANEL_ACCENT);
    MISSION_goal(goal,missionNode);PANEL_wrap(goal,2,9,36,1,PANEL_BODY);
    rule(11);PANEL_text("AMEAÇA PRINCIPAL",2,12,PANEL_ACCENT);
    enemyCard(MISSION_THREAT[missionNode],14);
    rule(20);PANEL_text("DICA DE COMBATE",2,21,PANEL_ACCENT);
    PANEL_wrap(copy->route ? copy->route : copy->attention,2,22,36,1,PANEL_BODY);
    PANEL_text("B: GUIA",2,26,PANEL_LIGHT);PANEL_right("A: COMEÇAR",26,PANEL_LIGHT);
    PANEL_radioCommit();
}
static void drawGuide(void)
{
    u8 types[ENEMY_TYPES];const u8 count=guideEnemies(types);
    char right[12],goal[48];sprintf(right,"%u/%u",guidePage+1,count+2);
    page("GUIA DA FASE",right);
    const MissionCopy *copy=&MISSION_COPY[missionNode];
    if(guidePage==0)
    {
        PANEL_text("SUA MISSÃO",2,8,PANEL_ACCENT);
        MISSION_goal(goal,missionNode);PANEL_wrap(goal,2,10,36,1,PANEL_BODY);
        rule(12);PANEL_text("COMO AVANÇAR",2,14,PANEL_ACCENT);
        PANEL_wrap(copy->attention,2,16,36,1,PANEL_BODY);
        if(copy->route){PANEL_text("FIQUE ATENTO",2,19,PANEL_ACCENT);PANEL_wrap(copy->route,2,21,36,1,PANEL_BODY);}
    }
    else if(guidePage==1)
    {
        PANEL_text("CONTROLES",2,8,PANEL_ACCENT);
        PANEL_text("DIRECIONAL",2,10,PANEL_ACCENT);PANEL_text("MOVER E MIRAR",15,10,PANEL_BODY);
        PANEL_text("A",2,12,PANEL_ACCENT);PANEL_text("ATIRAR (SEGURE)",15,12,PANEL_BODY);
        PANEL_text("C",2,14,PANEL_ACCENT);PANEL_text("ESCOLHER ITEM",15,14,PANEL_BODY);
        PANEL_text("B",2,16,PANEL_ACCENT);PANEL_text("USAR ITEM",15,16,PANEL_BODY);
        PANEL_text("START",2,18,PANEL_ACCENT);PANEL_text("PAUSAR",15,18,PANEL_BODY);
        PANEL_wrap("AO PARAR, O TIRO MANTÉM A ÚLTIMA DIREÇÃO DA MIRA.",2,21,36,1,PANEL_BODY);
    }
    else
    {
        const u8 type=types[guidePage-2];
        PANEL_text("CONHEÇA O INSETO",2,8,PANEL_ACCENT);enemyCard(type,10);
        rule(17);PANEL_text("COMO RECONHECER",2,19,PANEL_ACCENT);
        const char *profile=type==ENEMY_BOSS ? "CHEFE: INVOCA LACAIOS E INVESTE." :
            ENEMY_DEFS[type]->shape==SHAPE_SQUARE ? "SERRA-PAU: MAIS RESISTENTE." :
            ENEMY_DEFS[type]->shape==SHAPE_TRIANGLE ? "MUTUCA: MENOS VIDA." : "SAÚVA: HABILIDADE ESPECIAL.";
        PANEL_wrap(profile,2,21,36,1,PANEL_BODY);
    }
    PANEL_text("ESQ/DIR: PÁGINA",2,24,PANEL_BODY);
    PANEL_text("B: VOLTAR",2,26,PANEL_LIGHT);PANEL_right("A: PRÓXIMA",26,PANEL_LIGHT);
    PANEL_radioCommit();
}
void MISSION_show(u8 node)
{
    missionNode=node;guidePage=0;guideOpen=FALSE;drawMission();
}
bool MISSION_update(u16 pressed)
{
    if(guideOpen)
    {
        if(pressed&(BUTTON_B|BUTTON_START)){guideOpen=FALSE;drawMission();}
        else
        {
            u8 types[ENEMY_TYPES];const u8 pages=guideEnemies(types)+2;
            if(pressed&(BUTTON_A|BUTTON_RIGHT)){guidePage=(guidePage+1)%pages;drawGuide();}
            else if(pressed&BUTTON_LEFT){guidePage=(guidePage+pages-1)%pages;drawGuide();}
        }
        return FALSE;
    }
    if(pressed&BUTTON_B)
    {
        guidePage=0;guideOpen=TRUE;drawGuide();return FALSE;
    }
    return (pressed&BUTTON_A)!=0;
}
