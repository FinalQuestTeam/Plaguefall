// Compile actual production loaders/renderer against a recording VDP/DMA.
#include <assert.h>
#include <stdio.h>
#include "system/video/enemygfx.c"
#include "system/video/spritelist.c"

const u32 insect_frames[13*50*192]={0};
const u32 insect_icons[15*128]={0};
const u32 heroi_frames[50*192]={0};
const u16 heroi_palette[16]={0};
Enemy enemies[MAX_ENEMIES];
static const EnemyDef def={.size=16,.speedFp=40};
static const EnemyDef bossDef={.size=48,.speedFp=32};
const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES]={
    &def,&def,&def,&def,&def,&def,&def,&def,&def,&def,&def,&def,&def,&def,&bossDef};
FShot pshots[MAX_PSHOTS],eshots[MAX_ESHOTS];
s16 px=150,py=100,faceX=1,faceY=0,npcX=150,npcY=100;
u16 fps=60;
static u16 queueBytes,queueCount,transfers,writes,peakSprites,peakPixels,peakLine;
static u8 recordedCount[224];
static u16 recordedPixels[224];
static bool failDMA;
static u16 heroTransfers;
u16 DMA_getQueueTransferSize(void){return queueBytes;}
u16 DMA_getQueueSize(void){return queueCount;}
u16 DMA_getMaxQueueSize(void){return 80;}
bool DMA_queueDma(u8 kind,void*src,u16 to,u16 words,u16 step)
{
    if(failDMA) return false;
    assert(kind==DMA_VRAM && words==384 && step==2);
    const uintptr_t address=(uintptr_t)src;
    if(address>=(uintptr_t)heroi_frames && address+768<=(uintptr_t)(heroi_frames+50*192))
    {
        assert(to==(TILE_USER_INDEX+CHARS_TILE_BASE)*32);
        heroTransfers++;assert(heroTransfers<=1);
    }
    else
    {
        assert(address>=(uintptr_t)insect_frames);
        assert(address+768<=(uintptr_t)(insect_frames+13*50*192));
        assert(to>=(TILE_USER_INDEX+ENEMY_ROT_BASE)*32);
        assert(to+words*2<=(TILE_USER_INDEX+ENEMY_ICON_BASE)*32);
        transfers++;assert(transfers<=4);
    }
    queueBytes+=words*2;queueCount++;
    assert(queueBytes+1024<=7200);
    return true;
}
void PAL_setColors(u16 i,const u16*d,u16 n,u8 m){assert(i+n<=64);}
void VDP_loadTileData(const u32*d,u16 t,u16 n,u8 mode){assert(d && t+n<1440);}
void VDP_setTileMapXY(u16 p,u16 a,u16 x,u16 y){}
void VDP_setSpriteFull(u16 i,s16 x,s16 y,u8 size,u16 attr,u8 link)
{
    assert(i<80 && link<=80);
    if(y< -32) return;
    const unsigned w=(((size>>2)&3)+1)*8,h=((size&3)+1)*8;
    for(int r=y<0?0:y;r<y+(int)h && r<224;r++)
    {
        recordedCount[r]++;recordedPixels[r]+=w;
        assert(recordedCount[r]<=20 && recordedPixels[r]<=320);
        if(recordedCount[r]>peakLine)peakLine=recordedCount[r];
        if(recordedPixels[r]>peakPixels)peakPixels=recordedPixels[r];
    }
    writes++;
}
void VDP_setSpriteLink(u16 i,u8 link){assert(i<80);}
void VDP_updateSprites(u16 n,u8 mode){assert(n<=80);if(n>peakSprites)peakSprites=n;}
bool PLAYER_hidden(void){return false;}
u16 CHARS_dirTile(u8 d){return CHARS_TILE_BASE;}
u8 CHARS_dirFlipH(u8 d){return 0;}
u8 CHARS_dirFlipV(u8 d){return 0;}
void CHAINFX_update(void){}
bool NPC_active(void){return true;}
bool NPC_hidden(void){return false;}
u16 ITEMS_draw(u16 n)
{
    for(int i=0;i<8;i++)SPRITES_emit(&n,i*32,100,SPRITE_SIZE(2,2),0);
    return n;
}
u16 CHAINFX_draw(u16 n)
{
    for(int i=0;i<24;i++)SPRITES_emit(&n,i*12,110,SPRITE_SIZE(1,1),0);
    return n;
}
static void resetRecording(void)
{
    memset(recordedCount,0,sizeof recordedCount);
    memset(recordedPixels,0,sizeof recordedPixels);
    queueBytes=queueCount=transfers=writes=heroTransfers=0;
}
int main(void)
{
    HERO_load();
    ENEMYGFX_reset();
    for(int i=0;i<16;i++){enemies[i].active=true;enemies[i].type=i==15?14:i%12;enemies[i].x=i*18;enemies[i].y=100;}
    for(int f=0;f<4;f++){resetRecording();ENEMYGFX_prepare(f);assert(transfers==4);}
    for(int i=0;i<16;i++)assert(ENEMYGFX_ready(i));
    for(int f=4;f<604;f++)
    {
        resetRecording();
        px=150+(f%6);py=100+(f%6);faceX=(f/60)%3-1;faceY=(f/180)%3-1;
        for(int i=0;i<16;i++)
        {
            enemies[i].x=8+(f+i*19)%280;
            enemies[i].y=40+(f/5+i*7)%160;
            enemies[i].vx=(f&1)?32:-32;enemies[i].vy=(i&1)?32:-32;
            enemies[i].frozen=(f%17==0);enemies[i].burnFlash=(f%11==0);
            enemies[i].shielded=(f%7==0);
        }
        for(int i=0;i<16;i++)
        {
            pshots[i].active=eshots[i].active=true;
            pshots[i].x=eshots[i].x=(i*19)<<6;
            pshots[i].y=eshots[i].y=100<<6;
        }
        SPRITES_draw();
    }
    // Failed DMA must not expose old graphics as a newly spawned type.
    enemies[0].type=7;slots[0].valid=false;failDMA=true;
    resetRecording();ENEMYGFX_prepare(605);assert(!ENEMYGFX_ready(0));failDMA=false;
    // Global 80-sprite limit independent of scanline pressure.
    memset(lineSprites,0,sizeof lineSprites);memset(linePixels,0,sizeof linePixels);
    resetRecording();u16 n=0;
    for(int i=0;i<80;i++)assert(SPRITES_emit(&n,(i%10)*24,(i/10)*24,SPRITE_SIZE(1,1),0));
    assert(!SPRITES_emit(&n,300,200,SPRITE_SIZE(1,1),0) && n==80);
    // Pixel and count limits independently.
    memset(lineSprites,0,sizeof lineSprites);memset(linePixels,0,sizeof linePixels);resetRecording();n=0;
    for(int i=0;i<10;i++)assert(SPRITES_emit(&n,i*30,80,SPRITE_SIZE(4,1),0));
    assert(!SPRITES_emit(&n,0,80,SPRITE_SIZE(1,1),0));
    memset(lineSprites,0,sizeof lineSprites);memset(linePixels,0,sizeof linePixels);resetRecording();n=0;
    for(int i=0;i<20;i++)assert(SPRITES_emit(&n,i*8,80,SPRITE_SIZE(1,1),0));
    assert(!SPRITES_emit(&n,170,80,SPRITE_SIZE(1,1),0));
    printf("{\"frames_stressed\":600,\"peak_runtime_sat\":%u,\"peak_scanline_sprites\":%u,\"peak_scanline_pixels\":%u,\"global_and_dma_failure_tests\":true}\n",peakSprites,peakLine,peakPixels);
    return 0;
}
