#include "system/video/screens/loading.h"
// Resistance HUD: objective, four equipment slots, active mode, life and bar.

#include "system/video/screens/hud.h"
#include "system/video/markers.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "core/inventory.h"
#include "items/items.h"
#include "actors/shots.h"
#include "actors/player.h"
#include "system/video/floor.h"
#include "system/video/sprites/item_icons_data.h"
#include "system/video/sprites/icons_data.h"
#include "system/video/sprites/saint_data.h"
#include "levels/courtyard_data.h"

#define HUD_OPAQUE_BASE (TILE_USER_INDEX + FLOOR_TILE_BASE + COURTYARD_TILE_COUNT)
static const u16 opaqueTiles[HUD_OPAQUE_COUNT]={TILE_SKULL,TILE_BOMB_ICON,TILE_BOLT,TILE_ICON_SHIELD,TILE_ICON_ICE,TILE_ICON_FIRE,TILE_ICON_HEART,TILE_CLOCK,TILE_ICON_SAINT,TILE_ICON_SHOTS,TILE_ICON_SPEED};
static const u32 *const opaqueSources[HUD_OPAQUE_COUNT]={NULL,ITEM_BOMB_ICON_DATA,ITEM_CHAIN_ICON_DATA,ITEM_SHIELD_ICON_DATA,ITEM_ICE_ICON_DATA,ITEM_FIRE_ICON_DATA,ITEM_HEART_ICON_DATA,NULL,SAINT_ICON_DATA,ITEM_SHOTS_ICON_DATA,ITEM_SPEED_ICON_DATA};

void HUD_loadOpaqueIcons(void)
{
    // PAL1 index B is opaque black. Original icon/sprite tiles stay intact.
    u32 data[8];
    for(u16 i=0;i<HUD_OPAQUE_COUNT;i++) {
        for(u16 y=0;y<8;y++) {
            u32 row=opaqueSources[i] ? opaqueSources[i][y] : 0;
            if(!opaqueSources[i]) {
                const char *art=(i==0 ? ICON_SKULL_ART : ICON_CLOCK_ART)[y];
                for(u16 x=0;x<8;x++)if(art[x]=='#')row|=1UL<<((7-x)*4);
            }
            for(u16 x=0;x<8;x++)if(!(row&(15UL<<(x*4))))row|=11UL<<(x*4);
            data[y]=row;
        }
        LOADING_tiles(data,HUD_OPAQUE_BASE+i,1,DMA);
    }
}
u16 HUD_iconAttr(u16 tile,u16 pal)
{
    if(arenaActive && pal==PAL1)
        for(u16 i=0;i<HUD_OPAQUE_COUNT;i++)if(tile==opaqueTiles[i])
            return TILE_ATTR_FULL(pal,TRUE,FALSE,FALSE,HUD_OPAQUE_BASE+i);
    return TILE_ATTR_FULL(pal,FALSE,FALSE,FALSE,TILE_USER_INDEX+tile);
}

// The first120 menu-icon tiles are unused by live enemy frames. A persistent
// 3.8KiB native canvas permits exact pixel positions without extra palettes.
#include "system/video/screens/hud_panel_data.h"
#include "system/video/screens/result_font.h"
static u32 hudPixels[HUD_TILE_COUNT*8];
// Shared scratch: composers run sequentially on the main thread. Keeping this
// off the2.5KiB68000stack also protects the heap sentinel during interrupts.
static u32 regionBefore[17*3*8];
static u8 hudDirty[HUD_TILE_COUNT];
static u32 s_invSig;
static s16 lastLife=-1;
static bool hudPending;
static const char *objectiveLabel;
static u16 objectiveSymbol,objectiveAuxSymbol;
static char objectiveValue[20],objectiveAuxiliary[12];
typedef char hud_outside_route_and_shots[(HUD_TILE_COUNT<=180)?1:-1];

