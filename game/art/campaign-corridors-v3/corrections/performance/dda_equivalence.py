"""Execute unchanged clearShot() with a host collision observer, proving each sample."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]


def main():
    path=GAME/'src/actors/dinorah.c';source=path.read_text()
    start=source.index('static bool clearShot(');end=source.index('\n}',start)+2;tested=source[start:end]
    prefix=r'''
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
'''
    tail=r'''
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
'''
    host=HERE/'dda-equivalence-host.c';host.write_text(prefix+tested+'\n'+tail)
    exe=Path('/private/tmp/campaign-dda-equivalence')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(exe)],check=True)
    result=json.loads(subprocess.check_output([str(exe)],text=True))
    result.update(productionSource=str(path),productionFunctionSHA256=hashlib.sha256(tested.encode()).hexdigest(),
                  vectorRange=[-120,120],distanceGuard=112,origins=[[0,0],[-32,-32],[40,200],[3056,304]],
                  method='Exact extracted production clearShot compiled unchanged with collision observer. Each ordered sample equals old signed division; every possible first blocked sample and fully clear ray tested.',
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False)
    (HERE/'dda-equivalence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
