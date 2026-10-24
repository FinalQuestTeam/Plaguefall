// Estaleiro: five persistent generators, radio hold, Scorpion launch apron.
#include "levels/campaign_launch.h"
#include "levels/graph.h"
#include "core/game.h"
#include "core/objective.h"
#include "actors/npc.h"
#include "actors/player.h"
#include "system/video/objectivegfx.h"
#include "system/video/markers.h"
#include "system/video/spritelist.h"
#include "system/video/screens/loading.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/sfx.h"
#include "system/video/flash.h"
#include "enemies/enemies.h"
CampaignLaunchState campaignLaunch;
static const s16 machines[5][2]={{64,136},{448,136},{400,208},{416,296},{96,296}};
static u16 lastHUD,lastHP;
static u8 fireRow;
static u16 radioInv;
#define RADIO_SLOT 5
u8 launchPresentation; //1engine focus,2return; gameplay remains inside CL_update.
void CL_camera(s16 *x,s16 *y)
{
    if(currentLevel==N_15 && launchPresentation==1){*x=0;*y=24;}
}
static void presentationFrame(void)
{
    ARENA_camera();OBJECTIVEGFX_update();OBJECTIVEGFX_ground(FALSE);
    SPRITES_draw();SYS_doVBlankProcess();LOADING_poll();
}
void CL_sceneFire(u16 row);
bool CL_sceneReset(void);
static u8 poweredCount(void){u8 n=0;for(u8 i=0;i<5;i++)if(campaignLaunch.powered&(1u<<i))n++;return n;}
bool CL_active(void){return currentLevel==N_14 || currentLevel==N_15 || currentLevel==N_16;}
static void installEquipment(bool powered,u8 radioPose)
{
    // All five physical cabinet bodies persist after the power mission. Both
    // atlases plus the radio are reserved by each full-scene pack (151tiles).
    OBJECTIVEGFX_startCampaign((1u<<OART_GENERATOR)|(radioPose<6 ? (1u<<OART_RADIO) : 0));
    for(u8 i=0;i<5;i++){
        OBJECTIVEGFX_place(i,OART_GENERATOR,machines[i][0],machines[i][1],TRUE);
        if(powered)OBJECTIVEGFX_settle(i,3);
    }
    if(radioPose<6){
        OBJECTIVEGFX_place(RADIO_SLOT,OART_RADIO,256,192,TRUE);
        if(radioPose==4){objectiveVisuals[RADIO_SLOT].mode=4;objectiveVisuals[RADIO_SLOT].frame=4;}
        else OBJECTIVEGFX_prime(RADIO_SLOT,TRUE);
    }
}
static void updateRadioContact(void)
{
    // The raised desk is now a real solid. Contact is measured at its OUTSIDE
    // edge so bugs never need to enter blocked floor to damage the equipment.
    bool contact=FALSE;if(radioInv)radioInv--;
    for(u8 i=0;i<MAX_ENEMIES;i++){
        Enemy *e=&enemies[i];if(!e->active || !ENEMY_DEF(e)->contactDmg)continue;
        const u16 size=ENEMY_SIZE(e);
        if(e->x<313 && e->x+size>199 && e->y<217 && e->y+size>151){
            contact=TRUE;ENEMIES_knockbackFrom(e,256,192);
        }
    }
    if(contact && !radioInv){npcHp-=12;if(npcHp<0)npcHp=0;radioInv=5*fps;FLASH_trigger();}
}
void CL_start(void)
{
    memset(&campaignLaunch,0,sizeof campaignLaunch);CL_forceHUD();fireRow=0;launchPresentation=0;radioInv=0;
    if(!CL_active())return;
    if(CL_sceneReset())ARENA_draw();
    MARKERS_load();
    if(currentLevel==N_14)installEquipment(FALSE,6);
    else if(currentLevel==N_15){
        campaignLaunch.powered=31;installEquipment(TRUE,2);
        ENEMIES_setAggroSplit(3);NPC_spawn(244,180,100);campaignLaunch.left=120*fps;
    }else {
        campaignLaunch.powered=31;campaignLaunch.ignition=3;
        // Same machinery and layout, with an inert damaged radio after ignition.
        installEquipment(TRUE,4);
    }
    OBJECTIVEGFX_ground(TRUE);
}
u8 CL_update(void)
{
    if(!CL_active())return OBJ_ONGOING;
    campaignLaunch.clock++;
    if(currentLevel==N_14){
        for(u8 i=0;i<5;i++)if(!(campaignLaunch.powered&(1u<<i))){
            // Approach the front panel and release fire for0.6seconds.
            const bool close=abs(px+8-machines[i][0])<=28 && py+8>=machines[i][1]+8 && py+8<=machines[i][1]+40;
            OBJECTIVEGFX_prime(i,close);
            if(close && !(JOY_readJoypad(JOY_1)&BUTTON_A)){
                if(++campaignLaunch.work[i]>=fps*3/5){campaignLaunch.powered|=1u<<i;OBJECTIVEGFX_activate(i);sfxItemPickup();}
            }
        }
        if(campaignLaunch.powered==31)return OBJ_WON;
    }else if(currentLevel==N_15){
        updateRadioContact();
        if(!NPC_alive()){objectiveVisuals[RADIO_SLOT].mode=3;objectiveVisuals[RADIO_SLOT].age=0;return OBJ_LOST;}
        if(campaignLaunch.left)campaignLaunch.left--;
        const u8 step=campaignLaunch.left>80*fps ? 0 : campaignLaunch.left>40*fps ? 1 : campaignLaunch.left ? 2 : 3;
        if(step!=campaignLaunch.ignition){campaignLaunch.ignition=step;OBJECTIVEGFX_activate(RADIO_SLOT);if(step==1){arenaDamaged=1;fireRow=8;}}
        if(!campaignLaunch.left)return OBJ_WON;
    }
    if(fireRow==8){
        // Full authored fire state owns its own atlas. Replace atomically with
        // the display off; no frame can expose an old map with new tile pixels.
        const bool enabled=VDP_getEnable();VDP_setEnable(FALSE);DMA_flushQueue();
        LOADING_workBegin();launchPresentation=1;
        CL_sceneFire(8);ARENA_draw();
        installEquipment(TRUE,2);OBJECTIVEGFX_activate(RADIO_SLOT);
        OBJECTIVEGFX_ground(TRUE);CL_forceHUD();CL_drawHUD();
        HUD_drawLife(hp);HUD_drawInventory();HUD_flush();DMA_flushQueue();
        VDP_setEnable(enabled);fireRow=0;
        // This brief shot shows the engine firing. No AI, collision, damage,
        // player movement or defense countdown advances while it is shown.
        for(u16 i=0;i<fps*3/4;i++)presentationFrame();
        launchPresentation=2;
        for(u16 i=0;i<fps*2;i++){
            const s16 oldX=cameraX,oldY=cameraY;presentationFrame();
            if(oldX==cameraX && oldY==cameraY)break;
        }
        launchPresentation=0;LOADING_workEnd();
    }
    OBJECTIVEGFX_update();OBJECTIVEGFX_ground(FALSE);return OBJ_ONGOING;
}
bool CL_target(s16 *x,s16 *y){if(currentLevel!=N_15 || !NPC_alive())return FALSE;*x=npcX+12;*y=npcY+12;return TRUE;}
void CL_draw(u16 *n){if(CL_active())OBJECTIVEGFX_draw(n);}
void CL_forceHUD(void){lastHUD=lastHP=65535;}
bool CL_drawHUD(void)
{
    if(currentLevel!=N_14 && currentLevel!=N_15)return FALSE;
    u16 value=currentLevel==N_14 ? poweredCount() : (campaignLaunch.left+fps-1)/fps;
    if(value!=lastHUD || (currentLevel==N_15 && npcHp!=lastHP)){
        char buf[12],aux[12];lastHUD=value;lastHP=npcHp;
        sprintf(buf,currentLevel==N_14 ? "%u/5" : "%us",value);
        if(currentLevel==N_15)sprintf(aux,"%03d",npcHp);else aux[0]=0;
        HUD_drawObjective(currentLevel==N_14 ? "ENERGIA" : "RÁDIO",currentLevel==N_14 ? TILE_BOLT : TILE_CLOCK,buf,currentLevel==N_15 ? TILE_ICON_HEART : 0,aux);
    }
    return TRUE;
}
bool CL_prepText(char *buf,const LevelDef *def)
{
    if(def==&LEVEL14_def){strcpy(buf,"LIGUE AS 5 MÁQUINAS DE ENERGIA.");return TRUE;}
    if(def==&LEVEL15_def){strcpy(buf,"PROTEJA O RÁDIO POR 120 SEGUNDOS.");return TRUE;}
    return FALSE;
}
