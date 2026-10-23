
#include <assert.h>
#include <stdio.h>
#include "core/game.h"
#include "core/death.h"
#include "core/inventory.h"
#include "core/stats.h"
#include "actors/player.h"
#include "actors/shots.h"
#include "actors/bomb.h"
#include "items/items.h"
#include "levels/graph.h"
#include "enemies/enemies.h"

u16 fps=60;bool gameOver,arenaActive;
s16 arenaMinX=8,arenaMinY=32,arenaMaxX=311,arenaMaxY=215;
u8 currentLevel;
PhaseStats phaseStats;
FShot pshots[MAX_PSHOTS],eshots[MAX_ESHOTS];
static LevelDef level;
static TileRect lava={18,15,5,6};
static bool obstruction;
static unsigned pickups;
const LevelDef *LEVEL_current(void){return &level;}
s16 ARENA_startX(void){return 100;}s16 ARENA_startY(void){return 100;}
void ARENA_move(s32 *x,s32 *y,s16 dx,s16 dy,u16 size){(void)size;*x+=dx;*y+=dy;}
bool ARENA_blocked(s16 x,s16 y,u16 w,u16 h){
    return x<8||y<32||x+w-1>311||y+h-1>215||
        (obstruction && x<192&&x+16>144&&y<176&&y+16>120);
}
void ARENA_damageChurch(void){}
bool ARENA_playerShotBlocked(s16 x,s16 y){(void)x;(void)y;return false;}
void HUD_drawLife(s16 life){(void)life;}
void VDP_drawText(const char *s,u16 x,u16 y){(void)s;(void)x;(void)y;}
void SFX_playerHit(void){}void SFX_playerShot(void){}void SFX_bombBlast(void){}
void FLASH_trigger(void){}void sfxItemPickup(void){pickups++;}
void OBJECTIVE_addCollected(u8 type){(void)type;}
bool TEST_noDefeat(void){return false;}u16 TEST_shotLimit(void){return MAX_PSHOTS;}
u8 HERO_direction(s16 x,s16 y){(void)x;(void)y;return 0;}
void HERO_prepare(u8 dir){(void)dir;}void HERO_muzzle(s16 *x,s16 *y){*x=px;*y=py;}
u32 getApproximatedDistance(s16 x,s16 y){return abs(x)+abs(y);}
u16 ENEMIES_damageBox(s16 x,s16 y,u16 w,u16 h,u8 s){(void)x;(void)y;(void)w;(void)h;(void)s;return 0;}
u16 ENEMIES_chainDamage(s16 x,s16 y,u8 n,u16 r){(void)x;(void)y;(void)n;(void)r;return 0;}
u16 ENEMIES_killAll(void){return 0;}
const EnemyDef dummy={100};const EnemyDef *const ENEMY_DEFS[]={&dummy};
u16 test_random(void){static u16 r;return r++;}
bool SPRITES_emit(u16 *n,s16 x,s16 y,u8 s,u16 a){(void)x;(void)y;(void)s;(void)a;(*n)++;return true;}

