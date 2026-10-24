"""Host cache invalidation proof using exact extracted production ray functions."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]


def function(source,name):
    start=source.index('static bool '+name+'(')
    return source[start:source.index('\n}',start)+2]


def main():
    source=(GAME/'src/actors/dinorah.c').read_text()
    uncached=function(source,'uncachedClearShot');cached=function(source,'clearShot')
    start=source.index('typedef struct {s16 x,y,tx,ty;u8 gates;bool clear;} SightRay;')
    structures=source[start:source.index('\nvoid DINORAH_clear',start)]
    assert 'void DINORAH_clear(void){sightCount=sightNext=0;' in source
    assert 'DINORAH_clear();path=route;' in source
    meta=json.loads((HERE/'expected-ce8b35/maps.json').read_text())['06b']
    rects=','.join('{'+','.join(map(str,r[:4]))+'}' for r in meta['solids'] if len(r)<5 or r[4])
    gates=','.join('{'+','.join(map(str,r))+'}' for r in meta['gates'])
    prefix=r'''
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
'''+f'static const Rect solids[]={{{rects}}};\nstatic const Rect gates[]={{{gates}}};\n'+r'''
static bool hit(Rect r,int x,int y){return x<r.x+r.w && x+8>r.x && y<r.y+r.h && y+8>r.y;}
static bool ARENA_shotBlocked(s16 x,s16 y){
    y-=16;
    if(x<24 || x>3040 || y<64 || y>264)return true;
    for(unsigned i=0;i<sizeof(solids)/sizeof(*solids);i++)if(hit(solids[i],x,y))return true;
    for(unsigned i=0;i<2;i++)if((gateMask&(1<<i)) && hit(gates[i],x,y))return true;
    return false;
}
'''
    # The single host observer increments on entry; all production statements
    # and the cache key/comparison/eviction logic are otherwise unchanged.
    observed=uncached.replace('{\n','{\n    uncachedCalls++;\n',1)
    tail=r'''
static void reset(void){sightCount=sightNext=0;}
static void compare(s16 tx,s16 ty){
    unsigned long long before=uncachedCalls;
    bool a=clearShot(tx,ty);hits+=uncachedCalls==before;
    bool b=uncachedClearShot(tx,ty);assert(a==b);comparisons++;
}
static void must_miss(s16 tx,s16 ty){unsigned long long n=uncachedCalls;clearShot(tx,ty);assert(uncachedCalls==n+1);invalidationChecks++;}
static u32_dummy(void); /* removed by Python below */
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
'''.replace('static u32_dummy(void); /* removed by Python below */','')
    host=HERE/'sight-cache-host.c';host.write_text(prefix+structures+'\n'+observed+'\n'+cached+'\n'+tail)
    exe=Path('/private/tmp/campaign-sight-cache')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(exe)],check=True)
    result=json.loads(subprocess.check_output([str(exe)],text=True))
    result.update(productionFunctionsSHA256=hashlib.sha256((structures+uncached+cached).encode()).hexdigest(),
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False,
                  contracts=['Cache keys include integer originXY and endpointXY, exact2bit gate occupancy.','HP>0 and collapseTicks>0 both mean the same occupied gate; HP changes do not change geometry.','DINORAH_clear resets count/cursor; DINORAH_start invokes clear; only campaign uses cache.','Static shotRows/bounds and geometry are immutable within each campaign escort. Read-only tests cannot damage gates.'],
                  method='Exact cache and DDA functions extracted; one host entry counter added to uncached function only. Compare against uncached on static architecture plus all gate masks; exercise movement, eviction, restart and training bypass.')
    (HERE/'sight-cache-equivalence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
