// Sistema de objetivos de fase — ver objective.h.

#include "core/objective.h"
#include "levels/campaign_route_ops.h"
#include "levels/campaign_resistance.h"
#include "levels/campaign_factory.h"
#include "levels/campaign_launch.h"
#include "core/game.h"
#include "levels/graph.h"
#include "actors/npc.h"
#include "actors/dinorah.h"
#include "actors/player.h"
#include "system/video/spritelist.h"
#include "system/video/markers.h"
#include "enemies/enemies.h"                     // ENEMIES_setAggroSplit (PROTEGER)
#include "items/items.h"                        // ITEM_* (item alvo do COLETAR)
#include "system/video/screens/hud.h"
#include "system/video/scene_stream.h"
#include "system/video/screens/hud_label_data.h"
#include "system/video/sprites/tiles.h"

static const LevelDef *cur;
static u16 surviveLeft;      // frames restantes (SURVIVE / PROTECT)
static u16 collected;        // itens do tipo-alvo coletados (COLLECT)
static u16 arrivalTimer;
static u16 hudLast;          // assinatura do último HUD desenhado (gate de redesenho)

// nome (PT) do item para o texto da preparação do COLETAR
static const char *itemName(u8 type)
{
    switch (type)
    {
        case ITEM_HEART:  return "MARMITAS";
        case ITEM_BOMB:   return "CARGAS";
        case ITEM_SHOTS:  return "DIVISORES";
        case ITEM_SPEED:  return "SERVOS";
        case ITEM_SHIELD: return "CAPACITORES";
        case ITEM_CHAIN:  return "BOBINAS";
        case ITEM_ICE:    return "REFIS FRIOS";
        case ITEM_FIRE:   return "REFIS QUENTES";
    }
    return "ITENS";
}

// tile 8x8 do símbolo do item (para o HUD do COLETAR)
static u16 itemIcon(u8 type)
{
    switch (type)
    {
        case ITEM_HEART:  return TILE_ICON_HEART;
        case ITEM_BOMB:   return TILE_BOMB_ICON;
        case ITEM_SHOTS:  return TILE_ICON_SHOTS;
        case ITEM_SPEED:  return TILE_ICON_SPEED;
        case ITEM_SHIELD: return TILE_ICON_SHIELD;
        case ITEM_CHAIN:  return TILE_BOLT;
        case ITEM_ICE:    return TILE_ICON_ICE;
        case ITEM_FIRE:   return TILE_ICON_FIRE;
    }
    return TILE_SKULL;                           // fallback para tipo inválido
}

void OBJECTIVE_start(const LevelDef *def)
{
    cur = def;
    arrivalTimer=0;DINORAH_clear();
    if(def->objective==OBJ_ESCORT)DINORAH_start(def->route);
    if(def->route)MARKERS_load();
    collected = 0;
    surviveLeft = (u16) (def->objTarget * fps);
    hudLast = 0xFFFF;                            // força o 1º desenho do HUD

    if (def->objective == OBJ_PROTECT)
    {
        NPC_spawn(def->npcX, def->npcY, def->npcHp);
        ENEMIES_setAggroSplit(3);       // 1 a cada 3 inimigos persegue o jogador
    }
    else
    {
        NPC_clear();
        ENEMIES_setAggroSplit(def->objective==OBJ_ESCORT ? 2 : 0);       // demais objetivos: todos no alvo padrão
    }
    CR_OPS_start();CAMPAIGN_RESISTANCE_start();CF_start();CL_start();
}

void OBJECTIVE_addCollected(u8 itemType)
{
    // só conta o item-alvo da fase (não qualquer item)
    if (cur->objective == OBJ_COLLECT && itemType == cur->collectItem) collected++;
}

