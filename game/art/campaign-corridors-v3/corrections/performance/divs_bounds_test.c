/* Quantitative signed-division/range proof; not a68000cycle benchmark. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

static uint64_t samples[3];
static int32_t largest_numerator,largest_quotient,largest_divisor;

static int16_t divs_model(int32_t numerator,int16_t divisor)
{
    assert(divisor!=0);
    uint32_t a=numerator<0 ? (uint32_t)(-(int64_t)numerator) : (uint32_t)numerator;
    uint16_t b=divisor<0 ? (uint16_t)(-(int32_t)divisor) : (uint16_t)divisor;
    uint32_t magnitude=a/b;
    int64_t result=((numerator<0)!=(divisor<0)) ? -(int64_t)magnitude : magnitude;
    assert(result>=INT16_MIN && result<=INT16_MAX); /* DIVS overflow flag absent. */
    return (int16_t)result;
}
static void compare(int64_t wide,uint32_t denominator,unsigned family)
{
    assert(wide>=INT32_MIN && wide<=INT32_MAX);
    assert(denominator>0 && denominator<=INT16_MAX);
    int32_t numerator=(int32_t)wide;
    int32_t original=numerator/(int32_t)denominator;
    int16_t hardware=divs_model(numerator,(int16_t)denominator);
    assert(original==hardware);
    if(llabs(wide)>largest_numerator)largest_numerator=(int32_t)llabs(wide);
    if(abs(original)>largest_quotient)largest_quotient=abs(original);
    if((int32_t)denominator>largest_divisor)largest_divisor=denominator;
    samples[family]++;
}
/* Exact integer expression in SGDK/src/maths.c:getApproximatedDistance. */
static uint32_t approximate(int32_t dx,int32_t dy)
{
    uint32_t x=abs(dx),y=abs(dy),min=x<y?x:y,max=x>y?x:y;
    return ((max<<8)+(max<<3)-(max<<4)-(max<<1)+
            (min<<7)-(min<<5)+(min<<3)-(min<<1))>>8;
}
int main(void)
{
    /* Every ray vector admitted by the112pxguard, and every sample point. */
    for(int dx=-120;dx<=120;dx++)for(int dy=-120;dy<=120;dy++) {
        uint32_t dist=approximate(dx,dy);
        if(!dist || dist>112)continue;
        uint16_t steps=dist/8+1;
        for(uint16_t i=1;i<steps;i++) {
            compare((int32_t)dx*i,steps,0);compare((int32_t)dy*i,steps,0);
        }
    }
    for(unsigned region=0;region<2;region++) {
        unsigned fps=region?50:60,length=(fps*3/20)*4;
        int32_t stride=(36*64/fps)*length;
        /* Conservative complete36px interpolation envelope, each substep. */
        for(int delta=-36*64;delta<=36*64;delta++)for(unsigned step=1;step<=length;step++)
            compare((int64_t)delta*step,length,1);
        /* Every remaining waypoint vector within the3072x320authored world. */
        for(int dx=-3072;dx<=3072;dx++)for(int dy=-320;dy<=320;dy++) {
            uint32_t dist=approximate(dx,dy);
            if(dist<=1 || dist*64<=(uint32_t)stride)continue;
            compare((int64_t)dx*stride,dist,2);compare((int64_t)dy*stride,dist,2);
        }
    }
    printf("{\"passed\":true,\"method\":\"HostC original signed32division versus signed16DIVS arithmetic/range model; ASan/UBSan. Not execution of a68000instruction or timing proof.\",\"raySamples\":%llu,\"interpolationSamples\":%llu,\"waypointAxisSamples\":%llu,\"largestNumerator\":%d,\"largestQuotient\":%d,\"largestPositiveDivisor\":%d}\n",
           (unsigned long long)samples[0],(unsigned long long)samples[1],
           (unsigned long long)samples[2],largest_numerator,largest_quotient,largest_divisor);
    return 0;
}
