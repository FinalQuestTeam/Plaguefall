#include "system/video/screens/mission.h"
#include "system/video/screens/panel.h"
#include "levels/graph.h"
#include "core/objective.h"
#include "core/game.h"
#include "mission_copy.h"
#include "enemies/enemies.h"
const char *MISSION_name(u8 node){return node ? MISSION_COPY[node].name : "AREA DE TREINAMENTO";}
void MISSION_goal(char *text,u8 node)
{
    const LevelDef *def=node ? GRAPH[node].def : LEVEL_current();
    if(node && GRAPH_isFinal(node))strcpy(text,"DERROTE O ESCORPIAO.");
    else if(def->objective==OBJ_PROTECT)sprintf(text,"PROTEJA O SINALIZADOR POR %u S.",def->objTarget);
    else if(def->objective==OBJ_KILL)sprintf(text,"ELIMINE %u INIMIGOS.",def->killTarget);
    else OBJECTIVE_prepText(text,def);
}
void MISSION_show(u8 node)
{
    char title[16],right[20],goal[48];
    sprintf(title,"FASE %s",GRAPH[node].name);sprintf(right,"ETAPA %u/16",GRAPH[node].mapCol+1);
    PANEL_page(title,right);PANEL_text(MISSION_name(node),2,5,PANEL_ACCENT);
    PANEL_text("OBJETIVO",2,8,PANEL_ACCENT);MISSION_goal(goal,node);PANEL_wrap(goal,2,10,36,1,PANEL_BODY);
    PANEL_text("ATENCAO",2,13,PANEL_ACCENT);PANEL_wrap(MISSION_COPY[node].attention,2,15,36,1,PANEL_BODY);
    PANEL_wrap(MISSION_COPY[node].route,2,17,36,1,PANEL_BODY);
    PANEL_text("AMEACAS",2,20,PANEL_ACCENT);
    if(GRAPH_isFinal(node))PANEL_text("ESCORPIAO E LACAIOS",2,23,PANEL_BODY);
    else
    {
        const LevelDef *def=GRAPH[node].def;u16 seen=0,slot=0;
        for(u16 i=0;i<def->enemyTypeCount && slot<7;i++)
        {
            const u8 type=def->enemyTypes[i];if(seen&(1<<type))continue;seen|=1<<type;
            const u16 nt=(ENEMY_DEFS[type]->size>32 ? 32 : ENEMY_DEFS[type]->size)/8;
            PANEL_enemy(type,2+slot*5,25-nt,slot);slot++;
        }
    }
    PANEL_right("A: COMECAR",26,PANEL_LIGHT);
}