u8 OBJECTIVE_update(u16 kills)
{
    if(CAMPAIGN_RESISTANCE_active())return CAMPAIGN_RESISTANCE_update();
    if(CF_active())return CF_update();
    if(CL_active())return CL_update();
    CR_OPS_update();
    switch (cur->objective)
    {
        case OBJ_REACH:
        case OBJ_ESCORT:
        {
            if(cur->objective==OBJ_ESCORT && !DINORAH_alive())return OBJ_LOST;
            const ArenaRect *r=&cur->route->exit;
            const s16 x=(cur->objective==OBJ_ESCORT ? dinorahX : px)+8;
            const s16 y=(cur->objective==OBJ_ESCORT ? dinorahY : py)+8;
            const bool together=cur->objective!=OBJ_ESCORT || getApproximatedDistance(px-dinorahX,py-dinorahY)<=64;
            if(hp>0 && together && x>=r->x && x<r->x+r->w && y>=r->y && y<r->y+r->h)arrivalTimer++;
            else arrivalTimer=0;
            return arrivalTimer>=(fps*2+4)/5 ? OBJ_WON : OBJ_ONGOING;
        }
        case OBJ_SURVIVE:
            if (surviveLeft) surviveLeft--;
            return surviveLeft ? OBJ_ONGOING : OBJ_WON;

        case OBJ_COLLECT:
            return (collected >= cur->objTarget) ? OBJ_WON : OBJ_ONGOING;

        case OBJ_PROTECT:
            NPC_update();                       // sofre dano de inimigos encostados
            if (!NPC_alive())
            {
                // Result panels capture the arena before clearing the NPC.
                // Remove the fallen statue before that frozen frame is saved.
                ARENA_showNpc(FALSE);
                return OBJ_LOST;
            }
            if (surviveLeft) surviveLeft--;
            return surviveLeft ? OBJ_ONGOING : OBJ_WON;

        default: // OBJ_KILL
            return (kills >= cur->killTarget) ? OBJ_WON : OBJ_ONGOING;
    }
}

// segundos restantes (arredonda p/ cima) do timer de sobrevivência
static u16 secsLeft(void) { return (u16) ((surviveLeft + fps - 1) / fps); }

// Values are composed inside the fixed left section of the24px panel.
// Escort HUD values are bounded to0..100. Keep their exact three digits
// without the general-purpose formatter on a target/cover state transition.
static void objectiveNumber3(char *out,u16 value)
{
    if(value<=100) {
        const char *digits=HUD_OBJECTIVE_NUMBERS[value];
        out[0]=digits[0];out[1]=digits[1];out[2]=digits[2];out[3]=0;return;
    }
    const u16 hundreds=divu(value,100),rest=value-hundreds*100,tens=divu(rest,10);
    out[0]='0'+hundreds;out[1]='0'+tens;out[2]='0'+rest-tens*10;out[3]=0;
}
static void drawBaseHUD(u16 kills)
{
    if(CAMPAIGN_RESISTANCE_drawHUD() || CF_drawHUD() || CL_drawHUD())return;
    char value[20],aux[12];
    switch(cur->objective) {
        case OBJ_REACH:
        case OBJ_ESCORT: {
            const u16 progress=OBJECTIVE_progress();
            const ArenaRect *r=&cur->route->exit;
            const u16 arrow=MARKERS_hudArrow(r->x+r->w/2-px-8,r->y+r->h/2-py-8);
            const u16 sig=progress+((u16)(arrow-MARKER_HUD_E)<<8)+(cur->objective==OBJ_ESCORT ? dinorahHp*137+dinorahState*31 : 0);
            if(sig==hudLast)return;
            // A route percentage can wait for the next light streaming frame.
            // Keep combat/health immediate while dense scenery enters view.
            if(cur->objective==OBJ_REACH && SCENESTREAM_heavyFrame())return;
            hudLast=sig;
            if(cur->objective==OBJ_REACH) {
                objectiveNumber3(value,progress);HUD_drawObjective("SAÍDA",arrow,value,0,"");
            } else {
                objectiveNumber3(value,dinorahHp);objectiveNumber3(aux,progress);
                HUD_drawObjective(dinorahState==DIN_WAITING ? "COBERTURA" : dinorahState==DIN_PAUSING ? "PASSAGEM" : "DINORAH",TILE_ICON_SHIELD,value,arrow,aux);
            }
            break;
        }
        case OBJ_SURVIVE: {
            const u16 seconds=secsLeft();if(seconds==hudLast)return;hudLast=seconds;
            sprintf(value,"%03u",seconds);HUD_drawObjective("RESISTA",TILE_CLOCK,value,0,"");break;
        }
        case OBJ_COLLECT:
            if(collected==hudLast)return;
            hudLast=collected;
            sprintf(value,"%02u/%02u",collected,cur->objTarget);
            HUD_drawObjective("RECOLHA",itemIcon(cur->collectItem),value,0,"");break;
        case OBJ_PROTECT: {
            const u16 life=npcHp<0 ? 0 : npcHp,seconds=secsLeft(),sig=seconds*512+life;
            if(sig==hudLast)return;
            hudLast=sig;
            sprintf(value,"%03u",life);sprintf(aux,"%02u",seconds);
            HUD_drawObjective("PROTEJA",TILE_ICON_SAINT,value,TILE_CLOCK,aux);break;
        }
        default:
            if(currentLevel && GRAPH_isFinal(currentLevel)) {
                u16 life=0;
                for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active && enemies[i].type==ENEMY_BOSS)life=enemies[i].hp;
                if(life==hudLast)return;
                hudLast=life;
                sprintf(value,"%03u/%03u",life,ENEMY_DEFS[ENEMY_BOSS]->hp);
                HUD_drawObjective("ESCORPIÃO",TILE_SKULL,value,0,"");
            } else {
                if(kills==hudLast)return;
                hudLast=kills;HUD_drawKills(kills,cur->killTarget);
            }
            break;
    }
}
void OBJECTIVE_drawHUD(u16 kills)
{
    // Nearby pressure mechanisms own the panel; avoid composing an escort
    // label only to overwrite it again in the same frame.
    if(!CR_OPS_drawHUD())drawBaseHUD(kills);
}

