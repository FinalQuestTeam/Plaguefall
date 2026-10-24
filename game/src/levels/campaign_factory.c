// Persistent logical objectives; only visible clutches occupy animation slots.
#include "levels/campaign_factory.h"
#include "levels/graph.h"
#include "core/game.h"
#include "core/objective.h"
#include "actors/player.h"
#include "system/video/objectivegfx.h"
#include "system/video/markers.h"
#include "system/video/spritelist.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/sfx.h"
CampaignFactoryState campaignFactory;
static const s16 eggs[10][2]={{96,168},{96,248},{240,168},{240,248},{384,168},{384,248},{528,168},{528,248},{672,168},{672,248}};
// Controls are mounted in the northern service recess. Actors approach from y112.
static const s16 valves[3][2]={{144,104},{432,104},{576,104}};
static const s16 stationMonitors[3][2]={{180,88},{468,88},{612,88}};
static u16 lastHUD;
bool CF_active(void){return currentLevel==N_10 || currentLevel==N_11;}
static bool visible(u8 i){return eggs[i][0]>=cameraX-24 && eggs[i][0]<cameraX+344 && eggs[i][1]>=cameraY+8 && eggs[i][1]<cameraY+272;}
static void mapEggs(void)
{
    bool removed=FALSE;
    for(u8 s=0;s<7;s++){
        u8 i=campaignFactory.slots[s];
        if(i!=255 && (!visible(i) || ((campaignFactory.destroyed&(1u<<i)) && objectiveVisuals[s].mode==2))){
            OBJECTIVEGFX_hide(s);campaignFactory.slots[s]=255;removed=TRUE;
        }
    }
    // Restore old footprints before reusing their slot at a new world position.
    if(removed)OBJECTIVEGFX_ground(FALSE);
    for(u8 i=0;i<10;i++)if(!(campaignFactory.destroyed&(1u<<i)) && visible(i)){
        bool found=FALSE;for(u8 s=0;s<7;s++)if(campaignFactory.slots[s]==i)found=TRUE;
        if(!found)for(u8 s=0;s<7;s++)if(campaignFactory.slots[s]==255){
            campaignFactory.slots[s]=i;OBJECTIVEGFX_place(s,OART_NEST,eggs[i][0],eggs[i][1],TRUE);break;
        }
    }
}
void CF_start(void)
{
    memset(&campaignFactory,0,sizeof campaignFactory);memset(campaignFactory.slots,255,sizeof campaignFactory.slots);lastHUD=65535;
    if(!CF_active())return;
    memset(campaignFactory.hp,3,sizeof campaignFactory.hp);MARKERS_load();
    campaignFactory.artReady=OBJECTIVEGFX_startCampaign(1u<<(currentLevel==N_10 ? OART_NEST : OART_VALVE));
    if(currentLevel==N_10)mapEggs();
    else for(u8 i=0;i<3;i++)OBJECTIVEGFX_place(i,OART_VALVE,valves[i][0],valves[i][1],TRUE);
    OBJECTIVEGFX_ground(TRUE);
}
static void destroy(u8 i)
{
    if(campaignFactory.destroyed&(1u<<i))return;
    campaignFactory.hp[i]=0;campaignFactory.destroyed|=1u<<i;campaignFactory.done++;sfxItemPickup();
    for(u8 s=0;s<7;s++)if(campaignFactory.slots[s]==i)OBJECTIVEGFX_activate(s);
}
bool CF_shotHit(s16 x,s16 y)
{
    if(currentLevel!=N_10 || !campaignFactory.artReady)return FALSE;
    for(u8 i=0;i<10;i++)if(campaignFactory.hp[i] && abs(x-eggs[i][0])<=22 && y>=eggs[i][1]-40 && y<=eggs[i][1]+8){
        if(!--campaignFactory.hp[i])destroy(i);
        else for(u8 s=0;s<7;s++)if(campaignFactory.slots[s]==i)OBJECTIVEGFX_prime(s,TRUE);
        return TRUE;
    }
    return FALSE;
}
void CF_bomb(void)
{
    if(currentLevel!=N_10)return;
    for(u8 i=0;i<10;i++)if(eggs[i][0]>=cameraX && eggs[i][0]<cameraX+320 && eggs[i][1]>=cameraY+24 && eggs[i][1]<cameraY+224)destroy(i);
}
u8 CF_update(void)
{
    if(!CF_active())return OBJ_ONGOING;
    campaignFactory.clock++;OBJECTIVEGFX_update();
    if(currentLevel==N_10)mapEggs();
    else for(u8 i=0;i<3;i++)if(!(campaignFactory.opened&(1u<<i))){
        const bool working=abs(px+8-valves[i][0])<=26 && abs(py+8-valves[i][1])<=26 && !(JOY_readJoypad(JOY_1)&BUTTON_A);
        OBJECTIVEGFX_prime(i,working);
        // Work survives retreat, but only proximity advances the operation.
        if(working && ++campaignFactory.work[i]>=fps*3/2){
            campaignFactory.opened|=1u<<i;campaignFactory.done++;OBJECTIVEGFX_activate(i);sfxItemPickup();
        }
    }
    OBJECTIVEGFX_ground(FALSE);
    return campaignFactory.done==(currentLevel==N_10 ? 10 : 3) ? OBJ_WON : OBJ_ONGOING;
}
void CF_draw(u16 *n)
{
    if(!CF_active())return;
    OBJECTIVEGFX_draw(n);
    if(currentLevel==N_10){for(u8 i=0;i<10;i++)if(campaignFactory.hp[i]){MARKERS_destination(n,eggs[i][0],eggs[i][1]);break;}}
    else {
        // Each completed pressure station powers its attached control screen.
        for(u8 i=0;i<3;i++)if(campaignFactory.opened&(1u<<i))
            SPRITES_emit(n,stationMonitors[i][0]-4,stationMonitors[i][1]-4,SPRITE_SIZE(1,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_BOLT));
        for(u8 i=0;i<3;i++)if(!(campaignFactory.opened&(1u<<i))){MARKERS_destination(n,valves[i][0],valves[i][1]);break;}
    }
}
void CF_forceHUD(void){lastHUD=65535;if(CF_active() && campaignFactory.artReady)OBJECTIVEGFX_ground(TRUE);}
bool CF_drawHUD(void)
{
    if(!CF_active())return FALSE;
    if(lastHUD!=campaignFactory.done){char text[12];lastHUD=campaignFactory.done;sprintf(text,"%u/%u",campaignFactory.done,currentLevel==N_10 ? 10 : 3);
        HUD_drawObjective(currentLevel==N_10 ? "OVOS" : "VÁLVULAS",TILE_SKULL,text,0,"");}
    return TRUE;
}
bool CF_prepText(char *buf,const LevelDef *def)
{
    if(def==&LEVEL10_def){strcpy(buf,"DESTRUA OS 10 NINHOS DE OVOS.");return TRUE;}
    if(def==&LEVEL11_def){strcpy(buf,"LIBERE 3 VÁLVULAS. SOLTE A.");return TRUE;}
    return FALSE;
}
