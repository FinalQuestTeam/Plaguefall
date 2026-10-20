// Compile the actual simulation and weapon code, with only hardware/AV mocked.
#include <assert.h>
#include <stdio.h>
#include "enemies/enemies.c"
#include "actors/shots.c"
#include "actors/shots_player.c"
#include "system/video/enemygfx.c"
#include "system/video/projection.h"

const u32 insect_frames[ENEMY_ASSET_LONGWORDS]={0};
const u32 insect_icons[15*128]={0};
s16 px=150,py=100,faceX=1,faceY=0,hp=100;
u16 fps=60,ENEMY_CD=120;
bool gameOver=false,bossDefeated=false;
static u8 speedBonus;
static unsigned drops,blood,arcs,cases;
u16 random(void){return 1;}
u32 getApproximatedDistance(s16 x,s16 y){u16 a=x<0?-x:x,b=y<0?-y:y;return a>b?a+(b>>1):b+(a>>1);}
void damagePlayer(u16 damage){hp-=damage;}
u8 PLAYER_speedBonus(void){return speedBonus;}
void SFX_playerShot(void){}
void BLOOD_splat(s16 x,s16 y){blood++;}
void ITEMS_tryDrop(s16 x,s16 y,u8 type){drops++;}
void CHAINFX_reset(void){}
void CHAINFX_add(s16 a,s16 b,s16 c,s16 d){arcs++;}
#define BEHAVIOR(name) void name(Enemy *e,const EnemyDef *def){}
BEHAVIOR(ENEMYRED_update)
BEHAVIOR(ENEMYYELLOW_update)
BEHAVIOR(ENEMYPURPLE_update)
BEHAVIOR(ENEMYORANGE_update)
BEHAVIOR(ENEMYDUMMY_update)
BEHAVIOR(ENEMYBOSS_update)
u16 DMA_getQueueTransferSize(void){return 0;}
u16 DMA_getQueueSize(void){return 0;}
u16 DMA_getMaxQueueSize(void){return 80;}
bool DMA_queueDma(u8 type,void *source,u16 dest,u16 words,u16 step){assert(dest+words*2<=(TILE_USER_INDEX+ENEMY_ICON_BASE)*32);return true;}
void VDP_loadTileData(const u32 *d,u16 t,u16 n,u8 m){}
void VDP_setTileMapXY(u16 p,u16 a,u16 x,u16 y){}

static void target(u8 type,s16 x,s16 y)
{
    ENEMIES_clear();ENEMYGFX_reset();SHOTS_clear();SHOTS_resetPower();SHOTS_resetChain();
    ENEMIES_spawnAt(type,x,y);enemies[0].hp=9;enemies[0].frozen=600;
    bossDefeated=false;drops=blood=arcs=0;
    ENEMYGFX_prepare(0);
}
static void bullet(s16 x,s16 y,u8 mode)
{
    pshots[0]=(FShot){.x=(s32)x*64,.y=(s32)y*64,.mode=mode,.active=true};
}
int main(void)
{
    static const s16 dirs[8][2]={{0,-1},{1,-1},{1,0},{1,1},{0,1},{-1,1},{-1,0},{-1,-1}};
    for(u8 type=0;type<ENEMY_TYPES;type++)
    {
        const s16 size=ENEMY_DEFS[type]->size;
        if(type<12 || type==14)assert(ENEMY_ART[type].size==size);
        for(u16 direction=0;direction<8;direction++)
        {
            // Edge grazing and misses, independently of animation/facing.
            const s16 points[9][2]={{-8,size/2},{size,size/2},{size/2,-8},{size/2,size},
                {-7,size/2},{size-1,size/2},{size/2,-7},{size/2,size-1},{size/2,size/2}};
            for(u16 point=0;point<9;point++)
            {
                target(type,120,100);enemies[0].frozen=0;
                px=120+size/2+dirs[direction][0]*60-8;
                py=100+size/2+dirs[direction][1]*60-8;
                ENEMYGFX_prepare(0);
                const s16 x=enemies[0].x+points[point][0],y=enemies[0].y+points[point][1];
                // Projection must preserve rectangle overlap exactly: this is
                // the rendered bullet/body relationship that previously differed.
                assert(VIDEO_PROJECT_Y(y)-VIDEO_PROJECT_Y(enemies[0].y)==points[point][1]);
                bullet(x,y,SHOTMODE_NONE);SHOTS_updatePlayer();
                bool hit=point>=4;
                assert(enemies[0].hp==(hit?8:9));assert(pshots[0].active==!hit);cases++;
            }
            // Actual fire + travel in all8 facings and both speed extremes.
            for(u8 boost=0;boost<2;boost++)
            {
                px=150;py=100;faceX=dirs[direction][0];faceY=dirs[direction][1];speedBonus=boost?100:0;
                const s16 cx=px+8+faceX*48,cy=py+8+faceY*48;
                target(type,cx-size/2,cy-size/2);SHOTS_firePlayer();
                for(u16 frame=0;frame<40 && pshots[0].active;frame++)SHOTS_updatePlayer();
                assert(enemies[0].hp==8 && !pshots[0].active);cases++;
            }
        }
        target(type,120,100);enemies[0].shielded=true;bullet(120+size/2,100+size/2,SHOTMODE_NONE);
        SHOTS_updatePlayer();assert(enemies[0].hp==9 && !pshots[0].active);cases++;
        target(type,120,100);enemies[0].frozen=0;bullet(120+size/2,100+size/2,SHOTMODE_ICE);
        SHOTS_updatePlayer();assert(enemies[0].hp==8 && enemies[0].frozen==ICE_FREEZE_SEC*fps);cases++;
        target(type,120,100);bullet(120+size/2,100+size/2,SHOTMODE_FIRE);
        SHOTS_updatePlayer();assert(enemies[0].hp==8 && enemies[0].burn==FIRE_BURN_SEC*fps);cases++;
        target(type,120,100);enemies[0].hp=1;bullet(120+size/2,100+size/2,SHOTMODE_NONE);
        assert(SHOTS_updatePlayer()==1 && !enemies[0].active && drops==1 && blood==1);
        assert(bossDefeated==(type==ENEMY_BOSS));cases++;
    }
    printf("{\"passed\":true,\"collision_cases\":%u,\"types\":15,\"directions\":8,\"native_size_and_projection\":true,\"shield_freeze_burn_and_death\":true}\n",cases);
}
