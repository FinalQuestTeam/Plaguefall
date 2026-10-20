// Compile actual production loaders/renderer against a recording VDP/DMA.
#include <assert.h>
#include <stdio.h>
#include "system/video/enemygfx.c"
#include "system/video/spritelist.c"

const u32 insect_frames[ENEMY_ASSET_LONGWORDS]={0};
const u32 insect_icons[15*128]={0};
const u32 heroi_frames[5*ACTOR_VIEW_FRAMES*192]={0};
const u16 heroi_palette[16]={0};
Enemy enemies[MAX_ENEMIES];
static const EnemyDef def={.size=16,.speedFp=40};
static const EnemyDef def24={.size=24,.speedFp=40};
static const EnemyDef def32={.size=32,.speedFp=40};
static const EnemyDef bossDef={.size=48,.speedFp=32};
const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES]={
    &def,&def,&def32,&def,&def,&def,&def,&def,&def24,&def24,&def32,&def24,&def24,&def24,&bossDef};
FShot pshots[MAX_PSHOTS],eshots[MAX_ESHOTS];
s16 px=150,py=100,faceX=1,faceY=0,npcX=150,npcY=100;
u16 fps=60;
static u16 queueBytes,queueCount,transfers,writes,peakSprites,peakPixels,peakLine;
static u8 recordedCount[224];
static u16 recordedAttr[80];
static s16 recordedX[80],recordedY[80];
static u16 recordedPixels[224];
static bool failDMA;
static u16 heroTransfers;
static u16 queuedStart[8],queuedEnd[8],queuedRanges;
u16 DMA_getQueueTransferSize(void){return queueBytes;}
u16 DMA_getQueueSize(void){return queueCount;}
u16 DMA_getMaxQueueSize(void){return 80;}
bool DMA_queueDma(u8 kind,void*src,u16 to,u16 words,u16 step)
{
    if(failDMA) return false;
    assert(kind==DMA_VRAM && step==2);
    const uintptr_t address=(uintptr_t)src;
    if(address>=(uintptr_t)heroi_frames && address+768<=(uintptr_t)(heroi_frames+5*ACTOR_VIEW_FRAMES*192))
    {
        assert(to==(TILE_USER_INDEX+CHARS_TILE_BASE)*32);
        heroTransfers++;assert(heroTransfers<=1);
    }
    else
    {
        assert(address>=(uintptr_t)insect_frames);
        assert(address+words*2<=(uintptr_t)(insect_frames+ENEMY_ASSET_LONGWORDS));
        assert(to>=(TILE_USER_INDEX+ENEMY_ROT_BASE)*32);
        assert(to+words*2<=(TILE_USER_INDEX+ENEMY_ICON_BASE)*32);
        transfers++;assert(transfers<=4);
    }
    for(u16 i=0;i<queuedRanges;i++)assert(to>=queuedEnd[i] || to+words*2<=queuedStart[i]);
    assert(queuedRanges<8);queuedStart[queuedRanges]=to;queuedEnd[queuedRanges++]=to+words*2;
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
    recordedAttr[i]=attr;recordedX[i]=x;recordedY[i]=y;
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
    queueBytes=queueCount=transfers=writes=heroTransfers=queuedRanges=0;
}
static void checkPackedScanlines(void)
{
    unsigned seed=12345;
    for(int epoch=0;epoch<64;epoch++)
    {
        unsigned referenceCount[224]={0},referencePixels[224]={0};
        memset(lineSprites,0,sizeof lineSprites);memset(linePixels,0,sizeof linePixels);
        usedSpriteBits=usedPixelBits=0;
        resetRecording();u16 n=0;
        for(int attempt=0;attempt<128;attempt++)
        {
            seed=seed*1664525u+1013904223u;
            int x=(int)((seed>>16)%376)-32,y=(int)((seed>>8)%280)-32;
            u8 size=((seed>>3)&3)*4+((seed>>5)&3);
            unsigned w=(((size>>2)&3)+1)*8,h=((size&3)+1)*8;
            bool expected=n<80 && x<320 && x+(int)w>0 && y<224 && y+(int)h>0;
            for(int row=y<0?0:y;row<y+(int)h && row<224 && expected;row++)
                if(referenceCount[row]>=20 || referencePixels[row]+w>320)expected=false;
            unsigned before=n;
            assert(SPRITES_emit(&n,x,y,size,0)==expected);
            assert(n==before+(expected?1:0));
            if(expected)for(int row=y<0?0:y;row<y+(int)h && row<224;row++)
            {referenceCount[row]++;referencePixels[row]+=w;}
        }
    }
    // A blocked lower piece must not reserve rows or emit a partial actor.
    memset(lineSprites,0,sizeof lineSprites);memset(linePixels,0,sizeof linePixels);
    resetRecording();u16 n=0;
    for(int i=0;i<10;i++)assert(SPRITES_emit(&n,i*30,32,SPRITE_SIZE(4,1),0));
    unsigned before=writes;
    assert(!emitActor(&n,0,0,0) && n==10 && writes==before);
    for(int i=0;i<10;i++)assert(SPRITES_emit(&n,i*30,0,SPRITE_SIZE(4,4),0));
}

