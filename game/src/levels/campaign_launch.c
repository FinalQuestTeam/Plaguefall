// Estaleiro: five persistent generators, radio hold, Scorpion launch apron.
#include "levels/campaign_launch.h"
#include "levels/graph.h"
#include "levels/phase14_layout.h"
#include "levels/phase15_layout.h"
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
static const s16 (*machinePositions(void))[2]
{
    return PHASE14_MACHINES;
}
static bool stationNearby(u8 i)
{
    const s16 (*positions)[2]=machinePositions();
    return abs(px+8-positions[i][0])<=28 && py+8>=positions[i][1]+8 && py+8<=positions[i][1]+40;
}
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
    const s16 (*positions)[2]=machinePositions();
    // All three shipyard stages share native equipment and world anchors.
    OBJECTIVEGFX_startCampaign((1u<<OART_GENERATOR)|(radioPose<6 ? (1u<<OART_RADIO) : 0));
    for(u8 i=0;i<5;i++){
        OBJECTIVEGFX_place(i,OART_GENERATOR,positions[i][0],positions[i][1],TRUE);
        if(powered)OBJECTIVEGFX_settle(i,3);
    }
    if(radioPose<6){
        OBJECTIVEGFX_place(RADIO_SLOT,OART_RADIO,PHASE15_RADIO_X,PHASE15_RADIO_Y,TRUE);
        if(radioPose==4){objectiveVisuals[RADIO_SLOT].mode=4;objectiveVisuals[RADIO_SLOT].frame=4;}
        else OBJECTIVEGFX_prime(RADIO_SLOT,TRUE);
    }
}
static void updateRadioContact(void)
{
    // Only the compact core's ground base is solid/vulnerable. The antenna
    // above it never blocks movement or damages the objective on contact.
    bool contact=FALSE;if(radioInv)radioInv--;
    for(u8 i=0;i<MAX_ENEMIES;i++){
        Enemy *e=&enemies[i];if(!e->active || !ENEMY_DEF(e)->contactDmg)continue;
        const u16 size=ENEMY_SIZE(e);
        if(e->x<PHASE15_BASE_X+PHASE15_BASE_W+1 && e->x+size>PHASE15_BASE_X-1 &&
           e->y<PHASE15_BASE_Y+PHASE15_BASE_H+1 && e->y+size>PHASE15_BASE_Y-1){
            contact=TRUE;ENEMIES_knockbackFrom(e,PHASE15_TARGET_X,PHASE15_TARGET_Y);
        }
    }
    if(contact && !radioInv){npcHp-=12;if(npcHp<0)npcHp=0;radioInv=5*fps;OBJECTIVEGFX_radioHit();FLASH_trigger();}
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
        ENEMIES_setAggroSplit(3);NPC_spawn(PHASE15_NPC_X,PHASE15_NPC_Y,100);campaignLaunch.left=120*fps;
    }else {
        campaignLaunch.powered=31;campaignLaunch.ignition=3;
        // Only the engine windows change; retain the powered stage15 equipment.
        installEquipment(TRUE,2);
    }
    OBJECTIVEGFX_ground(TRUE);
}
u8 CL_update(void)
{
    if(!CL_active())return OBJ_ONGOING;
    campaignLaunch.clock++;
    if(currentLevel==N_14){
        const bool firing=JOY_readJoypad(JOY_1)&BUTTON_A;
        for(u8 i=0;i<5;i++)if(!(campaignLaunch.powered&(1u<<i))){
            const bool close=stationNearby(i);
            OBJECTIVEGFX_prime(i,close && !firing);
            if(close){
                campaignLaunch.decay[i]=0;
                if(!firing && ++campaignLaunch.work[i]>=fps*CL_POWER_SECONDS){
                    campaignLaunch.powered|=1u<<i;OBJECTIVEGFX_activate(i);sfxItemPickup();
                }
            }else if(campaignLaunch.work[i]){
                // Each full second away removes one second of unfinished work.
                if(++campaignLaunch.decay[i]>=fps){
                    campaignLaunch.decay[i]=0;
                    campaignLaunch.work[i]=campaignLaunch.work[i]>fps ? campaignLaunch.work[i]-fps : 0;
                }
            }else{
                campaignLaunch.decay[i]=0;
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
void CL_draw(u16 *n)
{
    if(!CL_active())return;
    OBJECTIVEGFX_draw(n);
    if(currentLevel==N_15){
        const u16 bar=ARENA_npcBar(npcHp,npcHpMax);
        if(bar)SPRITES_emit(n,PHASE15_BASE_X,PHASE15_BASE_Y+PHASE15_BASE_H+8,
                           SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
        return;
    }
    if(currentLevel!=N_14)return;
    for(u8 i=0;i<5;i++)if(!(campaignLaunch.powered&(1u<<i)) &&
                          (campaignLaunch.work[i] || stationNearby(i))){
        const s16 x=PHASE14_MACHINES[i][0]-16,y=PHASE14_MACHINES[i][1]-48;
        if(x+32<=cameraX || x>=cameraX+320 || y<cameraY+HUD_HEIGHT || y+8>cameraY+224)continue;
        const u16 value=divu(campaignLaunch.work[i]*20,fps*CL_POWER_SECONDS)*5;
        const u16 bar=ARENA_workBarAt(i,value,100);
        if(bar)SPRITES_emit(n,x,y,SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
    }
}
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
    if(def==&LEVEL14_def){strcpy(buf,"FIQUE 10s SEM ATIRAR EM CADA ESTAÇÃO.");return TRUE;}
    if(def==&LEVEL15_def){strcpy(buf,"PROTEJA O NÚCLEO DO RÁDIO POR 120s.");return TRUE;}
    return FALSE;
}
