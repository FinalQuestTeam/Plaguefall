// Mission-owned, imagegen-authored world objects. Frames stay resident; only
// small tilemap rows change during an action, with no animation pattern DMA.
#include "system/video/objectivegfx.h"
#include "system/video/objective_art_data.h"
#include "system/video/campaign_ground_art.h"
#include "system/video/sewer_gate_art.h"
#include "system/video/phase08_transmitter.h"
#include "system/video/scene_stream.h"
#include "levels/graph.h"
#include "system/video/floor.h"
#include "system/video/spritelist.h"
#include "system/video/screens/loading.h"
#include "levels/arena.h"
#include "levels/operations.h"
#include "levels/courtyard_data.h"
#include "core/game.h"
#include "enemies/enemies.h"
#include "objective_art.h"
#include "system/video/sprites/tiles.h"

#define ART_BASE (TILE_USER_INDEX+FLOOR_TILE_BASE+32)
#define ART_CAP 560
typedef char objective_tiles_fit[(ART_BASE+ART_CAP<=TILE_USER_INDEX+FLOOR_TILE_BASE+COURTYARD_TILE_COUNT)?1:-1];

ObjectiveVisual objectiveVisuals[OBJECTIVE_VISUAL_CAP];
u16 objectiveAnimationEvents[OBJECTIVE_ART_COUNT];
u8 objectiveAnimationFrameMask[OBJECTIVE_ART_COUNT];
u16 objectiveArtBases[OBJECTIVE_ART_COUNT];
static u8 drawnFrames[OBJECTIVE_VISUAL_CAP],drawnVisibility[OBJECTIVE_VISUAL_CAP];
static s16 lastCol,lastRow,lastRight,lastBottom;
static bool dirty,campaignArt;
static u16 idleClock;

