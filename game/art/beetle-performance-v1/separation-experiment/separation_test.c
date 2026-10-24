#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#define random SGDK_random
#include "enemies/enemies.h"
#undef random

Enemy enemies[MAX_ENEMIES];
static const EnemyDef small={.size=16},medium={.size=24},large={.size=32},boss={.size=48};
const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES]={
    &small,&small,&large,&small,&small,&small,&small,&small,
    &medium,&medium,&large,&medium,&medium,&medium,&boss};
static const u8 SEP_RECIP[32]={
    0,64,32,21,16,13,11,9,8,7,6,6,5,5,5,4,
    4,4,4,3,3,3,3,3,3,3,2,2,2,2,2,2};
static bool obstacle;
static unsigned calls;

static bool blocked(s16 x,s16 y,u16 size)
{
    return obstacle && x<232 && x+size>200 && y<224 && y+size>160;
}
void ARENA_move(s32 *x,s32 *y,s16 dx,s16 dy,u16 size)
{
    assert(abs(dx)<=SEP_MAX && abs(dy)<=SEP_MAX);calls++;
    s32 nx=*x+dx,ny=*y+dy;
    if(nx<8*64)nx=8*64;if(nx>(504-size)*64)nx=(504-size)*64;
    if(ny<64*64)ny=64*64;if(ny>(352-size)*64)ny=(352-size)*64;
    if(!blocked(nx>>6,*y>>6,size))*x=nx;
    if(!blocked(*x>>6,ny>>6,size))*y=ny;
}

#define ENEMIES_separate originalSeparate
#include "original-separate.inc"
#undef ENEMIES_separate
#define ENEMIES_separate compactSeparate
#include "separate.inc"
#undef ENEMIES_separate
#define SEPARATION_COMPASS
#define ENEMIES_separate compassSeparate
#include "separate.inc"
#undef ENEMIES_separate

static u32 rng=12648430;
static u16 next(void){rng=rng*1664525u+1013904223u;return rng>>16;}
static void run(void (*separate)(void)){separate();separate();}
static void valid(const Enemy *before)
{
    for(u16 i=0;i<MAX_ENEMIES;i++) {
        const Enemy *e=&enemies[i];
        if(!e->active){assert(!memcmp(e,&before[i],sizeof *e));continue;}
        assert(abs(e->fx-before[i].fx)<=SEP_MAX && abs(e->fy-before[i].fy)<=SEP_MAX);
        assert(e->fx>=8*64 && e->fx<=(504-ENEMY_SIZE(e))*64);
        assert(e->fy>=64*64 && e->fy<=(352-ENEMY_SIZE(e))*64);
        assert(!blocked(e->x,e->y,ENEMY_SIZE(e)));
    }
}
static double spread(void (*separate)(void))
{
    memset(enemies,0,sizeof enemies);obstacle=false;
    for(u16 i=0;i<8;i++) {
        Enemy *e=&enemies[i];e->active=true;e->type=ENEMY_SQ_PUR;
        e->x=240;e->y=184;e->fx=240*64;e->fy=184*64;
    }
    for(u16 t=0;t<600;t++)run(separate);
    double total=0;
    for(u16 i=0;i<8;i++)for(u16 j=i+1;j<8;j++) {
        const double dx=abs(enemies[i].fx-enemies[j].fx)/64.0,dy=abs(enemies[i].fy-enemies[j].fy)/64.0;
        total+=dx>=dy ? dx+dy/2 : dy+dx/2;
    }
    return total/28;
}
int main(void)
{
    Enemy start[MAX_ENEMIES],reference[MAX_ENEMIES];
    const u8 types[]={0,2,8};
    for(u16 scene=0;scene<4096;scene++) {
        memset(enemies,0,sizeof enemies);obstacle=(scene&1)!=0;
        for(u16 i=0;i<MAX_ENEMIES;i++) {
            Enemy *e=&enemies[i];e->active=next()%5!=0;e->type=types[next()%3];
            const u16 size=ENEMY_SIZE(e);
            do {
                e->x=8+next()%(496-size);e->y=64+next()%(288-size);
            }while(blocked(e->x,e->y,size));
            // Alternate sparse scenes with concentrated, overlapping groups.
            if(!(scene&3)){e->x=240+next()%16;e->y=232+next()%16;}
            e->fx=e->x*64+(next()&63);e->fy=e->y*64+(next()&63);
        }
        memcpy(start,enemies,sizeof start);calls=0;
        originalSeparate();assert(calls==0);originalSeparate();
        memcpy(reference,enemies,sizeof reference);
        memcpy(enemies,start,sizeof start);run(compactSeparate);
        assert(!memcmp(enemies,reference,sizeof reference));valid(start);
        memcpy(enemies,start,sizeof start);run(compassSeparate);valid(start);
    }
    // The compact routine also bounds the reciprocal for two 48px bosses;
    // the original reference is compared only over its 16/24/32px domain.
    memset(enemies,0,sizeof enemies);obstacle=false;
    enemies[0]=(Enemy){.x=100,.y=100,.fx=6400,.fy=6400,.type=ENEMY_BOSS,.active=true};
    enemies[1]=(Enemy){.x=134,.y=100,.fx=8576,.fy=6400,.type=ENEMY_BOSS,.active=true};
    memcpy(start,enemies,sizeof start);run(compactSeparate);valid(start);
    memcpy(enemies,start,sizeof start);run(compassSeparate);valid(start);
    const double original=spread(originalSeparate),compact=spread(compactSeparate),compass=spread(compassSeparate);
    assert(original>10 && compact==original && compass>=original*.8);
    printf("4096 compact/reference equivalence scenes; displacement, cadence, inactive actors, obstacle/bound checks and boss-distance bounds passed.\n");
    printf("Mean separation after 600 passes: original %.3f px, compact %.3f px, compass %.3f px.\n",original,compact,compass);
    return 0;
}
