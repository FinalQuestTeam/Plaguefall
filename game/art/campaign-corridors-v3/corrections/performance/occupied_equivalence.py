"""Host proof of the exact production occupied() implementation; no ROM build."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]


def main():
    arena = GAME / 'src/levels/arena.c'
    source = arena.read_text()
    begin = source.index('static const u32 occupiedLeft[32]')
    end = source.index('\n}', source.index('static bool occupied(', begin)) + 2
    tested = source[begin:end]
    header = '''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint16_t u16;typedef int16_t s16;typedef uint32_t u32;
#define TRUE true
#define FALSE false
static u16 collisionStride;
'''
    tail = r'''
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
'''
    path = HERE / 'occupied-equivalence-host.c'
    path.write_text(header + tested + '\n' + tail)
    executable = Path('/private/tmp/campaign-occupied-equivalence')
    command = ['cc', '-std=c11', '-O2', '-fsanitize=address,undefined', str(path), '-o', str(executable)]
    subprocess.run(command, check=True)
    result = json.loads(subprocess.check_output([str(executable)], text=True))
    result.update(productionSource=str(arena), productionFunctionSHA256=hashlib.sha256(tested.encode()).hexdigest(),
                  footprints=[[6,6],[8,8],[16,16],[24,24],[32,32],[48,48],[6,8],[8,6],[16,24],[24,16],[32,48],[48,32]],
                  widths=[384,512,2560,3072], height=320,
                  masks=['empty','full','alternating','singleBitPerWord','deterministicXorshift32'],
                  coordinates='Every integer x,y contained in the world for each footprint; includes every8px and256px crossing.',
                  preconditions='occupied() is only called after outside/bounds guards; negative/out-of-world inputs are excluded as in production.',
                  sanitizers=['address','undefined'], native68000TimingClaim=False,
                  reference='Former variable32bit-shift masks plus independent per-cell occupancy. Exact extracted production LUT/function is compiled unchanged.')
    (HERE/'occupied-equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
