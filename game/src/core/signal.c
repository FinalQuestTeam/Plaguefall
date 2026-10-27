#include "core/signal.h"
#include "levels/graph.h"
#include "core/campaign_state.h"

static SignalProgress checkpoint;

bool SIGNAL_valid(const SignalProgress *p)
{
    if(!p || !p->node || p->node>=NODE_MAX || p->flags>7 ||
       !p->power || p->power>5 || p->speed>5)return FALSE;
    const u8 n=p->node,f=p->flags;
    if(n==N_1 && f)return FALSE;
    if(n<=N_5 && (f&(CAMPAIGN_RESCUE_PARTIAL|CAMPAIGN_DINORAH_DEAD)))return FALSE;
    if(n<=N_12 && (f&CAMPAIGN_DINORAH_DEAD))return FALSE;
    if(n==N_2A && (f&CAMPAIGN_CHURCH_RUINED))return FALSE;
    if(n==N_2B && !(f&CAMPAIGN_CHURCH_RUINED))return FALSE;
    if(n==N_6A && (f&CAMPAIGN_RESCUE_PARTIAL))return FALSE;
    if(n==N_6B && !(f&CAMPAIGN_RESCUE_PARTIAL))return FALSE;
    if(n==N_13A && (f&CAMPAIGN_DINORAH_DEAD))return FALSE;
    if(n==N_13B && !(f&CAMPAIGN_DINORAH_DEAD))return FALSE;
    return TRUE;
}

// CRC-8/0x07, initial value A7, over the two payload bytes, MSB first.
// Payload: version:2, speed:3, power-minus-one:3, flags:3, node:5.
static u8 checksum(u16 payload)
{
    u8 crc=0xa7;
    for(u8 byte=0;byte<2;byte++)
    {
        crc^=(u8)(payload>>(byte ? 0 : 8));
        for(u8 bit=0;bit<8;bit++)crc=(crc&0x80) ? (u8)((crc<<1)^7) : (u8)(crc<<1);
    }
    return crc;
}
bool SIGNAL_encode(const SignalProgress *p,u8 symbols[SIGNAL_LENGTH])
{
    if(!symbols || !SIGNAL_valid(p))return FALSE;
    const u16 payload=(SIGNAL_VERSION<<14)|(p->speed<<11)|((p->power-1)<<8)|(p->flags<<5)|p->node;
    u32 value=((u32)payload<<8)|checksum(payload);
    for(u8 i=SIGNAL_LENGTH;i;i--){symbols[i-1]=value&15;value>>=4;}
    return TRUE;
}
bool SIGNAL_decode(const u8 symbols[SIGNAL_LENGTH],SignalProgress *p)
{
    if(!symbols || !p)return FALSE;
    u32 value=0;
    for(u8 i=0;i<SIGNAL_LENGTH;i++){if(symbols[i]>=SIGNAL_SYMBOLS)return FALSE;value=(value<<4)|symbols[i];}
    const u16 payload=value>>8;
    if((payload>>14)!=SIGNAL_VERSION || (u8)value!=checksum(payload))return FALSE;
    const SignalProgress decoded={payload&31,(payload>>5)&7,((payload>>8)&7)+1,(payload>>11)&7};
    if(!SIGNAL_valid(&decoded))return FALSE;
    *p=decoded;return TRUE;
}
u32 SIGNAL_history(const SignalProgress *p)
{
    if(!SIGNAL_valid(p))return 0;
    u32 history=0;u8 n=N_1;
    while(n<p->node)
    {
        history|=(u32)1<<n;
        switch(n)
        {
            case N_1:n=(p->flags&CAMPAIGN_CHURCH_RUINED) ? N_2B : N_2A;break;
            case N_2A:case N_2B:n=N_3;break;
            case N_5:n=(p->flags&CAMPAIGN_RESCUE_PARTIAL) ? N_6B : N_6A;break;
            case N_6A:case N_6B:n=N_7;break;
            case N_12:n=(p->flags&CAMPAIGN_DINORAH_DEAD) ? N_13B : N_13A;break;
            case N_13A:case N_13B:n=N_14;break;
            default:n++;break;
        }
    }
    return history;
}
void SIGNAL_reset(void){checkpoint.node=0;}
void SIGNAL_capture(u8 node,u8 flags,u8 power,u8 speed)
{
    const SignalProgress p={node,flags,power,speed};
    if(SIGNAL_valid(&p))checkpoint=p;
}
bool SIGNAL_checkpoint(SignalProgress *p)
{
    if(!p || !SIGNAL_valid(&checkpoint))return FALSE;
    *p=checkpoint;return TRUE;
}
