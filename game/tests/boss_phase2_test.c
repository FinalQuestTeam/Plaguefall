#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "enemies/enemy_boss.h"
#include "actors/shots.h"

u16 fps;
s16 px,py;
Enemy enemies[MAX_ENEMIES];
static unsigned room,volleys,pulses;
static u8 widths[32];
static const EnemyDef boss={.size=48,.hp=25,.speedFp=32};

u32 getApproximatedDistance(s16 x,s16 y)
{
    unsigned a=abs(x),b=abs(y);return a>b ? a+b/2 : b+a/2;
}
void ENEMIES_integrate(Enemy *e)
{
    e->fx+=e->vx;e->fy+=e->vy;e->x=e->fx/64;e->y=e->fy/64;
}
void ENEMIES_spawnAt(u8 type,s16 x,s16 y)
{
    for(unsigned i=0;i<MAX_ENEMIES;i++)if(!enemies[i].active) {
        enemies[i]=(Enemy){.type=type,.x=x,.y=y,.active=TRUE};return;
    }
}
void SFX_countPulse(bool go){assert(go);pulses++;}
bool SHOTS_enemyHasRoom(u8 count){assert(count==5);return room>=count;}
void SHOTS_enemyTarget(s16 x,s16 y){assert(x==px+8 && y==py+8);}
void fireEnemySpreadDmgWidth(s16 x,s16 y,u8 count,u8 dmg,u8 style,u8 divisor)
{
    (void)x;(void)y;assert(count==5 && dmg==13 && style==4);
    widths[volleys++%32]=divisor;
}
void fireEnemySpreadDmg(s16 x,s16 y,u8 count,u8 dmg,u8 style)
{fireEnemySpreadDmgWidth(x,y,count,dmg,style,3);}
static void tick(Enemy *e){ENEMYBOSS_update(e,&boss);}
static void ticks(Enemy *e,unsigned n){while(n--)tick(e);}
static unsigned hunters(void)
{
    unsigned n=0;for(unsigned i=0;i<MAX_ENEMIES;i++)n+=enemies[i].active && enemies[i].type==ENEMY_TRI_YEL;return n;
}
static Enemy *reset(u8 hp)
{
    memset(enemies,0,sizeof(enemies));room=10;volleys=pulses=0;px=600;py=400;
    enemies[0]=(Enemy){.type=ENEMY_BOSS,.hp=hp,.x=200,.y=200,.fx=200*64,.fy=200*64,.active=TRUE};
    return &enemies[0];
}
static void phase2(void)
{
    Enemy *e=reset(13);tick(e);assert(!(e->tB&BOSS_FURY));
    e->hp=12;e->shielded=TRUE;tick(e);
    assert((e->tB&BOSS_FURY) && e->mode==BOSS_TRANSITION && !e->shielded && pulses==1);
    const s16 x=e->x,y=e->y;
    bool flashed=false;
    for(unsigned i=1;i<4*fps/5-1;i++) {
        flashed|=e->hitFlash!=0;tick(e);
        assert(e->x==x && e->y==y && !e->shielded && e->mode==BOSS_TRANSITION);
    }
    assert(flashed);tick(e);assert(e->mode==BOSS_APPROACH);
    // Healing cannot undo/retrigger the once-only phase change.
    e->hp=25;ticks(e,3*fps/5);assert(e->mode==BOSS_TELEGRAPH && pulses==1);
    for(unsigned dash=0;dash<2;dash++) {
        s16 vx=e->vx,vy=e->vy,xx=e->x,yy=e->y;
        px=-px;py=-py; // moving the target cannot change the warned heading
        ticks(e,7*fps/20);
        assert(e->mode==BOSS_DASH && e->vx==vx && e->vy==vy && e->x==xx && e->y==yy);
        ticks(e,fps/2);
        assert(e->mode==(dash ? BOSS_RECOVER : BOSS_TELEGRAPH));
    }
    const s16 rx=e->x,ry=e->y;
    assert(e->retarget==6*fps/5 && !e->shielded && ENEMYBOSS_stationary(e));
    ticks(e,6*fps/5-1);assert(e->mode==BOSS_RECOVER && e->x==rx && e->y==ry && !volleys);
    tick(e);assert(e->mode==BOSS_RANGED && !e->shielded);
    room=4;tick(e);assert(!volleys && !e->fireTimer && !(e->tB&BOSS_NARROW_FAN));
    room=5;tick(e);assert(volleys==1 && widths[0]==2);
    ticks(e,6*fps/5+1);assert(volleys==2 && widths[1]==6);
    ticks(e,6*fps/5+1);assert(volleys==3 && widths[2]==2);
    // No periodic armor returns during a later15s shield window.
    e->tA=12*fps;tick(e);assert(!e->shielded && pulses==1);
}
static void summons(void)
{
    Enemy *e=reset(25);
    for(unsigned wave=1;wave<=6;wave++) {
        e->tA=10*fps-1;tick(e);assert(hunters()==2);
    }
    enemies[1].active=FALSE;e->tA=10*fps-1;tick(e);assert(hunters()==2);
    e->hp=12;tick(e);assert(hunters()==2);
    e->tA=10*fps-1;tick(e);assert(hunters()==2);
}
static void phase1(void)
{
    Enemy *e=reset(25);e->tA=12*fps-1;tick(e);assert(e->shielded);
    e->tA=15*fps-1;tick(e);assert(!e->shielded);
    volleys=0;e->tA=4*fps;e->fireTimer=0;room=4;tick(e);assert(!volleys && !e->fireTimer);
    room=5;tick(e);assert(volleys==1 && widths[0]==3);
    e=reset(1);tick(e);assert(e->mode==BOSS_TRANSITION && pulses==1);
}
int main(void)
{
    for(fps=50;fps<=60;fps+=10) {
        phase2();summons();phase1();
        printf("%uHz: phase threshold/latch, local flash, exact warnings and double dash,1.2s recovery, alternating full fans, no armor, two hunters and phase1 regression passed.\n",fps);
    }
}