static void checkDeferredScanlines(void)
{
    // Exhaust the complete encoded-load domain, including byte carries at >255.
    for(unsigned count=0;count<=80;count++)for(unsigned width=0;width<=count*4;width++)
    {
        u16 load=(count<<8)+width;
        assert((((u16)(load+0x6b57u)&0x8080u)!=0) == (count>20 || width>40));
    }
    unsigned seed=918273;
    for(int epoch=0;epoch<128;epoch++)
    {
        beginSprites();resetRecording();u16 n=0;
        for(int attempt=0;attempt<128;attempt++)
        {
            seed=seed*1664525u+1013904223u;
            int x=(int)((seed>>16)%376)-32,y=(int)((seed>>8)%280)-40;
            if(attempt%7==0)emitBoss(&n,x,y,(attempt*32)&~(1u<<11));
            else if(attempt%3==0)emitActor(&n,x,y,attempt*32);
            else SPRITES_emit(&n,x,y,((seed>>3)&3)*4+((seed>>5)&3),attempt*32);
        }
        unsigned counts[224]={0},pixels[224]={0},expectedN=0;
        u16 attrs[80];
        // Independent row-by-row reference, retaining each actor atomically.
        for(unsigned i=0;i<n;)
        {
            PendingSprite p=pending[i];i+=p.pieces;
            unsigned w=p.pieces==4?48:(((p.size>>2)&3)+1)*8,h=p.pieces>=2?48:((p.size&3)+1)*8;
            unsigned rowCount=p.pieces==4?2:1;
            bool accept=expectedN+p.pieces<=80;
            for(int y=p.y<0?0:p.y;y<p.y+(int)h && y<224;y++)
                if(counts[y]+rowCount>20 || pixels[y]+w>320)accept=false;
            if(!accept)continue;
            for(int y=p.y<0?0:p.y;y<p.y+(int)h && y<224;y++){counts[y]+=rowCount;pixels[y]+=w;}
            attrs[expectedN++]=p.attr;
            if(p.pieces>=2)attrs[expectedN++]=p.attr+16;
            if(p.pieces==4){attrs[expectedN++]=p.attr+24;attrs[expectedN++]=p.attr+32;}
        }
        assert(finishSprites(n)==expectedN && writes==expectedN);
        for(unsigned i=0;i<expectedN;i++)assert(recordedAttr[i]==attrs[i]);
        for(int y=0;y<224;y++)assert(recordedCount[y]==counts[y] && recordedPixels[y]==pixels[y]);
    }
}

static void checkHorizontalReuse(void)
{
    memset(enemies,0,sizeof enemies);ENEMYGFX_reset();
    px=150;py=100;enemies[0].active=true;enemies[0].type=0;
    enemies[0].x=100;enemies[0].y=100;
    resetRecording();ENEMYGFX_prepare(0);
    assert(transfers==1 && ENEMYGFX_ready(0) && !ENEMYGFX_entityFlipH(0));
    u16 tile=ENEMYGFX_entityTile(0);
    px=50;resetRecording();ENEMYGFX_prepare(0);
    assert(transfers==0 && ENEMYGFX_ready(0) && ENEMYGFX_entityFlipH(0));
    assert(ENEMYGFX_entityTile(0)==tile);
    HERO_load();resetRecording();HERO_prepare(6);
    assert(heroTransfers==0 && HERO_flipH());
    HERO_prepare(2);assert(heroTransfers==0 && !HERO_flipH());
    px=150;py=100;
}

static void checkCachePool(void)
{
    for(u16 i=0;i<MAX_ENEMIES;i++)
    {
        FrameSlot *s=&slots[i];
        if(!s->blocks)continue;
        assert(s->block+s->blocks<=CACHE_BLOCKS);
        assert(s->tile==ENEMY_ROT_BASE+s->block*CACHE_BLOCK_TILES);
        for(u16 b=s->block;b<s->block+s->blocks;b++)assert(blockOwner[b]==i);
        for(u16 j=0;j<i;j++)if(slots[j].blocks)
            assert(s->block>=slots[j].block+slots[j].blocks || slots[j].block>=s->block+s->blocks);
    }
}
static void checkNativeProjection(void)
{
    memset(enemies,0,sizeof enemies);ENEMYGFX_reset();
    for(u16 type=0;type<ENEMY_TYPES;type++)
    {
        enemies[0].active=true;enemies[0].type=type;enemies[0].x=100;enemies[0].y=80;
        resetRecording();SPRITES_draw();
        u16 tile=TILE_USER_INDEX+(type==12 || type==13 ? iconTile(type) : ENEMYGFX_entityTile(0));
        bool found=false;
        for(u16 i=0;i<writes;i++)if((recordedAttr[i]&2047)==tile)
        {assert(recordedX[i]==100 && recordedY[i]==VIDEO_PROJECT_Y(80));found=true;}
        assert(found);checkCachePool();
    }
}

int main(void)
{
    checkPackedScanlines();
    checkDeferredScanlines();
    checkHorizontalReuse();
    for(int flip=0;flip<2;flip++)
    {
        beginSprites();resetRecording();u16 n=0;
        assert(emitBoss(&n,16,40,flip<<11));assert(finishSprites(n)==4);
        assert(recordedX[0]==(flip?32:16) && recordedX[2]==(flip?16:48));
    }
    HERO_load();
    checkNativeProjection();
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
        checkCachePool();
    }
    // Churn and overcommit exercise free/reuse/eviction and queued-DMA pins.
    for(int epoch=0;epoch<1024;epoch++)
    {
        for(int i=0;i<16;i++)
        {enemies[i].active=(epoch+i)%7!=0;enemies[i].type=(epoch*5+i*3)%15;}
        resetRecording();ENEMYGFX_prepare(epoch+604);checkCachePool();
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
    printf("{\"native_projection_all_types\":true,\"cache_churn_frames\":1024,\"boss_composite_mirror\":true,\"horizontal_mirror_without_DMA\":true,\"deferred_random_frames\":128,\"frames_stressed\":600,\"peak_runtime_sat\":%u,\"peak_scanline_sprites\":%u,\"peak_scanline_pixels\":%u,\"global_and_dma_failure_tests\":true}\n",peakSprites,peakLine,peakPixels);
    return 0;
}