static unsigned inventoryCount(void){unsigned count=0;u8 type,n;for(u8 i=1;i<INV_POS;i++){INV_view(i,&type,&n);count+=type!=INV_EMPTY;}return count;}
static unsigned bags(void){unsigned n=0;for(u8 i=0;i<MAX_ITEMS;i++)n+=items[i].active&&items[i].type==ITEM_BAG;return n;}
static Item *bag(void){for(u8 i=0;i<MAX_ITEMS;i++)if(items[i].active&&items[i].type==ITEM_BAG)return &items[i];return NULL;}
static void seed(u8 node){
    DEATH_reset();ITEMS_clear();INV_clear();BOMB_reset();PLAYER_reset();PLAYER_fullHp();
    SHOTS_resetPower();PLAYER_resetSpeed();currentLevel=node;gameOver=false;pickups=0;
    for(u8 i=0;i<4;i++)SHOTS_addPower();for(u8 i=0;i<5;i++)PLAYER_addSpeed();
    INV_add(ITEM_SHIELD);INV_add(ITEM_CHAIN);INV_add(ITEM_ICE);
    SHOTS_setMode(SHOTMODE_ICE,3);PLAYER_grantShield();
}
static void restart(u8 node){PLAYER_reset();ITEMS_clear();DEATH_startPhase(node);assert(bags()==1);}
static void collect(void){assert(bag());px=bag()->x;py=bag()->y;ITEMS_update();}
static void die(u8 node){DEATH_capture(node,160,140);hp=0;DEATH_retry(node,160,140);restart(node);}
static void allNodes(void){
    for(u8 node=N_1;node<NODE_MAX;node++){
        seed(node);const u16 shield=PLAYER_shieldRemaining();
        die(node);
        assert(hp==100&&SHOTS_power()==1&&PLAYER_speedBonus()==0&&!inventoryCount()&&!BOMB_count());
        assert(SHOTS_mode()==SHOTMODE_NONE&&!SHOTS_modeCharges()&&!PLAYER_shieldRemaining());
        assert(bag()->ttl==ITEM_TTL_FOREVER);
        for(unsigned i=0;i<70000;i++)ITEMS_update();assert(bags()==1);
        collect();assert(!bags()&&pickups==1);
        if(node<=N_5){assert(SHOTS_power()==5&&PLAYER_speedBonus()==100&&inventoryCount()==3&&BOMB_count()==2);}
        else if(node<=N_11){assert(SHOTS_power()==4&&PLAYER_speedBonus()==80&&inventoryCount()==2&&BOMB_count()==2);}
        else{assert(SHOTS_power()==2&&PLAYER_speedBonus()==20&&!inventoryCount()&&!BOMB_count());}
        assert(SHOTS_mode()==(node<=N_11?SHOTMODE_ICE:SHOTMODE_NONE));
        assert(SHOTS_modeCharges()==(node<=N_11?3:0));
        assert(PLAYER_shieldRemaining()==(node<=N_11?shield:0));
        const u8 power=SHOTS_power(),speed=PLAYER_speedBonus();
        ITEMBAG_apply();ITEMS_update();assert(SHOTS_power()==power&&PLAYER_speedBonus()==speed&&pickups==1);
        ITEMS_clear();DEATH_startPhase(node);assert(!bags());
    }
}
static void repeatedDeaths(void){
    seed(N_6A);
    const u8 power[]={4,3,2,1,1,1},speed[]={80,60,40,20,0,0},count[]={2,1,0,0,0,0},bomb[]={2,2,2,1,0,0};
    for(u8 i=0;i<6;i++){
        die(N_6A);collect();assert(!bags());
        assert(SHOTS_power()==power[i]&&PLAYER_speedBonus()==speed[i]&&inventoryCount()==count[i]&&BOMB_count()==bomb[i]);
    }
    // The old floor at 3 is gone: even the last earned improvement is lost.
    seed(N_6B);SHOTS_resetPower();SHOTS_addPower();PLAYER_resetSpeed();PLAYER_addSpeed();
    die(N_6B);collect();assert(SHOTS_power()==1&&PLAYER_speedBonus()==0);
    seed(N_11);die(N_11);collect();u8 t,n;
    INV_view(1,&t,&n);assert(t==ITEM_SHIELD&&n==1);INV_view(2,&t,&n);assert(t==ITEM_CHAIN&&n==5);
    INV_view(3,&t,&n);assert(t==INV_EMPTY);
    // Dying before reaching the old bag captures the new, empty equipment.
    seed(N_1);die(N_1);die(N_1);collect();
    assert(SHOTS_power()==1&&PLAYER_speedBonus()==0&&!inventoryCount()&&!BOMB_count());
    seed(N_12);die(N_12);DEATH_capture(N_12,210,180);DEATH_retry(N_12,210,180);restart(N_12);
    assert(bag()->x==210&&bag()->y==180);collect();assert(SHOTS_power()==1&&PLAYER_speedBonus()==0);
}
static void conditionalAndSnapshot(void){
    for(u8 power=1;power<=5;power++)for(u8 speed=0;speed<=5;speed++){
        seed(N_16);SHOTS_resetPower();PLAYER_resetSpeed();
        for(u8 i=1;i<power;i++)SHOTS_addPower();for(u8 i=0;i<speed;i++)PLAYER_addSpeed();
        die(N_16);collect();
        assert(SHOTS_power()==(power>1?2:1));assert(PLAYER_speedBonus()==(speed?20:0));
    }
    seed(N_1);DEATH_capture(N_1,160,140);
    // Rendering/menus or other changes after capture cannot alter its contents.
    INV_clear();BOMB_clear();SHOTS_resetPower();PLAYER_resetSpeed();SHOTS_resetChain();PLAYER_restoreShield(0);
    DEATH_retry(N_1,250,190);restart(N_1);assert(bag()->x==160&&bag()->y==140);
    collect();assert(SHOTS_power()==5&&PLAYER_speedBonus()==100&&inventoryCount()==3&&BOMB_count()==2);
    // New pickups do not create a recovery entitlement absent before death.
    seed(N_16);SHOTS_resetPower();PLAYER_resetSpeed();die(N_16);
    SHOTS_addPower();PLAYER_addSpeed();collect();assert(SHOTS_power()==2&&PLAYER_speedBonus()==20);
    // New pickups survive recovery, caps hold, and a full inventory leaves
    // the original items in the bag until there is room, without repeat rewards.
    seed(N_1);die(N_1);SHOTS_addPower();PLAYER_addSpeed();BOMB_add();INV_add(ITEM_FIRE);
    collect();assert(bags()==1&&SHOTS_power()==5&&PLAYER_speedBonus()==100&&BOMB_count()==3&&inventoryCount()==3);
    const unsigned sounds=pickups;ITEMS_update();assert(pickups==sounds&&bags()==1);
    INV_cycle();INV_activate();assert(inventoryCount()==2&&SHOTS_mode()==SHOTMODE_FIRE);
    ITEMS_update();assert(!bags()&&inventoryCount()==3&&SHOTS_mode()==SHOTMODE_FIRE);
    u8 type,charges;INV_view(1,&type,&charges);assert(type==ITEM_ICE&&charges==ICE_CHARGES);
}
static void placementAndDrops(void){
    seed(N_16);level.lava=&lava;level.lavaCount=1;obstruction=true;
    die(N_16);assert(!ARENA_blocked(bag()->x,bag()->y,16,16));
    assert(!(bag()->x<184&&bag()->x+16>144&&bag()->y<168&&bag()->y+16>120));
    level.lavaCount=0;obstruction=false;
    DEATH_capture(N_16,100,100);DEATH_retry(N_16,100,100);restart(N_16);
    ITEMS_update();assert(bags()==1); // not under the respawn
    DEATH_capture(N_16,-100,-100);DEATH_retry(N_16,-100,-100);restart(N_16);
    assert(!ARENA_blocked(bag()->x,bag()->y,16,16));
    DEATH_reset();ITEMS_clear();DEATH_startPhase(N_16);assert(!bags());
    seed(N_12);DEATH_capture(N_12,160,140);DEATH_retry(N_12,160,140);
    ITEMS_clear();DEATH_startPhase(N_13A);assert(!bags());
    for(unsigned i=0;i<2000;i++){
        ITEMS_clear();ITEMS_tryDrop(180,140,0);
        for(u8 j=0;j<MAX_ITEMS;j++)assert(!items[j].active||items[j].type<ITEM_DROP_TYPES);
    }
    ITEMS_clear();ITEMS_testEnsure();unsigned count=0;
    for(u8 i=0;i<MAX_ITEMS;i++)count+=items[i].active;
    assert(count==8&&!bags());
}
int main(void){
    for(fps=50;fps<=60;fps+=10){
        allNodes();repeatedDeaths();conditionalAndSnapshot();placementAndDrops();
        printf("%uHz: bag in all 20 nodes, pre-death snapshot, no floor, conditional final rewards, empty bag, capped/partial pickup, replacement and safe placement passed.\n",fps);
    }
    return 0;
}
