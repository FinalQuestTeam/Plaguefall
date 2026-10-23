#include "system/video/screens/loading.h"
#include "system/video/screens/result_font.h"
#include "system/audio/audio.h"
#include "system/audio/music.h"
#include "system/audio/sfx.h"
#include "system/video/spritelist.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/radio_panel_data.h"
#include "levels/graph.h"
#include "radio_panel.h"

// The selected radio monitor stays in WINDOW while the destination is built.
// Target writes to the borrowed tiles go to savedTiles, never over visible art.
#define FIRST 2
#define TILES RADIO_PANEL_OVERLAY_COUNT
#define FIRST_BYTE (FIRST*32)
#define END_BYTE ((FIRST+TILES)*32)
static u8 workDepth;
static volatile bool loadingActive;
static volatile u8 loadingDigit;
static u32 serviceFrame,loadingStart;
static u16 loadingMinimum,desiredPalette[16];
// Allocated only while preparing a phase. Mission pages keep no arena snapshot;
// this temporary shadow leaves the usual RAM budget available to pause/help.
static u32 *savedTiles;
static u16 savedWindow[64*3]; // only HUD rows are visible once play begins
static u8 oldWindowX,oldWindowY;
static u16 loadingFrames;

static void readVRAM(u16 address,u16 *dest,u16 words)
{
    volatile u16 *data=(u16 *)VDP_DATA_PORT;
    volatile u32 *ctrl=(u32 *)VDP_CTRL_PORT;
    while(words)
    {
        const u16 count=words>128 ? 128 : words;
        SYS_disableInts();VDP_setAutoInc(2);*ctrl=VDP_READ_VRAM_ADDR(address);
        for(u16 i=0;i<count;i++)*dest++=*data;
        SYS_enableInts();address+=count*2;words-=count;LOADING_poll();
    }
}
static void audioFrame(void)
{
    AUDIO_frameBegin();MUSIC_update();SFX_update();AUDIO_frameEnd();
}
void LOADING_workBegin(void)
{
    if(!workDepth)serviceFrame=vtimer;
    workDepth++;
}
void LOADING_workEnd(void){if(workDepth)workDepth--;}
bool LOADING_active(void){return loadingActive;}
void LOADING_setEnable(bool enabled){if(!loadingActive)VDP_setEnable(enabled);}
void LOADING_windowOff(void){if(!loadingActive)VDP_setWindowOff();}
void LOADING_setColor(u16 index,u16 color)
{
    if(loadingActive && index<16)desiredPalette[index]=color;
    else PAL_setColor(index,color);
}
void LOADING_setColors(u16 index,const u16 *colors,u16 count,TransferMethod method)
{
    if(!loadingActive){PAL_setColors(index,colors,count,method);return;}
    // Apply immediately during loading: a deferred palette must not overwrite
    // the overlay at the next VBlank or retain a caller's stack buffer.
    for(u16 i=0;i<count;i++)LOADING_setColor(index+i,colors[i]);
}
void LOADING_getColors(u16 index,u16 *colors,u16 count)
{
    PAL_getColors(index,colors,count);
    if(loadingActive)for(u16 i=0;i<count;i++) {
        if(index+i<16)colors[i]=desiredPalette[index+i];
    }
}
void LOADING_tiles(const u32 *data,u16 index,u16 count,TransferMethod method)
{
    if(loadingActive && index<FIRST+TILES && index+count>FIRST)
    {
        // Commit the destination immediately to its shadow, even for queued
        // callers: their temporary source need not outlive this preparation.
        LOADING_copyVRAM((const u16 *)data,index*32,count*16);return;
    }
    if(!workDepth || method!=DMA){VDP_loadTileData(data,index,count,method);return;}
    while(count) {
        const u16 chunk=count>64 ? 64 : count;
        VDP_loadTileData(data,index,chunk,DMA);LOADING_poll();
        data+=chunk*8;index+=chunk;count-=chunk;
    }
}
void LOADING_copyVRAM(const u16 *data,u16 address,u16 words)
{
    while(words) {
        u16 chunk=words>1024 ? 1024 : words;
        if(loadingActive && address<END_BYTE)
        {
            if(address<FIRST_BYTE)
            {
                const u16 before=(FIRST_BYTE-address)/2;
                if(chunk>before)chunk=before;
                DMA_doDma(DMA_VRAM,(void *)data,address,chunk,2);
            }
            else
            {
                const u16 inside=(END_BYTE-address)/2;
                if(chunk>inside)chunk=inside;
                memcpy((u8 *)savedTiles+address-FIRST_BYTE,data,chunk*2);
            }
        }
        else DMA_doDma(DMA_VRAM,(void *)data,address,chunk,2);
        LOADING_poll();
        data+=chunk;address+=chunk*2;words-=chunk;
    }
}
static void cell(u16 tile,u16 x,u16 y)
{
    VDP_setTileMapXY(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,FIRST+tile),x,y);
}
static void label(const char *text,u16 x,u16 y)
{
    for(u16 i=0;text[i] && x+i<39;i++)
    {
        const u8 glyph=(u8)text[i]-32;
        cell(glyph<96 ? RADIO_PANEL_GLYPHS[glyph] : RADIO_PANEL_BLACK_TILE,x+i,y);
    }
}
static void animate(void)
{
    const u32 elapsed=vtimer-loadingStart;
    const u16 second=loadingMinimum>=3 ? loadingMinimum/3 : 1;
    const u8 digit=elapsed<second ? 3 : elapsed<second*2 ? 2 : 1;
    if(digit==loadingDigit)return;
    loadingDigit=digit;
    VDP_fillTileMapRect(WINDOW,TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,FIRST+RADIO_PANEL_BLACK_TILE),16,10,8,8);
    // Native 8x8 glyph at 8x scale, matching option 1 without a second timer.
    for(u16 y=0;y<8;y++) {
        const u8 bits=RESULT_FONT[('0'+digit-32)*8+y];
        for(u16 x=0;x<8;x++)if(bits&(0x80>>x))cell(RADIO_PANEL_INK_TILE,16+x,10+y);
    }
    for(u16 i=0;i<3;i++)cell(i<digit ? RADIO_PANEL_LAMP_ON_TILE : RADIO_PANEL_LAMP_OFF_TILE,17+i*2,20);
    SFX_countPulse(FALSE);
}
void LOADING_poll(void)
{
    if(!workDepth || serviceFrame==vtimer)return;
    serviceFrame=vtimer;
    if(loadingActive){animate();loadingFrames++;}
    audioFrame();
    // Work proceeds within the current video frame. Waiting here would make
    // every following checkpoint look overdue and turn small chunks into
    // hundreds of compulsory idle frames. Screen owners flush queued DMA.
}
bool LOADING_begin(u16 minimumFrames,u8 missionNode)
{
    savedTiles=MEM_alloc(TILES*32);
    if(!savedTiles)return FALSE;
    LOADING_workBegin();
    SPRITES_hide();SYS_doVBlankProcess();
    readVRAM(FIRST*32,(u16 *)savedTiles,TILES*16);
    readVRAM(VDP_WINDOW,savedWindow,64*3);
    oldWindowX=VDP_getReg(17);oldWindowY=VDP_getReg(18);
    PAL_getColors(0,desiredPalette,16);
    LOADING_tiles((const u32 *)radio_panel_tiles,FIRST,TILES,DMA);
    const u16 *map=(const u16 *)radio_panel_map;
    for(u16 y=0;y<28;y++)
    {
        u16 row[40];
        for(u16 x=0;x<40;x++)row[x]=TILE_ATTR_FULL(PAL0,TRUE,FALSE,FALSE,FIRST+map[y*40+x]);
        VDP_setTileMapDataRow(WINDOW,row,y,0,40,CPU);LOADING_poll();
    }
    label("PREPARAÇÃO",15,2);label("PREPARE-SE",15,7);
    char phase[16];sprintf(phase,"FASE %s",GRAPH[missionNode].name);label(phase,3,26);
    const char *name=MISSION_name(missionNode);label(name,38-strlen(name),26);
    // All patterns/map data were prepared outside the visible mission's
    // reservation. Reveal them and their palette together during VBlank.
    SYS_doVBlankProcess();
    PAL_setColors(0,(const u16 *)radio_panel_palette,16,CPU);
    VDP_setWindowFullScreen();
    loadingMinimum=minimumFrames;loadingFrames=0;loadingDigit=0;
    loadingStart=vtimer;loadingActive=TRUE;animate();
    // Count from the first complete visible frame, not from fade-out/setup.
    SYS_doVBlankProcess();loadingStart=serviceFrame=vtimer;
    audioFrame();
    return TRUE;
}
void LOADING_end(void)
{
    if(!loadingActive)return;
    while(vtimer-loadingStart<loadingMinimum) {
        animate();audioFrame();loadingFrames++;serviceFrame=vtimer;
        SYS_doVBlankProcess();
    }
    // All queued destination transfers must finish before returning ownership.
    SYS_doVBlankProcess();
    loadingActive=FALSE;
    VDP_loadTileData((const u32 *)savedTiles,FIRST,TILES,DMA);
    MEM_free(savedTiles);savedTiles=NULL;
    VDP_setTileMapData(VDP_WINDOW,savedWindow,0,64*3,2,CPU);
    PAL_setColors(0,desiredPalette,16,DMA);
    VDP_setReg(17,oldWindowX);VDP_setReg(18,oldWindowY);
    LOADING_workEnd();
    SFX_countPulse(TRUE);
}
