// Countdown borrows the tail of the live cache while simulation is frozen.
// Its allocator keeps the first140tiles available for the initial boss.
#include "system/video/screens/countdown.h"
#include "system/video/screens/radio_layout.h"
#include "system/video/sprites/tiles.h"
#include "system/video/spritelist.h"
#include "system/video/enemygfx.h"
#include "system/video/screens/hud.h"
#include "system/audio/sfx.h"
#include "core/game.h"
#include "radio_data.h"
#define BASE (TILE_USER_INDEX+ENEMY_ROT_BASE+ENEMY_CACHE_TILES-COUNTDOWN_CACHE_TILES)
static bool countdownActive;
static u8 countdownDigit;
static u16 goTimer;
typedef char countdown_fits[(COUNTDOWN_TILE_COUNT==COUNTDOWN_CACHE_TILES && ENEMY_CACHE_TILES-COUNTDOWN_CACHE_TILES>=ENEMY_MAX_FRAME_TILES)?1:-1];
bool COUNTDOWN_active(void){return countdownActive;}
void COUNTDOWN_close(void)
{
    countdownActive=FALSE;goTimer=0;
}
void COUNTDOWN_begin(void)
{
    COUNTDOWN_close();ENEMYGFX_reset();countdownActive=TRUE;
    countdownDigit=4;COUNTDOWN_set(3);
}
void COUNTDOWN_set(u8 number)
{
    if(!countdownActive || number==countdownDigit)return;
    countdownDigit=number;
    const u16 offset=number ? (3-number)*COUNTDOWN_TILE_COUNT : 3*COUNTDOWN_TILE_COUNT;
    VDP_loadTileData(((const u32 *)countdown_tiles)+offset*8,BASE,number ? COUNTDOWN_TILE_COUNT : 48,DMA);
    if(!number)goTimer=(fps*35+99)/100;
    SFX_countPulse(number==0);
}
void COUNTDOWN_update(void)
{
    if(goTimer && !--goTimer)COUNTDOWN_close();
}
void COUNTDOWN_draw(u16 *n)
{
    if(!countdownActive)return;
    const u16 width=countdownDigit ? 144 : 96,height=countdownDigit ? 80 : 32;
    const s16 left=countdownDigit ? 88 : 112,top=countdownDigit ? HUD_HEIGHT : HUD_HEIGHT+8;
    u16 tile=BASE;
    for(u16 y=0;y<height;y+=32)for(u16 x=0;x<width;x+=32)
    {
        const u16 w=width-x<32 ? width-x : 32,h=height-y<32 ? height-y : 32;
        SPRITES_emit(n,left+x+cameraX,top+y+cameraY,SPRITE_SIZE(w/8,h/8),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,tile));
        tile+=(w/8)*(h/8);
    }
}
