#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "core/signal.h"
#include "levels/graph.h"

int main(void)
{
    unsigned accepted=0,errors=0;u8 code[6],bad[6];SignalProgress decoded;
    unsigned char *used=calloc(1,1<<24);assert(used);
    for(u8 node=1;node<NODE_MAX;node++)for(u8 flags=0;flags<8;flags++)
    for(u8 power=1;power<=5;power++)for(u8 speed=0;speed<=5;speed++)
    {
        const SignalProgress p={node,flags,power,speed};
        if(!SIGNAL_valid(&p)){assert(!SIGNAL_encode(&p,code));continue;}
        assert(SIGNAL_encode(&p,code));assert(SIGNAL_decode(code,&decoded));
        assert(!memcmp(&p,&decoded,sizeof p));
        u32 key=0;for(unsigned i=0;i<6;i++)key=(key<<4)|code[i];
        assert(!used[key]);used[key]=1;accepted++;
        for(unsigned i=0;i<6;i++)for(unsigned replacement=0;replacement<16;replacement++)
        {
            if(replacement==code[i])continue;
            memcpy(bad,code,6);bad[i]=replacement;
            SignalProgress untouched={255,255,255,255};
            assert(!SIGNAL_decode(bad,&untouched));
            assert(untouched.node==255 && untouched.flags==255 && untouched.power==255 && untouched.speed==255);
            errors++;
        }
        const u8 route[16]={N_1,(flags&1)?N_2B:N_2A,N_3,N_4,N_5,(flags&2)?N_6B:N_6A,
            N_7,N_8,N_9,N_10,N_11,N_12,(flags&4)?N_13B:N_13A,N_14,N_15,N_16};
        u32 expected=0;
        for(unsigned i=0;i<16 && route[i]!=node;i++)expected|=(u32)1<<route[i];
        assert(SIGNAL_history(&p)==expected);
        SIGNAL_capture(node,flags,power,speed);assert(SIGNAL_checkpoint(&decoded));
        assert(!memcmp(&p,&decoded,sizeof p));SIGNAL_reset();assert(!SIGNAL_checkpoint(&decoded));
    }
    assert(accepted==2070 && errors==186300);
    const SignalProgress invalid[]={ {0,0,1,0},{NODE_MAX,0,1,0},{1,8,1,0},{1,0,0,0},{1,0,6,0},{1,0,1,6} };
    for(unsigned i=0;i<sizeof invalid/sizeof *invalid;i++)assert(!SIGNAL_encode(invalid+i,code));
    const u8 malformed[][6]={{0,0,0,1,7,4},{8,0,0,1,12,2},{12,0,0,1,9,9},{4,0,0,0,2,8},{4,0,1,4,4,4},{4,7,0,1,4,4},{7,0,0,1,13,6},{4,0,4,1,14,8}};
    for(unsigned i=0;i<sizeof malformed/sizeof *malformed;i++)assert(!SIGNAL_decode(malformed[i],&decoded));
    memset(bad,0,sizeof bad);assert(!SIGNAL_decode(bad,&decoded));
    bad[0]=16;assert(!SIGNAL_decode(bad,&decoded));
    assert(!SIGNAL_valid(NULL));assert(!SIGNAL_encode(NULL,code));assert(!SIGNAL_decode(NULL,&decoded));
    assert(!SIGNAL_decode(code,NULL));assert(!SIGNAL_checkpoint(NULL));
    free(used);printf("Signal: %u valid checkpoints, unique roundtrips, all8 histories, %u single-symbol errors rejected.\n",accepted,errors);
    return 0;
}