static const CampaignGroundArt *packedArt(u8 art)
{
    if((currentLevel==N_6A || currentLevel==N_6B) && art==OART_GATE)return &sewerGateGround;
    return &campaignGroundArt[art];
}
static void load(u8 art,u16 *cursor)
{
    const ObjectiveArt *a=&objectiveArt[art];
    objectiveArtBases[art]=*cursor;
    if(currentLevel==N_8 && art==OART_TRANSMITTER) {
        VDP_loadTileData(phase08TransmitterTiles,*cursor,PHASE08_TRANSMITTER_TILES,DMA);
        *cursor+=PHASE08_TRANSMITTER_TILES;return;
    }
    // Ground-only campaign mechanisms can address exact shared tiles through
    // a map. Keep contiguous frame storage for moving sprite objectives.
    if(campaignArt && packedArt(art)->count) {
        const CampaignGroundArt *packed=packedArt(art);
        VDP_loadTileData(packed->tiles,*cursor,packed->count,DMA);*cursor+=packed->count;return;
    }
    const u32 *source=(const u32 *)objective_animations+a->offset;
    const u16 tiles=a->tiles*6;
    VDP_loadTileData(source,*cursor,tiles,DMA);
    *cursor+=tiles;
}
void OBJECTIVEGFX_start(u8 mission)
{
    campaignArt=FALSE;
    memset(objectiveVisuals,0,sizeof objectiveVisuals);
    memset(objectiveAnimationEvents,0,sizeof objectiveAnimationEvents);
    memset(objectiveAnimationFrameMask,0,sizeof objectiveAnimationFrameMask);
    memset(objectiveArtBases,0,sizeof objectiveArtBases);memset(drawnFrames,255,sizeof drawnFrames);
    memset(drawnVisibility,0,sizeof drawnVisibility);idleClock=0;
    lastCol=lastRow=-1;dirty=TRUE;
    static const u8 arts[]={OART_NEST,OART_GENERATOR,OART_CARGO,OART_TRANSMITTER,OART_VALVE,OART_GATE,OART_TRAP,OART_RADIO};
    u16 cursor=ART_BASE;const bool enabled=VDP_getEnable();VDP_setEnable(FALSE);
    load(arts[mission],&cursor);
    if(mission==6)load(OART_CAGE,&cursor);
    VDP_setEnable(enabled);
}
bool OBJECTIVEGFX_startCampaign(u16 artMask)
{
    memset(objectiveVisuals,0,sizeof objectiveVisuals);
    memset(objectiveAnimationEvents,0,sizeof objectiveAnimationEvents);
    memset(objectiveAnimationFrameMask,0,sizeof objectiveAnimationFrameMask);
    memset(objectiveArtBases,0,sizeof objectiveArtBases);
    memset(drawnFrames,255,sizeof drawnFrames);memset(drawnVisibility,0,sizeof drawnVisibility);
    idleClock=0;lastCol=lastRow=-1;dirty=TRUE;campaignArt=TRUE;
    u16 cursor=TILE_USER_INDEX+FLOOR_TILE_BASE+ARENA_sceneTileCount(),required=0;
    for(u8 i=0;i<OBJECTIVE_ART_COUNT;i++)if(artMask&(1u<<i))
        required+=currentLevel==N_8 && i==OART_TRANSMITTER ? PHASE08_TRANSMITTER_TILES : packedArt(i)->count ? packedArt(i)->count : objectiveArt[i].tiles*6;
    const u16 workTiles=currentLevel==N_6B ? ARENA_WORK_BAR_TILE_COUNT : 0;
    if(cursor+required>TILE_USER_INDEX+FLOOR_TILE_BASE+COURTYARD_TILE_COUNT-workTiles)return FALSE;
    const bool enabled=VDP_getEnable();VDP_setEnable(FALSE);
    for(u8 i=0;i<OBJECTIVE_ART_COUNT;i++)if(artMask&(1u<<i))load(i,&cursor);
    VDP_setEnable(enabled);return TRUE;
}
void OBJECTIVEGFX_place(u8 slot,u8 art,s16 x,s16 y,bool ground)
{
    objectiveVisuals[slot]=(ObjectiveVisual){x,y,0,art,0,0,TRUE,ground,FALSE};dirty=TRUE;
}
void OBJECTIVEGFX_prime(u8 slot,bool primed)
{
    ObjectiveVisual *v=&objectiveVisuals[slot];
    if(v->mode || v->primed==primed)return;
    v->primed=primed;v->frame=primed ? 1 : 0;dirty=TRUE;
}
void OBJECTIVEGFX_activate(u8 slot)
{
    ObjectiveVisual *v=&objectiveVisuals[slot];
    if(v->mode==1)return;
    v->mode=1;v->age=0;v->frame=2;v->visible=TRUE;dirty=TRUE;
    objectiveAnimationEvents[v->art]++;
}
void OBJECTIVEGFX_idle(u8 slot)
{
    ObjectiveVisual *v=&objectiveVisuals[slot];
    if(!v->mode && !v->primed)return;
    v->mode=0;v->age=0;v->frame=0;v->primed=FALSE;dirty=TRUE;
}
void OBJECTIVEGFX_hide(u8 slot)
{if(objectiveVisuals[slot].visible){objectiveVisuals[slot].visible=FALSE;dirty=TRUE;}}
void OBJECTIVEGFX_settle(u8 slot,u8 frame)
{
    ObjectiveVisual *v=&objectiveVisuals[slot];
    if(v->mode==2 && v->frame==frame)return;
    v->mode=2;v->age=0;v->frame=frame;dirty=TRUE;
}
void OBJECTIVEGFX_update(void)
{
    if(++idleClock>=fps)idleClock=0;
    const u16 step=fps/5;
    for(u8 i=0;i<OBJECTIVE_VISUAL_CAP;i++) {
        ObjectiveVisual *v=&objectiveVisuals[i];if(!v->visible)continue;
        const u8 previous=v->frame;
        if(v->mode==1) {
            if(++v->age>=step*3){v->mode=2;v->frame=v->art==OART_RADIO ? (campaignArt ? 3 : 4) : v->art==OART_CARGO && i<3 ? 3 : 5;}
            else v->frame=2+divu(v->age,step);
        } else if(v->mode==3) { // radio short circuit, then persistent wreck
            if(++v->age>=step*3){v->mode=4;v->frame=5;}
            else v->frame=(v->age&4) ? 1 : 3;
        } else if(v->mode==5) {
            v->frame=1+divu(idleClock,fps/4)%4;
        } else if(v->mode==2) {
            if(v->age<fps*2)v->age++;
            if(v->art==OART_GENERATOR) {
                const u8 pulse=divu(idleClock*4,fps);
                v->frame=campaignArt ? 2+(idleClock>=fps/2) : pulse==0 ? 5 : pulse==2 ? 3 : 4;
            }
            if(v->art==OART_REFUGEE && v->age>=fps)v->visible=FALSE;
        } else if(!v->mode) {
            if(v->art==OART_TRANSMITTER && campaignArt) {
                static const u8 signalFrames[]={0,2,1,3};
                v->frame=signalFrames[divu(idleClock*4,fps)];
            } else if(v->art==OART_RADIO && campaignArt)v->frame=2+(idleClock>=fps/2);
            else if(v->art==OART_TRANSMITTER || v->art==OART_RADIO)v->frame=idleClock>=fps/2;
            else if(v->art==OART_CAGE && v->primed)v->frame=1+divu(idleClock*3,fps);
            else v->frame=v->primed ? 1 : 0;
        }
        objectiveAnimationFrameMask[v->art]|=1u<<v->frame;
        if(previous!=v->frame)dirty=TRUE;
    }
}
static void mapVisual(u8 slot,s16 clipLeft,s16 clipTop,s16 clipRight,s16 clipBottom)
{
    const ObjectiveVisual *v=&objectiveVisuals[slot];const ObjectiveArt *a=&objectiveArt[v->art];
    const s16 x=v->x-a->width/2,y=v->y-a->height+8;
    const s16 col=x/8,row=y/8;
    const u8 width=a->width/8,height=a->height/8;
    // Campaign objects have no labels outside their bounds. A completely
    // clipped object cannot touch the ring, including when restoring it.
    if(campaignArt && (col+width<=clipLeft || col>=clipRight || row+height<=clipTop || row>=clipBottom))return;
    const u16 base=objectiveArtBases[v->art]+v->frame*a->tiles;
    const u8 pal=v->mode==3 && (v->age&4) ? PAL0 : PAL1;
    const bool foreground=v->art==OART_CAGE || (v->mode==1 && (v->art==OART_NEST || v->art==OART_TRAP));
    for(u8 r=0;r<height;r++) {
        if(row+r<clipTop || row+r>=clipBottom)continue;
        s16 left=col,right=col+width;
        if(left<clipLeft)left=clipLeft;if(right>clipRight)right=clipRight;
        if(left>=right)continue;
        u16 data[8];
        for(s16 c=left;c<right;c++) {
            const u16 local=(c-col)*height+r;
            const bool ink=v->visible && ((campaignArt && (currentLevel==N_6A || currentLevel==N_6B) && v->art==OART_GATE) ? sewerGateVisible[v->frame*a->tiles+local] : objectiveTileVisible[(a->offset>>3)+v->frame*a->tiles+local]);
            u16 tile=base+local;
            if(campaignArt && packedArt(v->art)->count) {
                const u16 *indices=packedArt(v->art)->map;
                tile=objectiveArtBases[v->art]+indices[v->frame*a->tiles+local];
            }
            data[c-left]=ink ? TILE_ATTR_FULL(pal,foreground,FALSE,FALSE,tile) : (campaignArt ? (SCENESTREAM_active() ? 0 : ARENA_backgroundAttr(c,row+r)) : OPS_backgroundAttr(c,row+r));
        }
        VDP_setTileMapDataRow(BG_A,data,(row+r)&31,left&63,right-left,DMA_QUEUE_COPY);
    }
    const bool numbered=slot<3 && v->art!=OART_RADIO && v->art!=OART_TRAP && v->art!=OART_CAGE;
    const char glyph=v->art==OART_RADIO ? 'R' : v->art==OART_TRAP ? 'C' : slot==3 ? 'D' : v->mode==2 ? '+' : '1'+slot;
    if(!campaignArt && (numbered || v->art==OART_RADIO || (v->art==OART_TRAP && !slot) || (v->art==OART_CARGO && slot==3))) {
        const s16 labelRow=row-1,labelCol=(v->x-4)/8;
        if(labelRow>=clipTop && labelRow<clipBottom && labelCol>=clipLeft && labelCol<clipRight) {
            const u16 label=v->visible ? TILE_ATTR_FULL(PAL0,FALSE,FALSE,FALSE,TILE_FONT_INDEX+glyph-32) : 0;
            VDP_setTileMapDataRow(BG_A,&label,labelRow&31,labelCol&63,1,DMA_QUEUE_COPY);
        }
    }
}
void OBJECTIVEGFX_ground(bool force)
{
    const bool streamed=SCENESTREAM_active();
    const s16 col=cameraX/8,row=(cameraY+(streamed ? 24 : 0))/8;
    const s16 right=streamed ? (cameraX+319)/8+1 : col+64;
    const s16 bottom=streamed ? (cameraY+223)/8+1 : row+32;
    const bool moved=lastCol!=col || lastRow!=row || lastRight!=right || lastBottom!=bottom;
    if(!dirty && !force && !moved)return;
    for(u8 i=0;i<OBJECTIVE_VISUAL_CAP;i++) {
        const ObjectiveVisual *v=&objectiveVisuals[i];
        if(!v->ground || !objectiveArtBases[v->art])continue;
        const bool changed=drawnFrames[i]!=v->frame || drawnVisibility[i]!=v->visible;
        if(force || changed || lastCol<0)mapVisual(i,col,row,right,bottom);
        else if(moved && v->visible) {
            // Streamed maps pin only visible patterns. Paint the same edges
            // cleared by SCENESTREAM_move, including partial-tile view changes.
            if(col<lastCol)mapVisual(i,col,row,lastCol,bottom);
            if(right>lastRight)mapVisual(i,lastRight,row,right,bottom);
            if(row<lastRow)mapVisual(i,col,row,right,lastRow);
            if(bottom>lastBottom)mapVisual(i,col,lastBottom,right,bottom);
        }
        drawnFrames[i]=v->frame;drawnVisibility[i]=v->visible;
    }
    lastCol=col;lastRow=row;lastRight=right;lastBottom=bottom;dirty=FALSE;
}
static void sprite(u16 *n,u8 art,u8 frame,s16 x,s16 y,u8 palette)
{
    const ObjectiveArt *a=&objectiveArt[art];
    if(currentLevel==N_8 && art==OART_TRANSMITTER) {
        // Cull the complete object before traversing its exact sprite strips.
        // A priority target can be several screens away in the urban arena.
        if(x+16<=cameraX || x-16>=cameraX+320 || y+8<=cameraY+24 || y-24>=cameraY+224)return;
        for(u8 i=0;i<8;i++) {
            const u8 strip=phase08TransmitterStrips[frame*8+i];
            if(strip!=PHASE08_TRANSMITTER_BLANK)
                SPRITES_emit(n,x-16+(i/2)*8,y-24+(i%2)*16,SPRITE_SIZE(1,2),
                    TILE_ATTR_FULL(palette,TRUE,FALSE,FALSE,objectiveArtBases[art]+strip*2));
        }
        return;
    }
    const u16 base=objectiveArtBases[art]+frame*a->tiles;
    // Moving objectives are at most32px wide; split tall civilians at32px.
    const s16 left=x-a->width/2,top=y-a->height+8;
    const u8 rows=a->height/8,cols=a->width/8;
    if(rows<=4)SPRITES_emit(n,left,top,SPRITE_SIZE(cols,rows),TILE_ATTR_FULL(palette,TRUE,FALSE,FALSE,base));
    else {
        // Civilians use the same two-piece32x48 layout as Damião/Dinorah.
        SPRITES_emit(n,left,top,SPRITE_SIZE(4,4),TILE_ATTR_FULL(palette,TRUE,FALSE,FALSE,base));
        SPRITES_emit(n,left,top+32,SPRITE_SIZE(4,2),TILE_ATTR_FULL(palette,TRUE,FALSE,FALSE,base+16));
    }
}
void OBJECTIVEGFX_draw(u16 *count)
{
    for(u8 i=0;i<OBJECTIVE_VISUAL_CAP;i++) {
        const ObjectiveVisual *v=&objectiveVisuals[i];
        if(v->visible && !v->ground && objectiveArtBases[v->art]) {
            const bool live=v->art==OART_TRANSMITTER && !v->mode && i<3;
            sprite(count,v->art,v->frame,v->x,v->y,live && enemies[i].hitFlash ? PAL0 : PAL1);
            if(live && (enemies[i].frozen || enemies[i].burn))
                SPRITES_emit(count,v->x+12,v->y-32,SPRITE_SIZE(1,1),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,
                    TILE_USER_INDEX+(enemies[i].frozen ? TILE_ENEMY_ICE : TILE_ENEMY_FIRE)));
        }
    }
}
void OBJECTIVEGFX_cargo(u16 *n,s16 x,s16 y)
{SPRITES_emit(n,x-8,y-8,SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,TILE_USER_INDEX+TILE_BAG));}
bool OBJECTIVEGFX_pending(void)
{
    for(u8 i=0;i<OBJECTIVE_VISUAL_CAP;i++)if(objectiveVisuals[i].visible && (objectiveVisuals[i].mode==1 || objectiveVisuals[i].mode==3))return TRUE;
    return FALSE;
}
