// Common navigation language: resistance-metal badges, shared object palette.
#include "system/video/markers.h"
#include "system/video/marker_art.h"
#include "system/video/spritelist.h"
#include "system/video/screens/hud.h"
#include "system/video/sprites/tiles.h"
#include "levels/arena.h"
#include "core/game.h"
#include "routes.h"
#define BASE (TILE_USER_INDEX+ENEMY_ICON_BASE+180)
typedef char badges_fit_between_countdown_and_shots[(GAME_MARKER_TILES<=45)?1:-1];
void MARKERS_load(void){VDP_loadTileData((const u32 *)game_markers,BASE,GAME_MARKER_TILES,DMA);}
u16 MARKERS_hudArrow(s16 dx,s16 dy)
{
    return abs(dx)>abs(dy) ? (dx<0 ? MARKER_HUD_W : MARKER_HUD_E) : (dy<0 ? MARKER_HUD_N : MARKER_HUD_S);
}
const u32 *MARKERS_iconData(u16 symbol)
{
    return symbol>=MARKER_HUD_E && symbol<=MARKER_HUD_N ? GAME_MARKER_ICONS[symbol-MARKER_HUD_E] : NULL;
}
static void arrow(u16 *n,s16 x,s16 y,u16 direction)
{
    const u16 pulse=((vtimer/(fps/2))&1)*4;
    const bool vertical=direction==MARKER_HUD_S || direction==MARKER_HUD_N;
    SPRITES_emit(n,x,y,SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL1,TRUE,direction==MARKER_HUD_N,direction==MARKER_HUD_W,BASE+(vertical ? 8 : 0)+pulse));
}
void MARKERS_destination(u16 *n,s16 centerX,s16 centerY)
{
    s16 x=centerX-8,y=centerY-40;
    const s16 left=cameraX+4,right=cameraX+300,top=cameraY+HUD_HEIGHT+4,bottom=cameraY+204;
    const bool visible=x>=left && x<=right && y>=top && y<=bottom;
    const u16 direction=visible ? MARKER_HUD_S : MARKERS_hudArrow(centerX-(cameraX+160),centerY-(cameraY+(224+HUD_HEIGHT)/2));
    if(x<left)x=left;
    if(x>right)x=right;
    if(y<top)y=top;
    if(y>bottom)y=bottom;
    arrow(n,x,y,direction);
}
void MARKERS_alert(u16 *n,s16 centerX,s16 feetY)
{
    s16 x=centerX-8,y=feetY-60;
    const s16 top=cameraY+HUD_HEIGHT+4;
    if(y<top){x=centerX+20;y=feetY-30;}
    if(x<cameraX+4)x=cameraX+4;
    if(x>cameraX+300)x=cameraX+300;
    if(y<top)y=top;
    if(y>cameraY+204)y=cameraY+204;
    SPRITES_emit(n,x,y,SPRITE_SIZE(2,2),TILE_ATTR_FULL(PAL1,TRUE,FALSE,FALSE,BASE+16+((vtimer/(fps/2))&1)*4));
}
