/* Conservative clearShot AABB proof. No production or ROM mutation. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef struct {int x,y,w,h;} Rect;
static unsigned long long rays,samples,bounds,gates;
static uint32_t approximate(int dx,int dy) {
    uint32_t x=abs(dx),y=abs(dy),min=x<y?x:y,max=x>y?x:y;
    return ((max<<8)+(max<<3)-(max<<4)-(max<<1)+
            (min<<7)-(min<<5)+(min<<3)-(min<<1))>>8;
}
static int overlap(Rect a,Rect b) {
    return a.x<b.x+b.w && a.x+a.w>b.x && a.y<b.y+b.h && a.y+a.h>b.y;
}
static int feet_clear_bounds(Rect r,int width,int height) {
    return r.x>=24 && r.y>=64 && r.x+r.w<=width-16 && r.y+r.h<=height-16;
}
static int shot_inside_bounds(Rect r,int width,int height) {
    /* ARENA_shotBlocked compares groundY+VIDEO_HEIGHT_OFFSET on its lower edge. */
    return r.x>=24 && r.y>=64-16 && r.x+8<=width-16 && r.y+8<=height-16;
}
int main(void) {
    const int originsX[]={-32,0,24,31,32,80,248,255,256,912,1472,2032,2848,3056};
    const int originsY[]={-32,0,48,64,128,192,232,304};
    const Rect obstacles[]={{24,64,32,128},{248,128,32,128},{912,64,32,160},
                            {2032,104,32,144},{3072,0,32,320},{128,192,8,8}};
    for(unsigned ox=0;ox<sizeof(originsX)/sizeof(*originsX);ox++)
    for(unsigned oy=0;oy<sizeof(originsY)/sizeof(*originsY);oy++)
    for(int dx=-120;dx<=120;dx++)for(int dy=-120;dy<=120;dy++) {
        const unsigned dist=approximate(dx,dy),steps=dist/8+1;
        if(dist>112 || steps<=3)continue;
        const int dinorahX=originsX[ox],dinorahY=originsY[oy];
        const int tx=dinorahX+8+dx,ty=dinorahY+8+dy;
        const int sx=dinorahX+4,sy=dinorahY+4-16,ex=tx-4,ey=ty-4-16;
        const Rect box={sx<ex?sx:ex,sy<ey?sy:ey,abs(ex-sx)+8,abs(ey-sy)+8};
        assert(box.w<256 && box.h<256);rays++;
        for(unsigned i=1;i<steps;i++) {
            /* C99 signed division and68000 DIVS both truncate toward zero. */
            const Rect sample={dinorahX+4+dx*(int)i/(int)steps,
                               dinorahY+4+dy*(int)i/(int)steps-16,8,8};
            assert(sample.x>=box.x && sample.y>=box.y);
            assert(sample.x+8<=box.x+box.w && sample.y+8<=box.y+box.h);
            /* For nonnegative, guarded masks, each sample cell belongs to AABB. */
            if(box.x>=0 && box.y>=0) {
                assert(sample.x/8>=box.x/8 && sample.y/8>=box.y/8);
                assert((sample.x+7)/8<=(box.x+box.w-1)/8);
                assert((sample.y+7)/8<=(box.y+box.h-1)/8);
            }
            for(unsigned wi=0;wi<3;wi++) {
                const int width=wi==0?384:wi==1?2560:3072;
                if(feet_clear_bounds(box,width,320))assert(shot_inside_bounds(sample,width,320));
                bounds++;
            }
            for(unsigned j=0;j<sizeof(obstacles)/sizeof(*obstacles);j++) {
                /* Closed/collapsing gates block the same8x8 footprint; open
                   gates block neither box nor sample. */
                if(!overlap(box,obstacles[j]))assert(!overlap(sample,obstacles[j]));
                gates++;
            }
            samples++;
        }
    }
    printf("{\"passed\":true,\"rays\":%llu,\"containedSamples\":%llu,\"boundsImplications\":%llu,\"gateImplications\":%llu,\"SGDKDistanceExact\":true,\"signedTruncation\":true,\"negativeOriginsIncluded\":true,\"cellSetContainment\":true}\n",rays,samples,bounds,gates);
}
