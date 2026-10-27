// Persistent logical objectives; only visible clutches occupy animation slots.
#include "levels/campaign_factory.h"
#include "levels/arena.h"
#include "levels/phase10_layout.h"
#include "levels/phase11_layout.h"
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
#define eggs PHASE10_EGGS
#define valves PHASE11_VALVES
static u8 activeValve=255;
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
    memset(&campaignFactory,0,sizeof campaignFactory);memset(campaignFactory.slots,255,sizeof campaignFactory.slots);lastHUD=65535;activeValve=255;
    if(!CF_active())return;
    memset(campaignFactory.hp,3,sizeof campaignFactory.hp);MARKERS_load();
    campaignFactory.artReady=OBJECTIVEGFX_startCampaign(1u<<(currentLevel==N_10 ? OART_NEST : OART_VALVE));
    if(currentLevel==N_10)mapEggs();
    else for(u8 i=0;i<PHASE11_VALVE_COUNT;i++)OBJECTIVEGFX_place(i,OART_VALVE,valves[i][0],valves[i][1],TRUE);
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
    else {activeValve=255;for(u8 i=0;i<PHASE11_VALVE_COUNT;i++)if(!(campaignFactory.opened&(1u<<i))){
        const bool nearby=abs(px+8-valves[i][0])<=26 && abs(py+8-valves[i][1])<=26;
        const bool working=nearby && !(JOY_readJoypad(JOY_1)&BUTTON_A);
        if(nearby)activeValve=i;
        OBJECTIVEGFX_prime(i,working);
        // Work survives retreat, but only proximity advances the operation.
        if(working && ++campaignFactory.work[i]>=PHASE11_WORK_FRAMES){
            campaignFactory.opened|=1u<<i;campaignFactory.done++;OBJECTIVEGFX_activate(i);sfxItemPickup();
            activeValve=255;
        }
    }}
    OBJECTIVEGFX_ground(FALSE);
    return campaignFactory.done==(currentLevel==N_10 ? 10 : PHASE11_VALVE_COUNT) ? OBJ_WON : OBJ_ONGOING;
}
void CF_draw(u16 *n)
{
    if(!CF_active())return;
    OBJECTIVEGFX_draw(n);
    if(currentLevel==N_10){for(u8 i=0;i<10;i++)if(campaignFactory.hp[i]){MARKERS_destination(n,eggs[i][0],eggs[i][1]);break;}}
    else {
        for(u8 i=0;i<PHASE11_VALVE_COUNT;i++)if(campaignFactory.opened&(1u<<i))
            SPRITES_emit(n,valves[i][0]+12,valves[i][1]-24,SPRITE_SIZE(1,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_BOLT));
        if(activeValve<PHASE11_VALVE_COUNT && campaignFactory.work[activeValve]) {
            const u16 progress=divu(campaignFactory.work[activeValve]*20,PHASE11_WORK_FRAMES)*5;
            const u16 bar=ARENA_workBar(progress,100);
            if(bar)SPRITES_emit(n,valves[activeValve][0]-16,valves[activeValve][1]-36,SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
        }
        for(u8 i=0;i<PHASE11_VALVE_COUNT;i++)if(!(campaignFactory.opened&(1u<<i))){MARKERS_destination(n,valves[i][0],valves[i][1]);break;}
    }
}
void CF_forceHUD(void){lastHUD=65535;if(CF_active() && campaignFactory.artReady)OBJECTIVEGFX_ground(TRUE);}
bool CF_drawHUD(void)
{
    if(!CF_active())return FALSE;
    if(lastHUD!=campaignFactory.done){char text[12];lastHUD=campaignFactory.done;sprintf(text,"%u/%u",campaignFactory.done,currentLevel==N_10 ? 10 : PHASE11_VALVE_COUNT);
        HUD_drawObjective(currentLevel==N_10 ? "OVOS" : "VÁLVULAS",TILE_SKULL,text,0,"");}
    return TRUE;
}
bool CF_prepText(char *buf,const LevelDef *def)
{
    if(def==&LEVEL10_def){strcpy(buf,"DESTRUA OS 10 NINHOS DE OVOS.");return TRUE;}
    if(def==&LEVEL11_def){strcpy(buf,"LIBERE 6 VÁLVULAS. SOLTE A.");return TRUE;}
    return FALSE;
}
