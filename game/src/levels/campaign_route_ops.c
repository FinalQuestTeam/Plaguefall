// Both sewer escorts have shootable gates. Only6B requires bleeding pressure.
#include "levels/campaign_route_ops.h"
#include "levels/campaign_routes.h"
#include "levels/levels.h"
#include "levels/graph.h"
#include "core/objective.h"
#include "core/game.h"
#include "actors/player.h"
#include "actors/dinorah.h"
#include "system/video/objectivegfx.h"
#include "system/video/markers.h"
#include "system/video/spritelist.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "system/audio/sfx.h"

CampaignRouteOperations campaignRouteOps;
static u16 hudSignature;
static bool localHud,gateBoundsValid;
static s16 gateLeft,gateTop,gateRight,gateBottom;
static bool overlap(const ArenaRect *r,s16 x,s16 y,u16 w,u16 h)
{
    // Authored coordinates/sizes fit signed16; relative intervals avoid
    // repeated long arithmetic on every projectile/contact probe.
    return (u16)(x-r->x+(s16)w-1)<(u16)(r->w+w-1) &&
           (u16)(y-r->y+(s16)h-1)<(u16)(r->h+h-1);
}
bool CR_OPS_active(void)
{return currentLevel==N_6A || currentLevel==N_6B;}
u8 CR_OPS_gateBlockMask(void)
{
    if(!CR_OPS_active())return 0;
    return ((campaignRouteOps.gateHp[0] || campaignRouteOps.gateClearTicks[0]) ? 1 : 0) |
           ((campaignRouteOps.gateHp[1] || campaignRouteOps.gateClearTicks[1]) ? 2 : 0);
}
bool CR_OPS_prepText(char *buf,const LevelDef *def)
{
    if(def->route==&CAMPAIGN_ROUTE06A){strcpy(buf,"ESCOLTE. DESTRUA OS PORTÕES.");return TRUE;}
    if(def->route!=&CAMPAIGN_ROUTE06B)return FALSE;
    strcpy(buf,"ESCOLTE. ABRA VÁLVULAS E PORTÕES.");return TRUE;
}
void CR_OPS_start(void)
{
    memset(&campaignRouteOps,0,sizeof campaignRouteOps);
    localHud=FALSE;hudSignature=0xFFFF;gateBoundsValid=FALSE;
    if(!CR_OPS_active())return;
    gateLeft=gateTop=32767;gateRight=gateBottom=-32768;
    for(u8 i=0;i<2;i++) {
        const ArenaRect *g=&CAMPAIGN_ROUTE06_gates[i];
        if(g->x<gateLeft)gateLeft=g->x;if(g->y<gateTop)gateTop=g->y;
        if(g->x+g->w>gateRight)gateRight=g->x+g->w;
        if(g->y+g->h>gateBottom)gateBottom=g->y+g->h;
    }
    gateBoundsValid=TRUE;
    campaignRouteOps.gateHp[0]=campaignRouteOps.gateHp[1]=4;
    const bool pressure=currentLevel==N_6B;
    //6A gates can be shot immediately: no valve art, work or steam.
    if(!pressure)campaignRouteOps.pressureMask=3;
    if(!OBJECTIVEGFX_startCampaign((1u<<OART_GATE)|(pressure ? (1u<<OART_VALVE) : 0)))return;
    for(u8 i=0;i<2;i++) {
        const ArenaRect *g=&CAMPAIGN_ROUTE06_gates[i];
        const RoutePoint *v=&CAMPAIGN_ROUTE06B_valves[i];
        OBJECTIVEGFX_place(i,OART_GATE,g->x+g->w/2,g->y+g->h-8,TRUE);
        if(pressure)OBJECTIVEGFX_place(i+2,OART_VALVE,v->x,v->y+8,TRUE);
    }
    OBJECTIVEGFX_ground(TRUE);
}
bool CR_OPS_blocked(s16 x,s16 y,u16 w,u16 h)
{
    if(!CR_OPS_active())return FALSE;
    if(gateBoundsValid && (x+(s16)w<=gateLeft || x>=gateRight || y+(s16)h<=gateTop || y>=gateBottom))return FALSE;
    for(u8 i=0;i<2;i++)if((campaignRouteOps.gateHp[i] || campaignRouteOps.gateClearTicks[i]) && overlap(&CAMPAIGN_ROUTE06_gates[i],x,y,w,h))return TRUE;
    return FALSE;
}
bool CR_OPS_shotBlocked(s16 x,s16 y,bool player)
{
    if(!CR_OPS_active())return FALSE;
    if(gateBoundsValid && (x+8<=gateLeft || x>=gateRight || y+8<=gateTop || y>=gateBottom))return FALSE;
    for(u8 i=0;i<2;i++)if((campaignRouteOps.gateHp[i] || campaignRouteOps.gateClearTicks[i]) && overlap(&CAMPAIGN_ROUTE06_gates[i],x,y,8,8)) {
        // Closed pressure systems absorb the shot. An ally sightline probe
        // uses player=FALSE, so visibility checks cannot damage a door.
        if(player && campaignRouteOps.gateHp[i] && (campaignRouteOps.pressureMask&(1u<<i))) {
            campaignRouteOps.gateHp[i]--;SFX_playerHit();
            if(!campaignRouteOps.gateHp[i]) {
                // The native frame supplies the permanent supports. Keep the
                // passage closed during the authored collapse, including its
                // final pose, then clear the temporary sprite's own pillars.
                campaignRouteOps.gateClearTicks[i]=fps*4/5;
                OBJECTIVEGFX_activate(i);sfxItemPickup();
            }
            else OBJECTIVEGFX_prime(i,TRUE);
        }
        return TRUE;
    }
    return FALSE;
}
static bool working(u8 i)
{
    const RoutePoint *v=&CAMPAIGN_ROUTE06B_valves[i];
    const s16 dy=py+8-v->y;
    return abs(px+8-v->x)<=22 && dy>=16 && dy<=40;
}
void CR_OPS_update(void)
{
    if(!CR_OPS_active())return;
    if(campaignRouteOps.damageTimer)campaignRouteOps.damageTimer--;
    for(u8 i=0;i<2;i++)if(campaignRouteOps.gateClearTicks[i] && !--campaignRouteOps.gateClearTicks[i])OBJECTIVEGFX_hide(i);
    if(currentLevel==N_6B && ++campaignRouteOps.steamClock>=fps*3)campaignRouteOps.steamClock=0;
    for(u8 i=0;i<2;i++)if(!(campaignRouteOps.pressureMask&(1u<<i))) {
        if(working(i) && !(JOY_readJoypad(JOY_1)&BUTTON_A)) {
            if(campaignRouteOps.work[i]<(fps*3+1)/2)campaignRouteOps.work[i]++;
            OBJECTIVEGFX_prime(i+2,TRUE);
            if(campaignRouteOps.work[i]>=(fps*3+1)/2) {
                campaignRouteOps.pressureMask|=1u<<i;
                OBJECTIVEGFX_activate(i+2);sfxItemPickup();
            }
        }
        const ArenaRect *g=&CAMPAIGN_ROUTE06_gates[i];
        const ArenaRect steam={g->x-16,g->y,32,g->h,FALSE};
        // The same visible mouth is warned for1s before the2s hot phase.
        // The work position stays west of this zone, preserving a safe pocket.
        if(campaignRouteOps.steamClock>=fps && !campaignRouteOps.damageTimer && overlap(&steam,px,py,16,16)) {
            damagePlayer(5);campaignRouteOps.damageTimer=fps/2;SFX_ambient(SFX_AMB_LAVA);
        }
    }
    OBJECTIVEGFX_update();OBJECTIVEGFX_ground(FALSE);
}
void CR_OPS_draw(u16 *sprites)
{
    if(!CR_OPS_active())return;
    for(u8 i=0;i<2;i++)if(campaignRouteOps.gateHp[i] || campaignRouteOps.gateClearTicks[i]) {
        const ArenaRect *g=&CAMPAIGN_ROUTE06_gates[i];
        const RoutePoint *v=&CAMPAIGN_ROUTE06B_valves[i];
        if(!(campaignRouteOps.pressureMask&(1u<<i))) {
            // Existing alert art marks the real steam mouth; no invisible
            // hazard extends into the safe south face of the valve.
            if(g->x>=cameraX && g->x<cameraX+320 && (campaignRouteOps.steamClock<fps || (campaignRouteOps.steamClock&8)))MARKERS_alert(sprites,g->x,g->y+g->h/2);
            const s16 barY=v->y-28;
            if(v->x+16>cameraX && v->x-16<cameraX+320 && barY+8>cameraY+HUD_HEIGHT && barY<cameraY+224) {
                // Separate work/ally patterns prevent Dinorah's health from
                // overwriting this fill. Quantizing to5%
                // updates only its fill while retaining the exact work timer.
                const u16 value=divu(campaignRouteOps.work[i]*20,(fps*3+1)/2)*5;
                const u16 bar=ARENA_workBar(value,100);
                if(bar)SPRITES_emit(sprites,v->x-16,barY,SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
            }
            if(!working(i))MARKERS_destination(sprites,v->x,v->y+32);
        } else if(g->x+g->w>cameraX && g->x<cameraX+320) {
            MARKERS_shoot(sprites,g->x+g->w/2,g->y,4-campaignRouteOps.gateHp[i]);
        } else if(campaignRouteOps.gateHp[i])MARKERS_destination(sprites,g->x+g->w/2,g->y+g->h);
        // Guide the next unfinished compound. Future/offscreen warning
        // badges obscured the route and consumed the sprite admission budget.
        break;
    }
    OBJECTIVEGFX_draw(sprites);
}
bool CR_OPS_drawHUD(void)
{
    if(!CR_OPS_active())return FALSE;
    s16 selected=-1;
    for(u8 i=0;i<2;i++)if(campaignRouteOps.gateHp[i] && abs(px-CAMPAIGN_ROUTE06_gates[i].x)<128){selected=i;break;}
    if(selected<0) {
        if(localHud){localHud=FALSE;hudSignature=0xFFFF;OBJECTIVE_forceHUD(0);}
        return FALSE;
    }
    const u8 i=selected;const bool open=campaignRouteOps.pressureMask&(1u<<i);
    const u16 progress=open ? campaignRouteOps.gateHp[i] : (u32)campaignRouteOps.work[i]*100/((fps*3+1)/2);
    const bool operating=!open && working(i) && !(JOY_readJoypad(JOY_1)&BUTTON_A);
    const u16 sig=progress+(i<<8)+(open ? 1024 : 0)+(operating ? 2048 : 0);
    if(localHud && sig==hudSignature)return TRUE;
    localHud=TRUE;hudSignature=sig;
    char value[20],aux[12];
    if(open){sprintf(value,"%u/4",4-campaignRouteOps.gateHp[i]);strcpy(aux,"TIRO A");}
    else {sprintf(value,"%03u%%",progress);strcpy(aux,"SEM A");}
    HUD_drawObjective(open ? "PORTÃO" : operating ? "ABRINDO" : "VÁLVULA",open ? TILE_ICON_SHOTS : TILE_CLOCK,value,0,aux);
    return TRUE;
}
