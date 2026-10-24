
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef int16_t s16;typedef uint16_t u16;typedef int32_t s32;
#define TRUE true
#define FALSE false
static s16 dinorahX,dinorahY;
static int testDX,testDY,testSteps,blockedAt,calls;
static unsigned long long checkedSamples,queries;
static u16 getApproximatedDistance(s16 dx,s16 dy) {
    unsigned x=abs(dx),y=abs(dy),min=x<y?x:y,max=x>y?x:y;
    return ((max<<8)+(max<<3)-(max<<4)-(max<<1)+(min<<7)-(min<<5)+(min<<3)-(min<<1))>>8;
}
static s16 divs(s32 n,s16 d){assert(d>0);return n/d;}
static bool ARENA_shotBlocked(s16 x,s16 y) {
    const int i=calls+1;
    assert(x==dinorahX+4+testDX*i/testSteps);
    assert(y==dinorahY+4+testDY*i/testSteps);
    checkedSamples++;return calls++==blockedAt;
}
static bool clearShot(s16 tx,s16 ty)
{
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

int main(void) {
    const s16 origins[][2]={{0,0},{-32,-32},{40,200},{3056,304}};
    for(unsigned origin=0;origin<4;origin++) {
        dinorahX=origins[origin][0];dinorahY=origins[origin][1];
        for(testDX=-120;testDX<=120;testDX++)for(testDY=-120;testDY<=120;testDY++) {
            u16 dist=getApproximatedDistance(testDX,testDY);if(dist>112)continue;
            testSteps=dist/8+1;
            for(blockedAt=-1;blockedAt<testSteps-1;blockedAt++) {
                calls=0;const bool actual=clearShot(dinorahX+8+testDX,dinorahY+8+testDY);
                assert(actual==(blockedAt<0));
                assert(calls==(blockedAt<0?testSteps-1:blockedAt+1));queries++;
            }
        }
    }
    printf("{\"passed\":true,\"queries\":%llu,\"orderedSamples\":%llu,\"everyFirstObstruction\":true,\"signedTruncationExact\":true,\"SGDKDistanceExact\":true}\n",queries,checkedSamples);
}
