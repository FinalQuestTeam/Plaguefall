#include <assert.h>
#include <stdio.h>
#include "actors/player.h"
#include "actors/shots.h"
#include "core/game.h"
#include "core/stats.h"
#include "enemies/enemies.h"
#include "levels/levels.h"
#include "system/video/projection.h"

u16 fps;
bool gameOver,arenaActive;
s16 arenaMinX=8,arenaMinY=32,arenaMaxX=503,arenaMaxY=375;
u8 currentLevel=1,testStage;
PhaseStats phaseStats;
Enemy enemies[MAX_ENEMIES];
static LevelDef level;
static u16 testCap;
static unsigned sounds;

const LevelDef *LEVEL_current(void){return &level;}
u16 TEST_shotLimit(void){return testCap;}
bool TEST_noDefeat(void){return false;}
s16 ARENA_startX(void){return 80;}
s16 ARENA_startY(void){return 160;}
void ARENA_move(s32 *x,s32 *y,s16 dx,s16 dy,u16 size){(void)size;*x+=dx;*y+=dy;}
bool ARENA_playerShotBlocked(s16 x,s16 y){return x<8||x>496||y<32||y>368;}
void HUD_drawLife(s16 life){(void)life;}
void VDP_drawText(const char *s,u16 x,u16 y){(void)s;(void)x;(void)y;}
void SFX_playerHit(void){}
void SFX_playerShot(void){sounds++;}
u8 HERO_direction(s16 x,s16 y){(void)x;(void)y;return 0;}
void HERO_prepare(u8 dir){(void)dir;}
void HERO_muzzle(s16 *x,s16 *y){*x=px+8;*y=py-VIDEO_HEIGHT_OFFSET;}
u32 getApproximatedDistance(s16 x,s16 y)
{
    const u32 ax=abs(x),ay=abs(y),max=ax>ay?ax:ay,min=ax>ay?ay:ax;
    return (max*246+min*102)>>8; // mesmos coeficientes do SGDK
}
u16 ENEMIES_damageBox(s16 x,s16 y,u16 w,u16 h,u8 status){(void)x;(void)y;(void)w;(void)h;(void)status;return ENEMY_HIT_NONE;}
u16 ENEMIES_chainDamage(s16 x,s16 y,u8 count,u16 range){(void)x;(void)y;(void)count;(void)range;return 0;}

static void reset(u8 power,u8 cap)
{
    SHOTS_clear();SHOTS_resetPower();SHOTS_resetChain();
    PLAYER_reset();PLAYER_resetSpeed();PLAYER_fullHp();PLAYER_update(0);
    for(u8 i=1;i<power;i++)SHOTS_addPower();
    level.shotCap=cap;testCap=cap;sounds=0;
}

static void expectVolley(u8 power,u16 cap,u8 mode)
{
    const s32 fx=(px+4)*64,fy=(py-4)*64;
    s32 spd=PSHOT_SPEED*64;
    spd=spd*(100+PLAYER_speedBonus())/100;
    const s16 dx=faceX*64,dy=faceY*64;
    const s32 mag=getApproximatedDistance(dx,dy);
    const s32 vx=dx*spd/mag,vy=dy*spd/mag;
    u8 found=0;
    for(u16 i=0;i<MAX_PSHOTS;i++)if(pshots[i].active) {
        assert(i<cap);
        if(pshots[i].x!=fx||pshots[i].y!=fy)continue;
        assert(pshots[i].mode==mode&&pshots[i].renderPose==0);
        for(s16 o=1-power;o<power;o+=2)
            if(pshots[i].vx==vx-vy*o/SHOTS_ARC_SHEAR &&
               pshots[i].vy==vy+vx*o/SHOTS_ARC_SHEAR) {
                const u8 bit=1u<<((o+power-1)/2);
                assert(!(found&bit));found|=bit;
            }
    }
    if(found!=(1u<<power)-1) {
        fprintf(stderr,"%uHz power %u cap %u: incomplete volley, mask %u\n",fps,power,cap,found);
        assert(found==(1u<<power)-1);
    }
}

