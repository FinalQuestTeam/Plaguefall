"""Exact INV_matches versus INV_view storage comparison, including bomb truncation."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]


def main():
    source=(GAME/'src/core/inventory.c').read_text()
    def extract(name):
        start=source.index(name+'(');start=source.rfind('\n',0,start)+1
        if name=='INV_selected':return source[start:source.index('\n',start)]
        return source[start:source.index('\n}',start)+2]
    functions='\n'.join(extract(n) for n in ['INV_view','INV_selected','INV_matches'])
    prefix='''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint8_t u8;typedef uint16_t u16;
#define ITEM_BOMB 1
typedef struct {u8 type,charges;} InvSlot;
static InvSlot item[3];static u8 sel;static u16 bombs;
static u16 BOMB_count(void){return bombs;}
'''
    tail=r'''
static unsigned long long tests;
static void compare(const u8 *types,const u8 *counts){
    bool expected=true;InvSlot before[3];memcpy(before,item,sizeof item);u16 oldBombs=bombs;u8 oldSel=sel;
    for(u8 i=0;i<4;i++){u8 type,count;INV_view(i,&type,&count);if(types[i]!=type || counts[i]!=count)expected=false;}
    assert(INV_matches(types,counts)==expected);
    assert(!memcmp(before,item,sizeof item) && bombs==oldBombs && sel==oldSel && INV_selected()==oldSel);tests++;
}
static void snapshot(u8 *types,u8 *counts){for(u8 i=0;i<4;i++)INV_view(i,&types[i],&counts[i]);}
int main(void){
    u8 types[4],counts[4];
    for(sel=0;sel<4;sel++){
        for(unsigned b=0;b<=65535;b++){
            bombs=b;snapshot(types,counts);
            for(unsigned c=0;c<256;c++){counts[0]=c;compare(types,counts);}
        }
        bombs=0x9aff;
        for(unsigned field=0;field<6;field++)for(unsigned value=0;value<256;value++){
            ((u8 *)item)[field]=value;snapshot(types,counts);
            for(unsigned candidate=0;candidate<256;candidate++){
                if(field&1)counts[field/2+1]=candidate;else types[field/2+1]=candidate;
                compare(types,counts);
            }
        }
        snapshot(types,counts);for(unsigned type=0;type<256;type++){types[0]=type;compare(types,counts);}
    }
    printf("{\"passed\":true,\"comparisons\":%llu,\"allU16BombCountsAgainstAllU8SnapshotCounts\":true,\"allSixItemBytes0to255\":true,\"allFourSelections\":true,\"readOnlyStorageVerified\":true}\n",tests);
}
'''
    host=HERE/'inventory-matches-host.c';host.write_text(prefix+functions+'\n'+tail)
    exe=Path('/private/tmp/campaign-inventory-matches')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(exe)],check=True)
    result=json.loads(subprocess.check_output([str(exe)],text=True))
    result.update(productionFunctionsSHA256=hashlib.sha256(functions.encode()).hexdigest(),
                  method='Exact extracted INV_view, INV_selected and INV_matches. Every bomb16value against every snapshot8count; every item byte/storage8value against every snapshot8value; all selections and invalid bomb type snapshots. No storage changes permitted.',
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False)
    (HERE/'inventory-matches-equivalence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
