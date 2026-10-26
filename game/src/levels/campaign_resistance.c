// Campaign versions of the transport / priority missions. Five durable source
// states, exactly one carried load, one depot. Targets own the first3slots;
// reinforcement cannot reuse a dead target slot before its death is observed.
#include "levels/campaign_resistance.h"
#include "levels/phase07_layout.h"
#include "levels/phase08_layout.h"
#include "levels/graph.h"
#include "core/game.h"
#include "core/objective.h"
#include "actors/player.h"
#include "enemies/enemies.h"
#include "system/video/objectivegfx.h"
#include "system/video/markers.h"
#include "system/video/projection.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/sfx.h"
CampaignResistanceState campaignResistance;
#define sources PHASE07_SOURCES
#define targets PHASE08_TARGETS
static u16 lastHUD;
static bool near(s16 x,s16 y){return abs(px+8-x)<=22 && abs(py+8-y)<=22;}
static u8 doneCount(void){return (campaignResistance.priorityDone&1)+((campaignResistance.priorityDone>>1)&1)+((campaignResistance.priorityDone>>2)&1);}
bool CAMPAIGN_RESISTANCE_active(void){return currentLevel==N_7 || currentLevel==N_8;}
bool CAMPAIGN_RESISTANCE_blocked(s16 x,s16 y,u16 w,u16 h)
{
    if(currentLevel!=N_7)return FALSE;
    for(u8 i=0;i<5;i++)if(!(campaignResistance.taken&(1u<<i))){
        // Thin contact base under the complete case. Empty collected cases
        // release their floor immediately, including during the delivery trip.
        const s16 left=sources[i][0]-16,top=sources[i][1];
        if(x<left+32 && x+(s16)w>left && y<top+8 && y+(s16)h>top)return TRUE;
    }
    return FALSE;
}
bool CAMPAIGN_RESISTANCE_managesSpawn(void){return CAMPAIGN_RESISTANCE_active();}
bool CAMPAIGN_RESISTANCE_hideEnemy(u16 i){return currentLevel==N_8 && i<3 && !(campaignResistance.priorityDone&(1u<<i));}
void CAMPAIGN_RESISTANCE_start(void)
{
    memset(&campaignResistance,0,sizeof campaignResistance);campaignResistance.cargo=255;
    campaignResistance.spawnTimer=fps*3;lastHUD=65535;playerSlowPct=0;
    if(!CAMPAIGN_RESISTANCE_active())return;
    MARKERS_load();
    if(currentLevel==N_7){
        OBJECTIVEGFX_startCampaign(1u<<OART_CARGO);
        for(u8 i=0;i<5;i++)OBJECTIVEGFX_place(i,OART_CARGO,sources[i][0],sources[i][1],TRUE);
        OBJECTIVEGFX_place(5,OART_CARGO,PHASE07_DEPOT_X,PHASE07_DEPOT_Y,TRUE);OBJECTIVEGFX_settle(5,5);
    }else{
        OBJECTIVEGFX_startCampaign(1u<<OART_TRANSMITTER);
        for(u8 i=0;i<3;i++){
            ENEMIES_spawnAt(ENEMY_SQ_RED,targets[i][0],targets[i][1]);
            // Fixed transmitter posts. Normal red attacks and real HP/deaths.
            enemies[i].hp=4;campaignResistance.prioritySlots[i]=i;
            OBJECTIVEGFX_place(i,OART_TRANSMITTER,enemies[i].x+8,VIDEO_PROJECT_Y(enemies[i].y)+8,FALSE);
        }
    }
    OBJECTIVEGFX_ground(TRUE);
}
void CAMPAIGN_RESISTANCE_beforeUpdate(void)
{if(CAMPAIGN_RESISTANCE_active())playerSlowPct=currentLevel==N_7 && campaignResistance.cargo!=255 ? 20 : 0;}
static void spawn(void)
{
    if(campaignResistance.spawnTimer){campaignResistance.spawnTimer--;return;}
    campaignResistance.spawnTimer=fps*(currentLevel==N_8 ? 2+doneCount()*2 : 3);
    const LevelDef *def=LEVEL_current();ENEMIES_trySpawn(def->enemyTypes,def->enemyTypeCount);
}
u8 CAMPAIGN_RESISTANCE_update(void)
{
    if(!CAMPAIGN_RESISTANCE_active())return OBJ_ONGOING;
    campaignResistance.clock++;
    if(currentLevel==N_7){
        if(campaignResistance.cargo==255){
            for(u8 i=0;i<5;i++)if(!(campaignResistance.taken&(1u<<i))){
                if(!(campaignResistance.opened&(1u<<i))){
                    // Explicit half-second interaction at the chest's front.
                    // Release fire to operate; a hit/retreat preserves progress.
                    const s16 dx=px+8-sources[i][0],dy=py+8-sources[i][1];
                    if(abs(dx)<=24 && dy>=8 && dy<=32 && !(JOY_readJoypad(JOY_1)&BUTTON_A)){
                        OBJECTIVEGFX_prime(i,TRUE);
                        if(++campaignResistance.work[i]>=(fps+1)/2){campaignResistance.opened|=1u<<i;OBJECTIVEGFX_activate(i);sfxItemPickup();}
                    }else OBJECTIVEGFX_prime(i,FALSE);
                }else if(objectiveVisuals[i].mode==2 && near(sources[i][0]+24,sources[i][1]+16)){
                    campaignResistance.taken|=1u<<i;campaignResistance.cargo=i;OBJECTIVEGFX_settle(i,5);sfxItemPickup();break;
                }
            }
        }else if(near(PHASE07_DEPOT_X,PHASE07_DEPOT_Y)){
            campaignResistance.cargo=255;campaignResistance.delivered++;OBJECTIVEGFX_activate(5);sfxItemPickup();
            playerSlowPct=0;
        }
        for(u8 i=0;i<5;i++)if((campaignResistance.opened&(1u<<i)) && !(campaignResistance.taken&(1u<<i)) && objectiveVisuals[i].mode==2)OBJECTIVEGFX_settle(i,3);
        if(campaignResistance.delivered==5)return OBJ_WON;
    }else{
        for(u8 i=0;i<3;i++)if(!(campaignResistance.priorityDone&(1u<<i))){
            Enemy *e=&enemies[i];
            if(!e->active){campaignResistance.priorityDone|=1u<<i;OBJECTIVEGFX_activate(i);sfxItemPickup();
                // Death instantly postpones the next wave as well as reducing
                // subsequent pressure; no immediate leftover fast timer.
                campaignResistance.spawnTimer=fps*(2+doneCount()*2);
            }else{
                objectiveVisuals[i].x=e->x+8;objectiveVisuals[i].y=VIDEO_PROJECT_Y(e->y)+8;
            }
        }
        if(campaignResistance.priorityDone==7)return OBJ_WON;
    }
    spawn();const u16 count=ENEMIES_activeCount();if(count>campaignResistance.peakEnemies)campaignResistance.peakEnemies=count;
    OBJECTIVEGFX_update();OBJECTIVEGFX_ground(FALSE);return OBJ_ONGOING;
}
void CAMPAIGN_RESISTANCE_draw(u16 *n)
{
    if(!CAMPAIGN_RESISTANCE_active())return;
    if(currentLevel==N_7){
        for(u8 i=0;i<5;i++)if((campaignResistance.opened&(1u<<i)) && !(campaignResistance.taken&(1u<<i)) && objectiveVisuals[i].mode==2)
            OBJECTIVEGFX_cargo(n,sources[i][0]+24,sources[i][1]+16);
        if(campaignResistance.cargo!=255){OBJECTIVEGFX_cargo(n,px+20,py-4);MARKERS_destination(n,PHASE07_DEPOT_X,PHASE07_DEPOT_Y);}
    }
    OBJECTIVEGFX_draw(n);
}
void CAMPAIGN_RESISTANCE_forceHUD(void){lastHUD=65535;}
bool CAMPAIGN_RESISTANCE_drawHUD(void)
{
    if(!CAMPAIGN_RESISTANCE_active())return FALSE;
    const u16 value=currentLevel==N_7 ? campaignResistance.delivered : doneCount();
    const u16 sig=value+(campaignResistance.cargo!=255 ? 16 : 0);
    // HUD is only one tiny update per logical change; no diagnostic extra rows.
    if(lastHUD!=sig){char buf[12];lastHUD=sig;sprintf(buf,"%u/%u",value,currentLevel==N_7 ? 5 : 3);
        HUD_drawObjective(currentLevel==N_7 ? (campaignResistance.cargo!=255 ? "ENTREGUE" : "CARGAS") : "EMISSORES",currentLevel==N_7 ? TILE_BOMB_ICON : TILE_SKULL,buf,0,"");}
    return TRUE;
}
bool CAMPAIGN_RESISTANCE_prepText(char *buf,const LevelDef *def)
{
    if(def==&LEVEL07_def){strcpy(buf,"ABRA E ENTREGUE 5 CARGAS AO DEPÓSITO.");return TRUE;}
    if(def==&LEVEL08_def){strcpy(buf,"DESTRUA OS 3 INSETOS TRANSMISSORES.");return TRUE;}
    return FALSE;
}
