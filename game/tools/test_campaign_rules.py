"""Exercise the production graph, persistent consequences and radio variants."""
from pathlib import Path
import json,re,subprocess,tempfile,textwrap
GAME=Path(__file__).resolve().parents[1]
SRC=GAME/'src'
def main():
    defs=sorted(set(re.findall(r'\b(?:LEVEL|TEST)\w*_def\b',(SRC/'levels/levels.h').read_text())))
    with tempfile.TemporaryDirectory(prefix='campaign-rules-') as tmp:
        t=Path(tmp);(t/'levels').mkdir();(t/'core').mkdir()
        (t/'genesis.h').write_text('#pragma once\n#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\ntypedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;\n#define TRUE true\n#define FALSE false\n')
        (t/'levels/levels.h').write_text('#pragma once\n#include <genesis.h>\ntypedef struct {const u8 *enemyTypes;u8 enemyTypeCount;} LevelDef;\n'+'\n'.join('extern const LevelDef '+n+';' for n in defs))
        (t/'core/stats.h').write_text('#pragma once\n#include <genesis.h>\ntypedef struct {u16 bombsUsed,damageTaken;bool objFailed;} PhaseStats;extern PhaseStats phaseStats;u16 STATS_seconds(void);\n')
        test='''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "levels/graph.h"
#include "levels/story.h"
#include "core/stats.h"
#include "core/campaign_state.h"
PhaseStats phaseStats;u16 STATS_seconds(void){return 999;}
'''+ '\n'.join('const LevelDef '+n+'={0};' for n in defs)+'''
int main(void){
 assert(NODE_COUNT==19);
 for(u8 flags=0;flags<8;flags++){
  CAMPAIGN_reset();u8 n=N_1,steps=0;u32 seen=0;
  while(n){
   assert(++steps<=16);seen|=1u<<n;
   phaseStats.bombsUsed=(n==N_1 && (flags&1))?1:0;
   phaseStats.objFailed=(n==N_5 && (flags&2))||(n==N_12 && (flags&4));
   CAMPAIGN_record(n,phaseStats.objFailed);n=GRAPH_resolve(n);
  }
  assert(steps==16 && campaignFlags==flags && (seen&(1u<<N_16)));
  assert(seen&(1u<<((flags&1)?N_2B:N_2A)));
  assert(seen&(1u<<((flags&2)?N_6B:N_6A)));
  assert(seen&(1u<<((flags&4)?N_13B:N_13A)));
  for(u8 node=N_14;node<=N_16;node++){
   const StoryEntry *s=STORY_find(node,ANTES);assert(s);bool speaks=false;
   for(u8 i=0;i<s->count;i++)if(s->lines[i].portrait==P_DINORAH)speaks=true;
   assert(speaks==!(flags&4));
  }
  const StoryEntry *end=STORY_find(N_16,DEPOIS);assert(end && end->count>=6);
  bool din=false;for(u8 i=0;i<end->count;i++)din|=end->lines[i].portrait==P_DINORAH;
  assert(din==!(flags&4));
 }
 CAMPAIGN_reset();CAMPAIGN_record(N_6B,true);assert(campaignFlags==0);
 assert(!GRAPH_hasFailExit(N_6A)&&!GRAPH_hasFailExit(N_6B));
 assert(GRAPH_hasFailExit(N_5)&&GRAPH_hasFailExit(N_12));
 assert(!GRAPH_hasFailExit(N_15));
 puts("PASS: 8 campaign paths, 3 consequences, Dinorah variants, retry boundaries");
}
'''
        (t/'test.c').write_text(test)
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-fsanitize=address,undefined','-I'+str(t),'-I'+str(SRC),str(t/'test.c'),str(SRC/'levels/graph.c'),str(SRC/'levels/story.c'),str(SRC/'core/campaign_state.c'),'-o',str(t/'test')],check=True)
        subprocess.run([str(t/'test')],check=True)
    # Native codec maps each accented glyph to one byte. Simulate actual wrapping.
    lines=re.findall(r'LINE\(P_\w+,("(?:[^"\\]|\\.)*")\)',(SRC/'levels/story.c').read_text())
    for raw in lines:
        value=json.loads(raw);rest=value
        for row in range(4):
            rest=rest.lstrip(' ')
            if not rest:break
            length=min(len(rest),26)
            if len(rest)>26:
                space=rest[:26].rfind(' ')
                if space>0:length=space
            rest=rest[length:]
        assert not rest.strip(),f'Radio text clipped: {value}'
    print('PASS:',len(lines),'radio lines fit the native 26x4 panel')
if __name__=='__main__':main()