static void autofire(void)
{
    const s16 dirs[8][2]={{1,0},{1,1},{0,1},{-1,1},{-1,0},{-1,-1},{0,-1},{1,-1}};
    const u8 caps[]={6,16,0};
    for(u8 c=0;c<3;c++)for(u8 power=1;power<=SHOTS_MAX_POWER;power++)
    for(u8 d=0;d<8;d++)for(u8 speed=0;speed<=5;speed++) {
        reset(power,caps[c]);
        for(u8 i=0;i<speed;i++)PLAYER_addSpeed();
        faceX=dirs[d][0];faceY=dirs[d][1];
        const unsigned interval=PLAYER_FIRE_TENTHS*fps/10;
        for(unsigned frame=0;frame<interval*8;frame++) {
            const unsigned before=sounds;
            PLAYER_update(BUTTON_A);
            if(frame%interval==0) {
                assert(sounds==before+1);
                expectVolley(power,caps[c]?caps[c]:MAX_PSHOTS,SHOTMODE_NONE);
            }else assert(sounds==before);
            SHOTS_updatePlayer();
        }
    }
}

static void saturatedAndFragmented(void)
{
    for(u8 training=0;training<=1;training++)for(u8 cap=6;cap<=16;cap+=10)
    for(u8 power=1;power<=SHOTS_MAX_POWER;power++) {
        currentLevel=training?0:1;
        reset(power,cap);
        // No free slots: every direction must still be emitted, charges once.
        for(u16 i=0;i<cap;i++) {
            pshots[i].active=true;pshots[i].x=400*64;pshots[i].renderPose=0xff;
        }
        SHOTS_setMode(SHOTMODE_ICE,2);
        SHOTS_firePlayer();expectVolley(power,cap,SHOTMODE_ICE);
        assert(sounds==1&&SHOTS_modeCharges()==1);
        SHOTS_updatePlayer();SHOTS_firePlayer();expectVolley(power,cap,SHOTMODE_ICE);
        assert(sounds==2&&SHOTS_modeCharges()==0&&SHOTS_mode()==SHOTMODE_NONE);
        // Enough fragmented holes: existing shots must survive unchanged.
        reset(power,cap);
        for(u16 i=0;i<cap;i++) {
            pshots[i].active=true;pshots[i].x=400*64;
        }
        for(u16 i=0;i<power;i++)pshots[(i*5)%cap].active=false;
        bool kept[MAX_PSHOTS];
        for(u16 i=0;i<cap;i++)kept[i]=pshots[i].active;
        SHOTS_firePlayer();expectVolley(power,cap,SHOTMODE_NONE);
        for(u16 i=0;i<cap;i++)if(kept[i])assert(pshots[i].active&&pshots[i].x==400*64);
    }
    currentLevel=0;reset(5,0);SHOTS_setMode(SHOTMODE_FIRE,2);
    SHOTS_firePlayer();
    for(u16 i=0;i<MAX_PSHOTS;i++)assert(!pshots[i].active);
    assert(!sounds&&SHOTS_modeCharges()==2);
    currentLevel=1;
}

static void everyOccupancy(void)
{
    for(u8 cap=6;cap<=16;cap+=10)for(u8 power=1;power<=SHOTS_MAX_POWER;power++) {
        reset(power,cap);
        for(u32 mask=0;mask<(1u<<cap);mask++) {
            SHOTS_clear();
            u16 free=cap;
            for(u16 i=0;i<cap;i++)if(mask&(1u<<i)) {
                pshots[i].active=true;pshots[i].x=400*64;free--;
            }
            SHOTS_firePlayer();expectVolley(power,cap,SHOTMODE_NONE);
            u16 active=0,kept=0;
            for(u16 i=0;i<cap;i++)if(pshots[i].active) {
                active++;kept+=pshots[i].x==400*64;
            }
            assert(active==(free>=power ? cap-free+power : cap));
            assert(kept==(free>=power ? cap-free : cap-power));
        }
    }
}

int main(void)
{
    for(fps=50;fps<=60;fps+=10) {
        autofire();saturatedAndFragmented();everyOccupancy();
        printf("%uHz: complete volleys at powers 1..5, eight directions, all speed bonuses, caps 6/16/default, every pool occupancy and special charges passed.\n",fps);
    }
    return 0;
}
