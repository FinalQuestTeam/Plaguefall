
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef int16_t s16;typedef uint16_t u16;typedef uint8_t u8;typedef int32_t s32;
#define TRUE true
#define FALSE false
typedef struct {int x,y,w,h;} Rect;
static s16 dinorahX,dinorahY;static u8 currentLevel=8,gateMask;
static unsigned long long uncachedCalls,comparisons,hits,invalidationChecks;
static u8 CR_OPS_gateBlockMask(void){return gateMask;}
static u16 getApproximatedDistance(s16 dx,s16 dy){unsigned x=abs(dx),y=abs(dy),min=x<y?x:y,max=x>y?x:y;return ((max<<8)+(max<<3)-(max<<4)-(max<<1)+(min<<7)-(min<<5)+(min<<3)-(min<<1))>>8;}
static s16 divs(s32 n,s16 d){return n/d;}
static const Rect solids[]={{112,32,56,80},{80,72,144,32},{72,104,8,80},{224,104,8,80},{80,184,144,32},{1472,144,8,96},{1608,144,8,96},{1480,112,128,32},{1480,240,128,32},{1496,136,96,80},{2480,104,56,80},{2496,200,24,32},{2848,112,160,32},{2896,80,32,32},{2848,72,48,48},{2928,48,64,80},{984,24,32,112},{952,168,32,152},{808,64,96,80},{904,104,32,32},{2104,24,32,192},{2072,248,32,72},{1928,144,96,80},{2024,184,32,32}};
static const Rect gates[]={{960,112,32,64},{2080,192,32,64}};

static bool hit(Rect r,int x,int y){return x<r.x+r.w && x+8>r.x && y<r.y+r.h && y+8>r.y;}
static bool ARENA_shotBlocked(s16 x,s16 y){
    y-=16;
    if(x<24 || x>3040 || y<64 || y>264)return true;
    for(unsigned i=0;i<sizeof(solids)/sizeof(*solids);i++)if(hit(solids[i],x,y))return true;
    for(unsigned i=0;i<2;i++)if((gateMask&(1<<i)) && hit(gates[i],x,y))return true;
    return false;
}
typedef struct {s16 x,y,tx,ty;u8 gates;bool clear;} SightRay;
static SightRay sightRays[4];
static u8 sightCount,sightNext;
static bool uncachedClearShot(s16 tx,s16 ty)
{
    uncachedCalls++;
    s16 dx=tx-(dinorahX+8),dy=ty-(dinorahY+8);
    u16 dist=getApproximatedDistance(dx,dy),steps=dist/8+1;
    // Reproduce trunc(dx*i/steps) and trunc(dy*i/steps) exactly with
    // quotient/remainder accumulation. Two DIVS per ray replace two per
    // sample; the original collision points and their order stay identical.
    const s16 qx=divs(dx,steps),qy=divs(dy,steps);
    const u16 rx=abs(dx-qx*steps),ry=abs(dy-qy*steps);
    const s16 sx=dx<0 ? -1 : 1,sy=dy<0 ? -1 : 1;
    s16 x=dinorahX+4,y=dinorahY+4;
    u16 errorX=0,errorY=0;
    // Read-only probes must never damage destructible doors.
    for(u16 i=1;i<steps;i++) {
        x+=qx;y+=qy;errorX+=rx;errorY+=ry;
        if(errorX>=steps){errorX-=steps;x+=sx;}
        if(errorY>=steps){errorY-=steps;y+=sy;}
        if(ARENA_shotBlocked(x,y))return FALSE;
    }
    return TRUE;
}
static bool clearShot(s16 tx,s16 ty)
{
    if(!currentLevel)return uncachedClearShot(tx,ty);
    const u8 gates=CR_OPS_gateBlockMask();
    for(u8 i=0;i<sightCount;i++) {
        const SightRay *r=&sightRays[i];
        if(r->x==dinorahX && r->y==dinorahY && r->tx==tx && r->ty==ty && r->gates==gates)return r->clear;
    }
    const bool clear=uncachedClearShot(tx,ty);
    sightRays[sightNext]=(SightRay){dinorahX,dinorahY,tx,ty,gates,clear};
    sightNext=(sightNext+1)&3;if(sightCount<4)sightCount++;
    return clear;
}

static void reset(void){sightCount=sightNext=0;}
static void compare(s16 tx,s16 ty){
    unsigned long long before=uncachedCalls;
    bool a=clearShot(tx,ty);hits+=uncachedCalls==before;
    bool b=uncachedClearShot(tx,ty);assert(a==b);comparisons++;
}
static void must_miss(s16 tx,s16 ty){unsigned long long n=uncachedCalls;clearShot(tx,ty);assert(uncachedCalls==n+1);invalidationChecks++;}

int main(void){
    dinorahX=912;dinorahY=144;gateMask=3;
    for(unsigned field=0;field<5;field++){
        reset();dinorahX=912;dinorahY=144;gateMask=3;must_miss(1008,152);
        unsigned long long n=uncachedCalls;clearShot(1008,152);assert(uncachedCalls==n);invalidationChecks++;
        if(field==0)dinorahX++;if(field==1)dinorahY++;if(field==4)gateMask^=1;
        must_miss(1008+(field==2),152+(field==3));
    }
    reset();must_miss(1008,152);reset();must_miss(1008,152);
    /* All masks represent closed/collapsing(open=false) or fully hidden
       gates. Reusing a mask after returning to it is also exact. */
    for(unsigned repeat=0;repeat<1000;repeat++)for(gateMask=0;gateMask<4;gateMask++){
        compare(1008,152);compare(1008,152);compare(2128,232);
    }
    currentLevel=0;for(unsigned i=0;i<20;i++)must_miss(1008,152);currentLevel=8;
    unsigned random=0xa081b375;
    for(unsigned i=0;i<1000000;i++){
        random^=random<<13;random^=random>>17;random^=random<<5;
        if((i&31)==0)reset();
        if(i%5==0){dinorahX=24+(random%2980);dinorahY=80+((random>>12)%170);gateMask=(random>>24)&3;}
        s16 tx=dinorahX+8+(int)((random>>4)%201)-100;
        s16 ty=dinorahY+8+(int)((random>>16)%161)-80;
        compare(tx,ty);compare(tx,ty);
        assert(sightCount<=4 && sightNext<4);
    }
    printf("{\"passed\":true,\"cachedVsUncachedComparisons\":%llu,\"exactCacheHits\":%llu,\"explicitInvalidationAssertions\":%llu,\"originAndTargetXYInvalidated\":true,\"all4GateMasks\":true,\"restartReset\":true,\"trainingUncached\":true}\n",comparisons,hits,invalidationChecks);
}
