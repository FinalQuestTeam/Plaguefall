#include "text_data.h"
#include "system/video/screens/loading.h"
// Frozen native scenery + opaque resistance card. PAL2 is free once actors
// are hidden; PAL0/1/3 retain the scene's original colours. Only referenced
// background patterns are relocated, freeing VRAM for the card's own pixels.
#include "system/video/screens/result.h"
#include "system/video/screens/result_font.h"
#include "system/video/screens/panel_data.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/hud.h"
#include "system/video/spritelist.h"
#include "system/video/tilegen.h"
#include "system/video/floor.h"
#include "system/video/enemygfx.h"
#include "system/video/scene_stream.h"
#include "system/video/sprites/tiles.h"
#include "core/game.h"
#include "actors/dinorah.h"
#include "core/stats.h"
#include "core/death.h"
#include "levels/graph.h"
#include "levels/test.h"
#include "actors/shots.h"
#include "actors/player.h"
#include "system/audio/sfx.h"
#include "system/audio/music.h"
#include "interface_data.h"
// Result text is rasterized into the card. It can borrow the font's96 tiles
// until RESULT_close restores them. BG_B begins at0xc000 (tile1536).
#define RESULT_PATTERN_END 1536
#define BG_CAP (RESULT_PATTERN_END - FIRST - CARD_MAX_TILES)
#define CARD_W 32
#define CARD_MAX_H 23
#define CARD_MAX_TILES (CARD_W*CARD_MAX_H)
#define MAP_WORDS (64*32)
#define FIRST (TILE_USER_INDEX + NUM_TILES)
typedef char result_vram_fits[(FIRST+BG_CAP+CARD_MAX_TILES<=RESULT_PATTERN_END)?1:-1];
static bool resultActive,armed;
static bool cardVisible;
static u8 resultKind,choice,exitView,exitChoice;
static u16 age,resultKills,cardBase,cardTop,cardHeight;
static u16 resultPalette[64];
static u32 *card;
volatile u16 resultCaptureFault,resultCaptureTileCount;

