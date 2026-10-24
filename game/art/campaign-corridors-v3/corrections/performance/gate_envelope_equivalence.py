"""Exact extracted gate callbacks versus the former callbacks without broadphase."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]


def main():
    source=(GAME/'src/levels/campaign_route_ops.c').read_text()
    start=source.index('bool CR_OPS_blocked(');end=source.index('\nstatic bool working',start)
    tested=source[start:end]
    old='\n'.join(line for line in tested.splitlines() if 'if(gateBoundsValid &&' not in line)
    old=old.replace('CR_OPS_blocked(','old_blocked(').replace('CR_OPS_shotBlocked(','old_shotBlocked(')
    meta=json.loads((HERE/'expected-ce8b35/maps.json').read_text())['06b']
    rects=','.join('{'+','.join(map(str,r))+',false}' for r in meta['gates'])
    prefix='''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef int16_t s16;typedef uint16_t u16;typedef uint8_t u8;
#define TRUE true
#define FALSE false
typedef struct {s16 x,y,w,h;bool blocksShots;} ArenaRect;
typedef struct {u16 work[2],steamClock,damageTimer;u8 gateHp[2],pressureMask;u16 gateClearTicks[2];} CampaignRouteOperations;
static CampaignRouteOperations campaignRouteOps;
static bool gateBoundsValid=true;static s16 gateLeft,gateTop,gateRight,gateBottom;
static const u16 fps=60;
static int effects;
static bool CR_OPS_active(void){return true;}
static bool overlap(const ArenaRect *r,s16 x,s16 y,u16 w,u16 h){return x<r->x+r->w && x+(s16)w>r->x && y<r->y+r->h && y+(s16)h>r->y;}
static void SFX_playerHit(void){effects+=1;}
static void OBJECTIVEGFX_activate(u16 i){effects+=10+i;}
static void sfxItemPickup(void){effects+=100;}
static void OBJECTIVEGFX_prime(u16 i,bool b){effects+=1000+i+b;}
'''+f'static const ArenaRect CAMPAIGN_ROUTE06B_gates[2]={{{rects}}};\n'
    tail=r'''
int main(void) {
    unsigned long long geometry=0,damage=0;
    gateLeft=gateTop=32767;gateRight=gateBottom=-32768;
    for(u8 i=0;i<2;i++){const ArenaRect *g=&CAMPAIGN_ROUTE06B_gates[i];if(g->x<gateLeft)gateLeft=g->x;if(g->y<gateTop)gateTop=g->y;if(g->x+g->w>gateRight)gateRight=g->x+g->w;if(g->y+g->h>gateBottom)gateBottom=g->y+g->h;}
    const u16 sizes[]={6,8,16,24,32,48};
    for(u8 state=0;state<4;state++) {
        memset(&campaignRouteOps,0,sizeof campaignRouteOps);campaignRouteOps.gateHp[0]=state&1;campaignRouteOps.gateHp[1]=(state>>1)&1;
        for(s16 x=-32;x<=3104;x++)for(s16 y=-32;y<=352;y++)for(u8 i=0;i<6;i++) {
            assert(CR_OPS_blocked(x,y,sizes[i],sizes[i])==old_blocked(x,y,sizes[i],sizes[i]));geometry++;
        }
    }
    for(u8 hp0=0;hp0<=4;hp0++)for(u8 hp1=0;hp1<=4;hp1++)for(u8 tick=0;tick<4;tick++)
    for(u8 pressure=0;pressure<4;pressure++)for(u8 player=0;player<2;player++)for(u8 valid=0;valid<2;valid++)
    for(u8 gate=0;gate<2;gate++) {
        gateBoundsValid=valid;
        const ArenaRect *g=&CAMPAIGN_ROUTE06B_gates[gate];
        for(s16 x=g->x-9;x<=g->x+g->w+9;x++)for(s16 y=g->y-9;y<=g->y+g->h+9;y++) {
            CampaignRouteOperations initial={0};initial.gateHp[0]=hp0;initial.gateHp[1]=hp1;initial.pressureMask=pressure;
            initial.gateClearTicks[0]=(tick&1)?48:0;initial.gateClearTicks[1]=(tick&2)?48:0;
            campaignRouteOps=initial;effects=0;bool a=CR_OPS_shotBlocked(x,y,player);CampaignRouteOperations after=campaignRouteOps;int expected_effects=effects;
            campaignRouteOps=initial;effects=0;bool b=old_shotBlocked(x,y,player);
            assert(a==b && !memcmp(&after,&campaignRouteOps,sizeof after) && effects==expected_effects);damage++;
        }
    }
    printf("{\"passed\":true,\"geometryQueries\":%llu,\"damageAndEffectComparisons\":%llu,\"allHP0to4\":true,\"closedCollapsingOpen\":true,\"cacheInvalidFallback\":true}\n",geometry,damage);
}
'''
    host=HERE/'gate-envelope-host.c';host.write_text(prefix+tested+'\n'+old+'\n'+tail)
    exe=Path('/private/tmp/campaign-gate-envelope')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(exe)],check=True)
    result=json.loads(subprocess.check_output([str(exe)],text=True))
    result.update(productionFunctionSHA256=hashlib.sha256(tested.encode()).hexdigest(),gates=meta['gates'],
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False,
                  method='Extracted current callbacks, exact former callbacks obtained by removing only early-envelope lines. Compare geometry, HP, collapse timers and all sound/visual side effects.')
    (HERE/'gate-envelope-equivalence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
