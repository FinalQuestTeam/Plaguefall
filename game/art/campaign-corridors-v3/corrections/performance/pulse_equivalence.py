"""Compile exact production pulse() on host and compare absolute-vtimer reference."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]


def main():
    path=GAME/'src/system/video/markers.c'
    source=path.read_text()
    start=source.index('static u32 pulseTimer=')
    end=source.index('\n}',source.index('static u16 pulse(void)',start))+2
    tested=source[start:end]
    prefix='''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint16_t u16;typedef uint32_t u32;
static u32 vtimer;static u16 fps;
'''
    tail=r'''
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
'''
    host=HERE/'pulse-equivalence-host.c'
    host.write_text(prefix+tested+'\n'+tail)
    executable=Path('/private/tmp/campaign-pulse-equivalence')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(executable)],check=True)
    result=json.loads(subprocess.check_output([str(executable)],text=True))
    result.update(productionSource=str(path),productionFunctionSHA256=hashlib.sha256(tested.encode()).hexdigest(),
                  rates=[50,60],consecutiveFramesPerRate=1000000,skipLengths=list(range(1,61)),
                  skipStartingValues=4096,wrap32StartingValuesPerRate=256,framesPerWrap=180,
                  randomJumpsPerRate=1000000,alternatingRateRandomJumps=1000000,
                  repeatedFrameQueries=True,reference='((now/(fps/2))&1)*4',
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False)
    (HERE/'pulse-equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
