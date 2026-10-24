#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint16_t u16;typedef int16_t s16;typedef uint32_t u32;
#define TRUE true
#define FALSE false
static u16 collisionStride;
static const u32 occupiedLeft[32]={0xffffffffUL,0x7fffffffUL,0x3fffffffUL,0x1fffffffUL,0x0fffffffUL,0x07ffffffUL,0x03ffffffUL,0x01ffffffUL,0x00ffffffUL,0x007fffffUL,0x003fffffUL,0x001fffffUL,0x000fffffUL,0x0007ffffUL,0x0003ffffUL,0x0001ffffUL,0x0000ffffUL,0x00007fffUL,0x00003fffUL,0x00001fffUL,0x00000fffUL,0x000007ffUL,0x000003ffUL,0x000001ffUL,0x000000ffUL,0x0000007fUL,0x0000003fUL,0x0000001fUL,0x0000000fUL,0x00000007UL,0x00000003UL,0x00000001UL};
static const u32 occupiedRight[32]={0x80000000UL,0xc0000000UL,0xe0000000UL,0xf0000000UL,0xf8000000UL,0xfc000000UL,0xfe000000UL,0xff000000UL,0xff800000UL,0xffc00000UL,0xffe00000UL,0xfff00000UL,0xfff80000UL,0xfffc0000UL,0xfffe0000UL,0xffff0000UL,0xffff8000UL,0xffffc000UL,0xffffe000UL,0xfffff000UL,0xfffff800UL,0xfffffc00UL,0xfffffe00UL,0xffffff00UL,0xffffff80UL,0xffffffc0UL,0xffffffe0UL,0xfffffff0UL,0xfffffff8UL,0xfffffffcUL,0xfffffffeUL,0xffffffffUL};
static bool occupied(const u32 *rows,s16 x,s16 y,u16 w,u16 h)
{
    const u16 left=x>>3,right=(x+w-1)>>3,first=left>>5,last=right>>5;
    u32 a=occupiedLeft[left&31];const u32 b=occupiedRight[right&31];
    const u16 count=((y+h-1)>>3)-(y>>3)+1;
    const u32 *line=rows+(y>>3)*collisionStride+first;
    if(first==last) {
        a&=b;
        for(u16 row=0;row<count;row++,line+=collisionStride)if(*line&a)return TRUE;
    } else {
        const u16 delta=last-first;
        for(u16 row=0;row<count;row++,line+=collisionStride)if((*line&a) || (line[delta]&b))return TRUE;
    }
    return FALSE;
}

static bool original(const u32 *rows,s16 x,s16 y,u16 w,u16 h) {
    const u16 left=x>>3,right=(x+w-1)>>3,first=left>>5,last=right>>5;
    const u32 a=0xffffffffUL>>(left&31),b=0xffffffffUL<<(31-(right&31));
    for(u16 row=y>>3;row<=((y+h-1)>>3);row++) {
        const u32 *line=rows+row*collisionStride;
        if(first==last) {if(line[first]&(a&b))return true;}
        else if((line[first]&a)||(line[last]&b))return true;
    }
    return false;
}
static bool cells(const u32 *rows,s16 x,s16 y,u16 w,u16 h) {
    for(u16 row=y/8;row<=(y+h-1)/8;row++)
        for(u16 col=x/8;col<=(x+w-1)/8;col++)
            if(rows[row*collisionStride+col/32]&(UINT32_C(0x80000000)>>(col%32)))return true;
    return false;
}
static u32 rng=0x5107ab39;
static u32 random32(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
int main(void) {
    const u16 widths[]={384,512,2560,3072};
    const u16 shapes[][2]={{6,6},{8,8},{16,16},{24,24},{32,32},{48,48},{6,8},{8,6},{16,24},{24,16},{32,48},{48,32}};
    u32 rows[512];unsigned long long tested=0,cross=0,same=0,positive=0;
    for(u16 wi=0;wi<4;wi++) {
        const u16 width=widths[wi];collisionStride=(width+255)/256;
        for(u16 pattern=0;pattern<5;pattern++) {
            for(u16 i=0;i<512;i++)rows[i]=pattern==0?0:pattern==1?UINT32_MAX:pattern==2?(i&1?UINT32_C(0xaaaaaaaa):UINT32_C(0x55555555)):pattern==3?(UINT32_C(0x80000000)>>(i%32)):random32();
            for(u16 si=0;si<12;si++) {
                const u16 w=shapes[si][0],h=shapes[si][1];
                for(s16 y=0;y<=320-h;y++)for(s16 x=0;x<=width-w;x++) {
                    const bool a=original(rows,x,y,w,h),b=occupied(rows,x,y,w,h),c=cells(rows,x,y,w,h);
                    if(a!=b||b!=c){fprintf(stderr,"mismatch %u %u %d %d %u %u\n",width,pattern,x,y,w,h);return 1;}
                    tested++;positive+=a;
                    if((x/8)/32==((x+w-1)/8)/32)same++;else cross++;
                }
            }
        }
    }
    printf("{\"passed\":true,\"queries\":%llu,\"sameWord\":%llu,\"crossWord\":%llu,\"occupiedResults\":%llu}\n",tested,same,cross,positive);
    return 0;
}
