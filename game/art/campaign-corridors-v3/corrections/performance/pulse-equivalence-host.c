#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint16_t u16;typedef uint32_t u32;
static u32 vtimer;static u16 fps;
static u32 pulseTimer=0xffffffffUL;
static u16 pulseRate,pulseOffset,pulsePhase;
static u16 pulse(void)
{
    const u32 now=vtimer;
    if(now!=pulseTimer || fps!=pulseRate) {
        const u16 half=fps/2,period=half*2;
        // Preserve the exact absolute-vtimer animation. Normal consecutive
        // frames advance its remainder without a software32-bit divide.
        if(fps==pulseRate && now>=pulseTimer && now-pulseTimer<period) {
            pulsePhase+=(u16)(now-pulseTimer);
            if(pulsePhase>=period)pulsePhase-=period;
        } else pulsePhase=now%period;
        pulseOffset=pulsePhase>=half ? 4 : 0;pulseTimer=now;pulseRate=fps;
    }
    return pulseOffset;
}

static unsigned long long calls=0;
static void check(u32 now,u16 rate) {
    vtimer=now;fps=rate;
    const u16 expected=((now/(rate/2))&1)*4;
    const u16 actual=pulse();calls++;
    if(actual!=expected){fprintf(stderr,"mismatch now=%u fps=%u expected=%u got=%u\n",now,rate,expected,actual);exit(1);}
}
static u32 random_state=0xa6b7291c;
static u32 random32(void){random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;return random_state;}
int main(void) {
    const u16 rates[2]={50,60};
    for(u16 region=0;region<2;region++) {
        u16 rate=rates[region];
        for(u32 now=0;now<1000000;now++){check(now,rate);check(now,rate);}
        for(u32 base=0;base<4096;base++)for(u32 step=1;step<=60;step++) {
            check(base,rate);check(base+step,rate);check(base+step,rate);
        }
        for(u32 offset=0;offset<256;offset++) {
            u32 now=UINT32_MAX-offset;check(now,rate);
            for(u16 step=0;step<180;step++)check(++now,rate);
        }
        for(u32 i=0;i<1000000;i++)check(random32(),rate);
    }
    for(u32 i=0;i<1000000;i++)check(random32(),rates[i&1]);
    printf("{\"passed\":true,\"calls\":%llu}\n",calls);
    return 0;
}
