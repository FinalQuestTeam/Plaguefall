/* Native arithmetic/range proof, not68000execution or timing. */
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static unsigned long long normal,ally,fallback;
static int maxNum,maxDen,maxQuot,maxAllyDen,maxAllyQuot;
static unsigned approx(int dx,int dy){unsigned x=abs(dx),y=abs(dy),min=x<y?x:y,max=x>y?x:y;return ((max<<8)+(max<<3)-(max<<4)-(max<<1)+(min<<7)-(min<<5)+(min<<3)-(min<<1))>>8;}
static int16_t hardware(int32_t num,unsigned den){assert(den>0 && den<=32767);int q=num/(int)den;assert(q>=INT16_MIN && q<=INT16_MAX);if(abs(num)>maxNum)maxNum=abs(num);if((int)den>maxDen)maxDen=den;if(abs(q)>maxQuot)maxQuot=abs(q);return q;}
static void axis(int delta,unsigned dist,unsigned speed){int32_t n=(int32_t)delta*speed;int old=n/(int)dist;int now=dist<=32767?hardware(n,dist):n/(int)dist;assert(old==now);normal++;fallback+=dist>32767;}
int main(void){
    for(int dx=-3104;dx<=3104;dx++)for(int dy=-384;dy<=384;dy++){
        unsigned dist=approx(dx,dy);if(!dist)dist=1;
        axis(dx,dist,128);axis(dy,dist,128);axis(dx,dist,200);axis(dy,dist,200);
    }
    const int extremes[]={-32767,-32766,-3072,-2,-1,0,1,2,3072,32766,32767};
    for(unsigned i=0;i<11;i++)for(unsigned j=0;j<11;j++){
        int dx=extremes[i],dy=extremes[j];unsigned dist=approx(dx,dy);if(!dist)dist=1;
        axis(dx,dist,128);axis(dy,dist,128);axis(dx,dist,200);axis(dy,dist,200);
    }
    const int anchors[5][2]={{17,11},{29,23},{30,27},{26,43},{21,45}};
    const int canon[8]={0,1,2,3,4,3,2,1},mirror[8]={0,0,0,0,0,1,1,1};
    for(int dx=-120;dx<=120;dx++)for(int dy=-120;dy<=120;dy++){
        if(approx(dx,dy)>112)continue;
        for(unsigned dir=0;dir<8;dir++){
            const int *anchor=anchors[canon[dir]];
            int mx=-16+(mirror[dir]?32-anchor[0]:anchor[0]),my=anchor[1]-23;
            int ax=dx-mx,ay=dy-my;unsigned dist=approx(ax,ay);if(!dist)dist=1;
            for(unsigned region=0;region<2;region++){
                unsigned fps=region?50:60,den=fps*dist;assert(den>0 && den<=32767);
                if((int)den>maxAllyDen)maxAllyDen=den;
                const int deltas[2]={ax,ay};
                for(unsigned axis=0;axis<2;axis++){
                    int64_t wide=(int64_t)deltas[axis]*180*64;assert(wide>=INT32_MIN && wide<=INT32_MAX);
                    int old=((int32_t)wide/(int)fps)/(int)dist;
                    int now=hardware((int32_t)wide,den);assert(old==now);
                    if(abs(now)>maxAllyQuot)maxAllyQuot=abs(now);ally++;
                }
            }
        }
    }
    printf("{\"passed\":true,\"enemyAxisComparisons\":%llu,\"allyAxisComparisons\":%llu,\"fallbackComparisons\":%llu,\"largestNumerator\":%d,\"largestHardwareDivisor\":%d,\"largestHardwareQuotient\":%d,\"largestAllyDivisor\":%d,\"largestAllyQuotient\":%d,\"fps\":[50,60],\"SGDKDistanceExact\":true,\"all8MuzzleFacings\":true,\"nestedTruncationExact\":true}\n",normal,ally,fallback,maxNum,maxDen,maxQuot,maxAllyDen,maxAllyQuot);
}