// redesenho incondicional (invalida o gate): para quando outro código pode ter
// escrito na linha 0 (ex.: volta da pausa) — desenha o HUD do objetivo ATIVO,
// seja ele mortes, tempo, coleta ou proteção
void OBJECTIVE_forceHUD(u16 kills)
{
    hudLast = 0xFFFF;
    CAMPAIGN_RESISTANCE_forceHUD();CF_forceHUD();CL_forceHUD();
    OBJECTIVE_drawHUD(kills);
}

void OBJECTIVE_prepText(char *buf, const LevelDef *def)
{
    if(CR_OPS_prepText(buf,def) || CAMPAIGN_RESISTANCE_prepText(buf,def) || CF_prepText(buf,def) || CL_prepText(buf,def))return;
    switch (def->objective)
    {
        case OBJ_REACH: strcpy(buf,"CHEGUE A SAÍDA SINALIZADA."); break;
        case OBJ_ESCORT: strcpy(buf,"LEVE DINORAH VIVA ATÉ A SAÍDA."); break;
        case OBJ_SURVIVE: sprintf(buf, "META: SOBREVIVA %d S", def->objTarget); break;
        case OBJ_COLLECT: sprintf(buf, "META: COLETE %d %s", def->objTarget, itemName(def->collectItem)); break;
        case OBJ_PROTECT: sprintf(buf, "META: PROTEJA O ALIADO %d S", def->objTarget); break;
        default:          sprintf(buf, "META: MATE %d INIMIGOS", def->killTarget); break;
    }
}

// Read-only snapshots for the pause screen; no simulation tick.
u16 OBJECTIVE_secondsLeft(void){return secsLeft();}
u16 OBJECTIVE_collected(void){return collected;}

u16 OBJECTIVE_progress(void)
{
    if(!cur || !cur->route)return 0;
    if(cur->objective==OBJ_ESCORT)return dinorahNode>=cur->route->count ? 100 : divu((u32)(dinorahNode-1)*100,cur->route->count-1);
    const s16 start=cur->route->points[0].x,end=cur->route->exit.x+cur->route->exit.w/2;
    s16 p=px+8-start;if(p<0)p=0;if(p>end-start)p=end-start;
    return divu((u32)p*100,end-start);
}
void OBJECTIVE_drawMarkers(u16 *n)
{
    CR_OPS_draw(n);CAMPAIGN_RESISTANCE_draw(n);CF_draw(n);CL_draw(n);
    if(!cur || !cur->route || (cur->objective!=OBJ_REACH && cur->objective!=OBJ_ESCORT))return;
    const ArenaRect *r=&cur->route->exit;
    MARKERS_destination(n,r->x+r->w/2,r->y+r->h/2);
    if(DINORAH_alive()) {
        const u16 bar=ARENA_npcBar(dinorahHp,100);
        if(bar)SPRITES_emit(n,dinorahX-8,dinorahY-40,SPRITE_SIZE(4,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,bar));
        if(dinorahState==DIN_WAITING || dinorahState==DIN_PAUSING)
            MARKERS_alert(n,dinorahX+8,dinorahY);
    }
}