static void rect(u16 x,u16 y,u16 w,u16 h,u16 color)
{
    static const u32 leftMask[8]={0xffffffffUL,0x0fffffffUL,0x00ffffffUL,0x000fffffUL,0x0000ffffUL,0x00000fffUL,0x000000ffUL,0x0000000fUL};
    static const u32 rightMask[9]={0,0xf0000000UL,0xff000000UL,0xfff00000UL,0xffff0000UL,0xfffff000UL,0xffffff00UL,0xfffffff0UL,0xffffffffUL};
    const u32 ink=0x11111111UL*color;
    for(u16 yy=y;yy<y+h;yy++) {
        u32 *word=&hudPixels[((yy>>3)*40+(x>>3))*8+(yy&7)];
        u16 remaining=w,start=x&7;
        while(remaining) {
            const u16 count=remaining<8-start ? remaining : 8-start;
            const u32 mask=leftMask[start]&rightMask[start+count];
            *word=(*word&~mask)|(ink&mask);
            remaining-=count;start=0;word+=8;
        }
    }
}
static void blitRow(u16 x,u16 y,u32 ink,u32 mask)
{
    u32 *word=&hudPixels[((y>>3)*40+(x>>3))*8+(y&7)];
    const u16 shift=(x&7)*4;
    const u32 first=mask>>shift;
    *word=(*word&~first)|(ink>>shift);
    if(shift && x+8<320) {
        const u16 rest=32-shift;const u32 last=mask<<rest;
        word+=8;*word=(*word&~last)|(ink<<rest);
    }
}
static void text(const char *s,u16 x,u16 y,u16 color)
{
    const u32 ink=0x11111111UL*color;
    while(*s && x+8<=320) {
        const u8 c=*s++;
        if(c>=32 && c<128)for(u16 yy=0;yy<8;yy++) {
            const u32 mask=HUD_FONT_MASK[RESULT_FONT[(c-32)*8+yy]];
            blitRow(x,y+yy,ink&mask,mask);
        }
        x+=8;
    }
}
static const u32 *iconData(u16 tile)
{
    const u32 *marker=MARKERS_iconData(tile);if(marker)return marker;
    for(u16 i=0;i<HUD_OPAQUE_COUNT;i++)if(tile==opaqueTiles[i])return opaqueSources[i];
    return NULL;
}
static void icon(u16 tile,u16 x,u16 y)
{
    const u32 *data=iconData(tile);
    for(u16 yy=0;yy<8;yy++) {
        u32 row=0;
        if(data)row=data[yy];
        else if(tile==TILE_SKULL || tile==TILE_CLOCK) {
            const char *art=(tile==TILE_SKULL ? ICON_SKULL_ART : ICON_CLOCK_ART)[yy];
            for(u16 xx=0;xx<8;xx++)if(art[xx]=='#')row|=1UL<<((7-xx)*4);
        }
        const u32 nz=(row|(row>>1)|(row>>2)|(row>>3))&0x11111111UL;
        const u32 mask=(nz<<4)-nz;
        blitRow(x,y+yy,row,mask);
    }
}
static void beginRegion(u16 left,u16 width,u32 *old)
{
    for(u16 row=0;row<HUD_ROWS;row++) {
        const u16 offset=(row*40+left)*8;
        memcpy(old+row*width*8,hudPixels+offset,width*32);
        memcpy(hudPixels+offset,HUD_PANEL_DATA+offset,width*32);
    }
}
static void endRegion(u16 left,u16 width,const u32 *old)
{
    for(u16 row=0;row<HUD_ROWS;row++)for(u16 col=0;col<width;col++) {
        const u16 tile=row*40+left+col;
        if(memcmp(hudPixels+tile*8,old+(row*width+col)*8,32)){hudDirty[tile]=TRUE;hudPending=TRUE;}
    }
}
void HUD_begin(void)
{
    memcpy(hudPixels,HUD_PANEL_DATA,sizeof hudPixels);
    memset(hudDirty,0,sizeof hudDirty);hudPending=FALSE;lastLife=-1;s_invSig=0xffffffffUL;objectiveLabel=NULL;
    LOADING_tiles(hudPixels,HUD_TILE_BASE,HUD_TILE_COUNT,DMA);
    HUD_present();
}
void HUD_present(void)
{
    if(LOADING_active())return;
    for(u16 row=0;row<HUD_ROWS;row++)for(u16 col=0;col<40;col++)
        VDP_setTileMapXY(WINDOW,TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,HUD_TILE_BASE+row*40+col),col,row);
    VDP_setTextPlane(WINDOW);VDP_setWindowOnTop(HUD_ROWS);
}
void HUD_flush(void)
{
    // At most512bytes; retain the existing1024byte SAT/scroll reserve. ROM
    // actor/death uploads see the queued HUD bytes and back off normally.
    if(!hudPending)return;
    hudPending=FALSE;
    u16 remaining=16;
    for(u16 tile=0;tile<HUD_TILE_COUNT && remaining;tile++) {
        if(!hudDirty[tile])continue;
        u16 count=1;
        while(tile+count<HUD_TILE_COUNT && count<remaining && hudDirty[tile+count])count++;
        if(DMA_getQueueTransferSize()+count*32+1024>DMA_TRANSFER_CAPACITY_NTSC ||
           DMA_getQueueSize()+3>=DMA_getMaxQueueSize()){hudPending=TRUE;break;}
        if(!DMA_queueDma(DMA_VRAM,hudPixels+tile*8,(HUD_TILE_BASE+tile)*32,count*16,2)){hudPending=TRUE;break;}
        memset(hudDirty+tile,0,count);remaining-=count;tile+=count-1;
        if(!remaining)hudPending=TRUE;
    }
}
static void markRect(u16 x,u16 y,u16 w,u16 h)
{
    if(!w || !h)return;
    for(u16 row=y>>3;row<=(y+h-1)>>3;row++)
        for(u16 col=x>>3;col<=(x+w-1)>>3;col++)hudDirty[row*40+col]=TRUE;
    hudPending=TRUE;
}
static void editValue(const char *value,char *previous,u16 x,u16 color)
{
    if(!strcmp(value,previous))return;
    const u16 length=strlen(value),oldLength=strlen(previous),width=(length>oldLength ? length : oldLength)*8;
    rect(x,13,width,8,11);text(value,x,13,color);markRect(x,13,width,8);
    strcpy(previous,value);
}
void HUD_drawObjective(const char *label,u16 symbol,const char *value,u16 auxiliaryIcon,const char *auxiliary)
{
    const u16 color=symbol==TILE_ICON_SAINT || symbol==TILE_ICON_SHIELD ? 1 : 4;
    // The common timer/HP tick edits only its digits, not39tiles of labels,
    // frame and icons. This keeps protection/combat updates within budget.
    if(label==objectiveLabel && symbol==objectiveSymbol && auxiliaryIcon==objectiveAuxSymbol) {
        editValue(value,objectiveValue,symbol ? 20 : 8,color);
        editValue(auxiliary,objectiveAuxiliary,auxiliaryIcon ? 72 : 64,auxiliaryIcon ? 4 : 1);
        return;
    }
    u32 *old=regionBefore;beginRegion(0,13,old);
    text(label,8,3,1);
    if(symbol)icon(symbol,8,13);
    text(value,symbol ? 20 : 8,13,color);
    if(auxiliaryIcon)icon(auxiliaryIcon,60,13);
    text(auxiliary,auxiliaryIcon ? 72 : 64,13,auxiliaryIcon ? 4 : 1);
    endRegion(0,13,old);
    objectiveLabel=label;objectiveSymbol=symbol;objectiveAuxSymbol=auxiliaryIcon;
    strcpy(objectiveValue,value);strcpy(objectiveAuxiliary,auxiliary);
}
void HUD_drawKills(u16 kills,u16 target)
{
    char value[16];sprintf(value,"%02u/%02u",kills,target);
    HUD_drawObjective("ELIMINE",TILE_SKULL,value,0,"");
}
void HUD_drawLife(s16 life)
{
    if(life<0)life=0;
    if(life>100)life=100;
    if(life==lastLife)return;
    if(lastLife<0) {
        text("VIDA",242,3,1);rect(242,15,68,6,6);markRect(242,0,68,24);
    }
    lastLife=life;
    char value[4];sprintf(value,"%03u",life);
    rect(282,3,24,8,11);text(value,282,3,1);markRect(282,3,24,8);
    rect(243,16,66,4,11);
    const u16 fill=((u32)life*66+50)/100;
    if(fill){rect(243,16,fill,4,life<=25 ? 3 : 14);rect(243,16,fill,1,life<=25 ? 4 : 1);}
    markRect(243,16,66,4);
}
static u16 iconTile(u8 type)
{
    switch(type){case ITEM_CHAIN:return TILE_BOLT;case ITEM_SHIELD:return TILE_ICON_SHIELD;
        case ITEM_ICE:return TILE_ICON_ICE;case ITEM_FIRE:return TILE_ICON_FIRE;default:return TILE_BOMB_ICON;}
}
static u32 hudInvSig(void)
{
    u32 sig=INV_selected();
    for(u8 i=0;i<INV_POS;i++){u8 type,count;INV_view(i,&type,&count);sig=sig*131u+((u32)type<<8)+count;}
    sig=sig*131u+((u32)SHOTS_mode()<<8)+SHOTS_modeCharges();
    return sig*131u+(PLAYER_shieldRemaining()+fps-1)/fps;
}
void HUD_drawInventory(void)
{
    u32 *old=regionBefore;beginRegion(13,17,old);
    for(u8 i=0;i<INV_POS;i++) {
        const u16 x=108+i*26;const bool selected=i==INV_selected();
        rect(x,3,24,18,selected ? 4 : 10);rect(x+1,4,22,16,11);
        if(selected)rect(x+2,19,20,1,4);
        u8 type,count;INV_view(i,&type,&count);
        if(type==INV_EMPTY)text("-",x+8,8,9);
        else {
            char digit[2]={(char)('0'+(count>9 ? 9 : count)),0};
            icon(iconTile(type),x+3,8);text(digit,x+14,8,1);
        }
    }
    const u16 shieldSeconds=(PLAYER_shieldRemaining()+fps-1)/fps;
    const bool modeActive=SHOTS_mode()!=SHOTMODE_NONE && SHOTS_modeCharges();
    if(shieldSeconds) {
        const u16 y=modeActive ? 2 : 4,h=modeActive ? 10 : 16,contentY=modeActive ? 3 : 8;
        rect(214,y,20,h,4);rect(215,y+1,18,h-2,11);
        icon(TILE_ICON_SHIELD,216,contentY);
        char digit[2]={(char)('0'+shieldSeconds),0};text(digit,225,contentY,1);
    }
    if(modeActive) {
        const u16 y=shieldSeconds ? 12 : 4,h=shieldSeconds ? 10 : 16,contentY=shieldSeconds ? 13 : 8;
        rect(214,y,20,h,6);rect(215,y+1,18,h-2,11);
        icon(SHOTS_mode()==SHOTMODE_CHAIN ? TILE_BOLT : SHOTS_mode()==SHOTMODE_ICE ? TILE_ICON_ICE : TILE_ICON_FIRE,216,contentY);
        char digit[2]={(char)('0'+SHOTS_modeCharges()),0};text(digit,225,contentY,2);
    }
    endRegion(13,17,old);s_invSig=hudInvSig();
}
void HUD_drawInventoryIfDirty(void)
{
    if(hudInvSig()!=s_invSig)HUD_drawInventory();
}