static void readVRAM(u16 address,u16 *dest,u16 words)
{
    volatile u16 *data=(u16 *)VDP_DATA_PORT;
    volatile u32 *ctrl=(u32 *)VDP_CTRL_PORT;
    SYS_disableInts();VDP_setAutoInc(2);*ctrl=VDP_READ_VRAM_ADDR(address);
    while(words) {
        const u16 chunk=words>128 ? 128 : words;
        for(u16 i=0;i<chunk;i++)*dest++=*data;
        words-=chunk;SYS_enableInts();LOADING_poll();
        // VBlank/DMA may change the VDP address and auto-increment.
        address+=chunk*2;
        if(words){SYS_disableInts();VDP_setAutoInc(2);*ctrl=VDP_READ_VRAM_ADDR(address);}
    }
}
static bool begin(void)
{
    resultCaptureFault=0;resultCaptureTileCount=0;
    // Gameplay is finished. Freeze its VRAM pixels and release the live tile
    // cache before allocating capture scratch; retries reload the arena.
    SCENESTREAM_end();
    // Snapshot one background map. Inspect procedural BG_A floor rows in
    // small stack chunks rather than retaining a second4KiB plane in heap.
    u16 *maps=MEM_alloc(MAP_WORDS*2);
    u16 *lookup=MEM_alloc(2048*2);
    if(!maps || !lookup)
    {resultCaptureFault=1;if(maps)MEM_free(maps);if(lookup)MEM_free(lookup);return FALSE;}
    SPRITES_hide();SYS_doVBlankProcess();
    PAL_getColors(0,resultPalette,64);
    readVRAM(VDP_BG_B,maps,MAP_WORDS);
    memset(lookup,0xff,2048*2);
    // The live WINDOW HUD hides these rows. A streamed scene deliberately
    // does not populate them, so never expose their stale map cells when
    // the result turns WINDOW off. Clear the intersecting tile rows.
    if(arenaActive)for(u16 row=(u16)cameraY>>3;row<=((u16)cameraY+HUD_HEIGHT-1)>>3;row++)
        memset(maps+(row&31)*64,0,128);
    if(!arenaActive)for(u16 row=1;row<32;row++)
    {
        u16 foreground[64];readVRAM(VDP_BG_A+row*128,foreground,64);
        for(u16 col=0;col<64;col++)
        {
            const u16 tile=foreground[col]&0x7ff;
            if(tile==TILE_USER_INDEX+TILE_WALL || tile==TILE_USER_INDEX+TILE_LAVA || tile==TILE_USER_INDEX+TILE_MUD)
                maps[row*64+col]=foreground[col];
        }
    }
    u16 count=0;
    for(u16 i=0;i<MAP_WORDS;i++)
    {
        const u16 attr=maps[i],tile=attr&0x7ff;
        if(!tile){maps[i]=0;continue;}
        if(lookup[tile]==0xffff)
        {
            if(count==BG_CAP)
            {resultCaptureFault=2;resultCaptureTileCount=count;MEM_free(maps);MEM_free(lookup);return FALSE;}
            lookup[tile]=FIRST+count++;
        }
        maps[i]=(attr&0xf800)|lookup[tile];
    }
    resultCaptureTileCount=count;
    // Allocate only patterns actually referenced, after counting. Read them
    // all before relocation can overwrite their old VRAM addresses.
    u16 *patterns=MEM_alloc(count*32);
    if(!patterns){resultCaptureFault=1;MEM_free(maps);MEM_free(lookup);return FALSE;}
    for(u16 tile=0;tile<2048;tile++)if(lookup[tile]!=0xffff)
        readVRAM(tile*32,patterns+(lookup[tile]-FIRST)*16,16);
    LOADING_tiles((const u32 *)patterns,FIRST,count,DMA);
    VDP_clearPlane(BG_A,TRUE);
    VDP_setTileMapData(VDP_BG_B,maps,0,MAP_WORDS,2,CPU);
    VDP_setHorizontalScroll(BG_A,0);VDP_setVerticalScroll(BG_A,0);VDP_setWindowOff();
    cardBase=FIRST+count;
    MEM_free(patterns);MEM_free(lookup);MEM_free(maps);
    card=MEM_alloc(CARD_MAX_TILES*32);
    if(!card){resultCaptureFault=3;return FALSE;}
    PAL_setColors(PAL2*16,(const u16 *)interface_palette,16,DMA);
    cardVisible=FALSE;choice=exitView=exitChoice=0;age=0;armed=FALSE;
    return TRUE;
}
static void artRows(u16 first,u16 count)
{
    for(u16 y=first;y<first+count;y++)for(u16 x=0;x<CARD_W;x++)
    {
        const u16 sx=x==31 ? 39 : x,sy=y>=cardHeight-4 ? 28-cardHeight+y : y;
        const u16 tile=((const u16 *)interface_map)[sy*40+sx];
        memcpy(card+(y*CARD_W+x)*8,((const u32 *)interface_tiles)+tile*8,32);
        if(!x)LOADING_poll();
    }
}
static void art(u16 top,u16 height)
{
    cardTop=top;cardHeight=height;artRows(0,height);
}
static void fill(u16 x,u16 y,u16 w,u16 h,u16 color)
{
    const u32 pixels=(u32)color*0x11111111UL;
    for(u16 row=y;row<y+h;row++)for(u16 col=x>>3;col<(x+w)>>3;col++)
        card[((row>>3)*CARD_W+col)*8+(row&7)]=pixels;
}
static void line(const char *text,u16 row,u16 color)
{
    const u16 len=strlen(text);
    if(len>29 || row<cardTop || row>=cardTop+cardHeight)return;
    const u16 x=(256-len*8)/2,shift=(x&7)*4;
    for(u16 i=0;i<len;i++)
    {
        LOADING_poll();
        const u8 glyph=(u8)text[i]-32;if(glyph>=96)continue;
        u32 *dest=card+((row-cardTop)*CARD_W+(x>>3)+i)*8;
        for(u16 gy=0;gy<8;gy++)
        {
            u32 bits=RESULT_FONT[glyph*8+gy];
            bits=(bits|(bits<<12))&0x000f000fUL;
            bits=(bits|(bits<<6))&0x03030303UL;
            bits=(bits|(bits<<3))&0x11111111UL;
            const u32 mask=bits*15,ink=bits*color;
            if(!shift)dest[gy]=(dest[gy]&~mask)|ink;
            else
            {
                dest[gy]=(dest[gy]&~(mask>>shift))|(ink>>shift);
                dest[gy+8]=(dest[gy+8]&~(mask<<(32-shift)))|(ink<<(32-shift));
            }
        }
    }
}
static void menu(const char *first,const char *second,u8 selected,u16 row,u16 controls)
{
    fill(16,(row+selected*2-cardTop)*8-3,224,14,PANEL_RUST_INDEX);
    char buf[40];sprintf(buf,"%s%s",selected ? "" : "> ",first);line(buf,row,selected ? 14 : 15);
    sprintf(buf,"%s%s",selected ? "> " : "",second);line(buf,row+2,selected ? 15 : 14);
    line("CIMA/BAIXO: ESCOLHER",controls,2);
}
static void drawSelection(void)
{
    // Rebuild only the two choices and their highlight. Keep scenery, text,
    // plane maps and the display enabled throughout controller navigation.
    const u16 first=(exitView ? 15 : 16)-cardTop-1;
    artRows(first,5);
    if(exitView)menu("VOLTAR À TENTATIVA","SAIR PARA O TÍTULO",exitChoice,15,20);
    else if(resultKind==3)menu("VOLTAR AO TÍTULO","JOGAR NOVAMENTE",choice,16,21);
    else menu("TENTAR NOVAMENTE","VOLTAR AO TÍTULO",choice,16,21);
    // Five rows = 5 KiB: fits a single NTSC or PAL vertical blank.
    VDP_waitVSync();
    LOADING_tiles(card+first*CARD_W*8,cardBase+first*CARD_W,5*CARD_W,DMA);
}
static void submit(void)
{
    const bool enabled=VDP_getEnable();
    // The first card uploads into unused patterns while the frozen scenery
    // stays visible. Replacing an existing modal still requires a blanked DMA.
    if(cardVisible)VDP_setEnable(FALSE);
    LOADING_tiles(card,cardBase,CARD_W*cardHeight,DMA);
    // Confirmation is shorter than the defeat card: transparent outer rows
    // reveal the same frozen BG_B, rather than leaving the old paper behind.
    VDP_clearPlane(BG_A,TRUE);
    for(u16 y=0;y<cardHeight;y++)
    {
        u16 row[CARD_W];
        for(u16 x=0;x<CARD_W;x++)row[x]=TILE_ATTR_FULL(PAL2,TRUE,FALSE,FALSE,cardBase+y*CARD_W+x);
        VDP_setTileMapDataRow(BG_A,row,cardTop+y,4,CARD_W,DMA_QUEUE_COPY);
    }
    SYS_doVBlankProcess();
    VDP_setEnable(enabled);cardVisible=TRUE;resultActive=TRUE;
}
static void draw(void)
{
    char buf[64];
    if(exitView)
    {
        art(5,19);line("SAIR DA PARTIDA?",7,12);
        line("O PROGRESSO DESTA PARTIDA",10,14);line("SERÁ PERDIDO.",12,14);
        menu("VOLTAR À TENTATIVA","SAIR PARA O TÍTULO",exitChoice,15,20);
        line("A: OK  B/START: CANCELAR",22,15);
    }
    else if(resultKind==0)
    {
        const bool ruleTest=!currentLevel && testStage==TEST_RULE_ROOM;
        const u8 ruleNode=ruleTest ? TEST_ruleNode() : currentLevel;
        art(2,23);line(DINORAH_active() && !DINORAH_alive() ? "ESCOLTA INTERROMPIDA" : "FIM DA TENTATIVA",4,12);line(DINORAH_active() && !DINORAH_alive() ? "DINORAH CAIU." : "DAMIÃO CAIU.",6,12);
        if(ruleTest)sprintf(buf,"TREINO / ETAPAS %s",ruleNode==N_1 ? "1 A 5" : ruleNode==N_6A ? "6 A 11" : "12 A 16");
        else if(currentLevel)sprintf(buf,"FASE %s",GRAPH[currentLevel].name);else sprintf(buf,"FASE TESTE %u",testStage);
        line(buf,7,2);line(ruleTest ? TEST_name(testStage) : MISSION_name(currentLevel),8,14);
        const u16 seconds=STATS_seconds();
        if(ruleTest)sprintf(buf,"TIRO: %u / VELOC: +%u%%",SHOTS_power(),PLAYER_speedBonus());
        else if(LEVEL_current()->objective==OBJ_KILL)sprintf(buf,"INIMIGOS: %02u/%02u | %02u:%02u",resultKills,LEVEL_current()->killTarget,seconds/60,seconds%60);
        else sprintf(buf,"TEMPO DA TENTATIVA: %02u:%02u",seconds/60,seconds%60);
        line(buf,10,2);line("RECOMECE A MESMA FASE.",12,14);
        line("VIDA CHEIA AO REPETIR.",13,14);
        if(!ruleNode)line("ITENS E MELHORIAS ZERADOS.",14,14);
        else if(DEATH_rule(ruleNode)==DEATH_KEEP)line("BORNAL: RECUPERE TUDO.",14,14);
        else if(DEATH_rule(ruleNode)==DEATH_REDUCE)line("BORNAL: -1 NÍVEL E -1 ITEM.",14,14);
        else line("BORNAL: ATÉ 1 TIRO E 1 VELOC.",14,14);
        menu("TENTAR NOVAMENTE","VOLTAR AO TÍTULO",choice,16,21);
        line("A: OK   START: TENTAR",23,15);
    }
    else if(resultKind==3)
    {
        art(3,22);line("VITÓRIA / ETAPA 16 DE 16",5,12);
        line("O ESCORPIÃO CAIU.",8,12);line("O SINAL DELE PAROU.",10,14);
        line("HOJE, DÁ PRA VOLTAR PRA CASA.",12,14);line("CAMPANHA CONCLUÍDA.",14,2);
        menu("VOLTAR AO TÍTULO","JOGAR NOVAMENTE",choice,16,21);
        line("A/START: CONFIRMAR",23,15);
    }
    else
    {
        art(6,16);
        sprintf(buf,"%s / FASE %s",resultKind==2 ? "MUDANÇA DE ROTA" : "OBJETIVO CUMPRIDO",GRAPH[currentLevel].name);
        line(buf,8,12);
        if(resultKind==2)
        {line("SINAL PERDIDO.",11,12);line("A RETIRADA SERÁ POR TERRA.",13,14);line("A MISSÃO CONTINUA.",15,2);}
        else if(LEVEL_current()->objective==OBJ_REACH)
        {line("SAÍDA ALCANÇADA.",11,12);line("OS TÚNEIS FICARAM PARA TRÁS.",13,14);line("SIGA ATÉ O SINALIZADOR.",15,2);}
        else if(LEVEL_current()->objective==OBJ_ESCORT)
        {line("DINORAH ESTÁ A SALVO.",11,12);line("A RETIRADA FOI CONCLUÍDA.",13,14);line("O GRUPO PODE SEGUIR.",15,2);}
        else if(LEVEL_current()->objective==OBJ_PROTECT)
        {line("SINAL PROTEGIDO.",11,12);sprintf(buf,"%u SEGUNDOS DE PROTEÇÃO.",LEVEL_current()->objTarget);line(buf,13,14);line("O RESGATE FOI CONFIRMADO.",15,2);}
        else
        {
            line("CAMINHO ABERTO.",11,12);
            if(LEVEL_current()->objective==OBJ_KILL)sprintf(buf,"%u INIMIGOS ELIMINADOS.",resultKills);
            else if(LEVEL_current()->objective==OBJ_SURVIVE)sprintf(buf,"%u SEGUNDOS SOBREVIVIDOS.",LEVEL_current()->objTarget);
            else sprintf(buf,"COLETA CONCLUÍDA.");
            line(buf,13,14);line("SIGA PARA O PRÓXIMO DESTINO.",15,2);
        }
        line("A/START: SEGUIR",20,15);
    }
    submit();
}
bool RESULT_defeat(u16 kills)
{LOADING_workBegin();resultKind=0;resultKills=kills;bool ok=begin();if(ok){draw();SFX_silence();MUSIC_playGameOver();}LOADING_workEnd();return ok;}
bool RESULT_complete(u16 kills,bool failed)
{LOADING_workBegin();resultKind=failed ? 2 : 1;resultKills=kills;bool ok=begin();if(ok){draw();if(failed)SFX_enemyShot();else {SFX_silence();MUSIC_playVictory();}}LOADING_workEnd();return ok;}
bool RESULT_victory(void)
{LOADING_workBegin();resultKind=3;bool ok=begin();if(ok){draw();SFX_silence();MUSIC_playVictory();}LOADING_workEnd();return ok;}
u8 RESULT_update(u16 joy,u16 pressed)
{
    if(age<fps)age++;
    if(!(joy&(BUTTON_A|BUTTON_START)))armed=TRUE;
    if(!resultActive)return (pressed&BUTTON_START) ? (resultKind==3 ? RESULT_TITLE : RESULT_RETRY) : RESULT_STAY;
    if(!armed || age<(fps*35+99)/100)return RESULT_STAY;
    if(resultKind==1 || resultKind==2)return (pressed&(BUTTON_A|BUTTON_START)) ? RESULT_RETRY : RESULT_STAY;
    if(exitView)
    {
        if(pressed&(BUTTON_B|BUTTON_START)){exitView=0;draw();}
        else if(pressed&(BUTTON_UP|BUTTON_DOWN)){exitChoice^=1;drawSelection();}
        else if(pressed&BUTTON_A){if(exitChoice)return RESULT_TITLE;exitView=0;draw();}
        return RESULT_STAY;
    }
    if(resultKind==0 && (pressed&BUTTON_START))return RESULT_RETRY;
    if(pressed&(BUTTON_UP|BUTTON_DOWN)){choice^=1;drawSelection();}
    else if((pressed&BUTTON_B) && resultKind==0 && choice){choice=0;drawSelection();}
    else if(pressed & (resultKind==3 ? (BUTTON_A|BUTTON_START) : BUTTON_A))
    {
        if(resultKind==3)return choice ? RESULT_REPLAY : RESULT_TITLE;
        if(!choice)return RESULT_RETRY;
        exitView=1;exitChoice=0;draw();
    }
    return RESULT_STAY;
}
void RESULT_close(void)
{
    MUSIC_stopResultCue();
    if(!resultActive)return;
    const bool enabled=VDP_getEnable();
    SPRITES_hide();SYS_doVBlankProcess();VDP_setEnable(FALSE);
    MEM_free(card);card=NULL;resultActive=FALSE;
    VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
    PAL_setColors(0,resultPalette,64,DMA);LOADING_tiles((const u32 *)text_font,TILE_FONT_INDEX,FONT_LENGTH,DMA);
    VDP_setWindowOff();VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
    VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
    VDP_setTextPlane(BG_A);VDP_setTextPriority(FALSE);
    // Fixed object tiles were never borrowed; rebuilding them here used to
    // extend the black loading gap on every completion.
    TILEGEN_palette();ENEMYGFX_reset();VDP_setEnable(enabled);
}
