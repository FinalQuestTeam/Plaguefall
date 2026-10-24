"""Prove compiled101number strings and fullu16fallback of the exact helper."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();rom=(args.build_dir/'rom.bin').read_bytes()
    symbols=[]
    for line in subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(args.build_dir/'rom.out')],text=True).splitlines():
        f=line.split()
        if len(f)==4 and f[3].split('.lto_priv.')[0]=='HUD_OBJECTIVE_NUMBERS':symbols.append((int(f[0],16),int(f[1],16)))
    assert symbols
    tables=[rom[a:a+s] for a,s in symbols];assert all(len(t)==404 and t==tables[0] for t in tables)
    table=tables[0]
    for i in range(101):assert table[i*4:i*4+4]==f'{i:03d}\0'.encode()
    source=(GAME/'src/core/objective.c').read_text();start=source.index('static void objectiveNumber3(')
    tested=source[start:source.index('\n}',start)+2]
    prefix='''#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
typedef uint16_t u16;typedef uint32_t u32;
static u16 divu(u32 n,u16 d){assert(d && n/d<=65535);return n/d;}
'''
    prefix+='static const char HUD_OBJECTIVE_NUMBERS[101][4]={'+','.join('{'+','.join(map(str,table[i*4:i*4+4]))+'}' for i in range(101))+'};\n'
    tail=r'''
int main(void){
    for(unsigned value=0;value<=65535;value++){
        char out[4],old[4];objectiveNumber3(out,value);
        const u16 hundreds=value/100,rest=value-hundreds*100,tens=rest/10;
        old[0]='0'+hundreds;old[1]='0'+tens;old[2]='0'+rest-tens*10;old[3]=0;
        assert(!memcmp(out,old,4));
        if(value<=100){char formatted[8];snprintf(formatted,sizeof formatted,"%03u",value);assert(!memcmp(out,formatted,4));}
    }
    printf("{\"passed\":true,\"compiledStrings\":101,\"tableBytes\":404,\"allU16ValuesAndFallback\":65536}\n");
}
'''
    host=HERE/'objective-number-host.c';host.write_text(prefix+tested+'\n'+tail)
    exe=Path('/private/tmp/campaign-objective-number')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(exe)],check=True)
    result=json.loads(subprocess.check_output([str(exe)],text=True))
    result.update(romSHA256=hashlib.sha256(rom).hexdigest(),productionFunctionSHA256=hashlib.sha256(tested.encode()).hexdigest(),
                  compiledTableSHA256=hashlib.sha256(table).hexdigest(),
                  method='All101compiledROMstrings equal exact3digits+NUL; unchanged extracted helper matches priorDIVUformula for everyu16value including fallback.',
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
