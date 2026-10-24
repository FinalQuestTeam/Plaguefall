"""Exhaustive0..100glyph transitions against prior full clear/text rendering."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import argparse

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]
BUILD=Path('/private/tmp/plaguefall-guidebook-milestones/442390ac21328b74a427f2fc8c63742bdcb5abf80aea3fab4aee6e2ccf020ec8')


def extract(source,name):
    match=re.search(r'static void '+name+r'\([^\n]+\)\n\{',source)
    assert match,name
    return source[match.start():source.index('\n}',match.end())+2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path,default=BUILD)
    parser.add_argument('--output',type=Path,default=HERE/'hud-value-glyph-equivalence.json')
    args=parser.parse_args();build=args.build_dir
    source=(GAME/'src/system/video/screens/hud.c').read_text()
    functions='\n'.join(extract(source,n) for n in ['rect','blitRow','text','markRect','valueGlyph','editValue','inventoryDigit'])
    symbols={}
    for line in subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(build/'rom.out')],text=True).splitlines():
        f=line.split()
        if len(f)==4:symbols[f[3]]=(int(f[0],16),int(f[1],16))
    rom=(build/'rom.bin').read_bytes()
    def array(name,key,kind):
        a,size=symbols[key];data=rom[a:a+size]
        vals=struct.unpack('>'+str(size//4)+'I',data) if kind=='u32' else data
        return 'static const '+kind+' '+name+'[]={'+','.join(hex(x) for x in vals)+'};\n'
    fonts=[rom[a:a+s] for k,(a,s) in symbols.items() if k.startswith('RESULT_FONT')]
    assert all(f==fonts[0] for f in fonts)
    prefix='''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint32_t u32;typedef uint16_t u16;typedef uint8_t u8;
#define TRUE true
static u32 hudPixels[960];static u8 hudDirty[120];static bool hudPending;
'''+array('HUD_FONT_MASK','HUD_FONT_MASK','u32')+array('RESULT_FONT','RESULT_FONT.lto_priv.0','u8')
    if 'HUD_NATIVE_DIGITS' in functions:
        prefix+=array('HUD_NATIVE_DIGITS','HUD_NATIVE_DIGITS','u32').replace('HUD_NATIVE_DIGITS[]','HUD_NATIVE_DIGITS[3][10][8]')
    tail=r'''
static void oldEditValue(const char *value,char *previous,u16 x,u16 color){
    if(!strcmp(value,previous))return;
    const u16 a=strlen(value),b=strlen(previous),width=(a>b?a:b)*8;
    rect(x,13,width,8,11);text(value,x,13,color);markRect(x,13,width,8);strcpy(previous,value);
}
static unsigned long long cases,changedTiles;
static void compare(const char *before,const char *after,u16 x,u16 color){
    u32 initial[960],expected[960];char previous[20];
    for(unsigned i=0;i<960;i++)hudPixels[i]=(UINT32_C(0x12345678)*i)^UINT32_C(0xb193c574);
    rect(x,13,strlen(before)*8,8,11);text(before,x,13,color);memcpy(initial,hudPixels,sizeof initial);
    strcpy(previous,before);oldEditValue(after,previous,x,color);memcpy(expected,hudPixels,sizeof expected);
    memcpy(hudPixels,initial,sizeof initial);memset(hudDirty,0,sizeof hudDirty);hudPending=false;
    strcpy(previous,before);editValue(after,previous,x,color);
    assert(!memcmp(expected,hudPixels,sizeof expected));assert(!strcmp(previous,after));
    for(unsigned tile=0;tile<120;tile++)if(memcmp(initial+tile*8,hudPixels+tile*8,32)){assert(hudDirty[tile]);changedTiles++;}
    cases++;
}
int main(void){
    const u16 positions[]={8,20,64,72};const u16 colors[]={1,2,4};
    for(unsigned p=0;p<4;p++)for(unsigned c=0;c<3;c++)for(unsigned old=0;old<=100;old++)for(unsigned now=0;now<=100;now++){
        char a[20],b[20];snprintf(a,sizeof a,"%03u",old);snprintf(b,sizeof b,"%03u",now);compare(a,b,positions[p],colors[c]);
    }
    const char *fallbacks[]={"","0","00","000","100","000%","3/4"};
    for(unsigned a=0;a<7;a++)for(unsigned b=0;b<7;b++)for(unsigned p=0;p<4;p++)for(unsigned c=0;c<3;c++)compare(fallbacks[a],fallbacks[b],positions[p],colors[c]);
    unsigned inventoryCases=0;
    const u16 ys[]={3,8,13};
    for(unsigned a=0;a<10;a++)for(unsigned b=0;b<10;b++)for(unsigned y=0;y<3;y++)for(unsigned color=1;color<=2;color++){
        u32 initial[960],expected[960];char before[2]={'0'+a,0},after[2]={'0'+b,0};
        for(unsigned i=0;i<960;i++)hudPixels[i]=(UINT32_C(0x5371a09b)*i)^UINT32_C(0xa195c774);
        rect(225,ys[y],8,8,11);text(before,225,ys[y],color);memcpy(initial,hudPixels,sizeof initial);
        rect(225,ys[y],8,8,11);text(after,225,ys[y],color);memcpy(expected,hudPixels,sizeof expected);
        memcpy(hudPixels,initial,sizeof initial);memset(hudDirty,0,sizeof hudDirty);inventoryDigit('0'+b,ys[y],color);
        assert(!memcmp(expected,hudPixels,sizeof expected));
        for(unsigned tile=0;tile<120;tile++)if(memcmp(initial+tile*8,hudPixels+tile*8,32))assert(hudDirty[tile]);
        inventoryCases++;
    }
    printf("{\"passed\":true,\"transitions\":%llu,\"inventoryDigitTransitions\":%u,\"changedTilesCheckedDirty\":%llu,\"all0to100Pairs\":true,\"full3840ByteCanvasCompared\":true,\"fallbackLengthsCompared\":true}\n",cases,inventoryCases,changedTiles);
}
'''
    host=HERE/'hud-value-glyph-host.c';host.write_text(prefix+functions+'\n'+tail)
    exe=Path('/private/tmp/campaign-hud-value-glyph')
    subprocess.run(['cc','-std=c11','-O2','-fsanitize=address,undefined',str(host),'-o',str(exe)],check=True)
    result=json.loads(subprocess.check_output([str(exe)],text=True))
    result.update(romSHA256=hashlib.sha256(rom).hexdigest(),sourceFunctionsSHA256=hashlib.sha256(functions.encode()).hexdigest(),
                  positions=[8,20,64,72],colors=[1,2,4],allCompiledFontCopiesIdentical=True,
                  method='Exact extracted production rect/text/valueGlyph/editValue with exact ROMfont/mask. Compare all101x101numeric transitions against previous full clear/text; random neighbour pixels and every changed tile dirty bit checked.',
                  sanitizers=['address','undefined'],productionModified=False,native68000TimingClaim=False)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
