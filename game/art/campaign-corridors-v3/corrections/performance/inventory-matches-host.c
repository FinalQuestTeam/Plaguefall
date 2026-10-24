#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint8_t u8;typedef uint16_t u16;
#define ITEM_BOMB 1
typedef struct {u8 type,charges;} InvSlot;
static InvSlot item[3];static u8 sel;static u16 bombs;
static u16 BOMB_count(void){return bombs;}
void INV_view(u8 i, u8 *type, u8 *count)
{
    if (i == 0) { *type = ITEM_BOMB; *count = (u8) BOMB_count(); }
    else        { *type = item[i - 1].type; *count = item[i - 1].charges; }
}
u8 INV_selected(void) { return sel; }
bool INV_matches(const u8 *types,const u8 *counts)
{
    return types[0]==ITEM_BOMB && counts[0]==(u8)BOMB_count() &&
        types[1]==item[0].type && counts[1]==item[0].charges &&
        types[2]==item[1].type && counts[2]==item[1].charges &&
        types[3]==item[2].type && counts[3]==item[2].charges;
}

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
