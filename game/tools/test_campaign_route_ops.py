"""Host contract checks for the actual6B operation C code, independent of VDP.

The source under test is included unchanged. Only hardware/rendering services
are stubs; the pressure, contact, shot, timing and work-position logic is real.
"""
from pathlib import Path
import subprocess,tempfile
GAME=Path(__file__).resolve().parents[1]
HEADERS=['genesis.h','levels/campaign_route_ops.h','levels/campaign_routes.h','levels/levels.h','levels/graph.h','core/objective.h','core/game.h','actors/player.h','actors/dinorah.h','system/video/objectivegfx.h','system/video/markers.h','system/video/screens/hud.h','system/video/sprites/tiles.h','system/audio/sfx.h']
COMMON=r'''
#ifndef FAKE_API
#define FAKE_API
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;typedef int16_t s16;
#define TRUE true
#define FALSE false
#define JOY_1 0
#define BUTTON_A 1
#define N_6B 8
#define OART_GATE 5
#define OART_VALVE 4
#define SFX_AMB_LAVA 0
#define TILE_BOMB_ICON 1
#define TILE_CLOCK 2
typedef struct{s16 x,y,w,h;bool blocksShots;}ArenaRect;
typedef struct{s16 x,y;u8 pauseSeconds;}RoutePoint;
typedef struct{int dummy;}RouteDef;
typedef struct{const RouteDef*route;}LevelDef;
typedef struct{u16 work[2],steamClock,damageTimer;u8 gateHp[2],pressureMask;u16 gateClearTicks[2];}CampaignRouteOperations;
extern CampaignRouteOperations campaignRouteOps;
static RouteDef CAMPAIGN_ROUTE06B,otherRoute;
static ArenaRect CAMPAIGN_ROUTE06B_gates[2]={{1008,160,32,64,1},{2032,160,32,64,1}};
static RoutePoint CAMPAIGN_ROUTE06B_valves[2]={{968,176,0},{1992,176,0}};
static u8 currentLevel=8;static u16 fps=60,joy=0;static s16 px=48,py=160;static int damage,activations,restores,hidden[2];
static LevelDef level={&CAMPAIGN_ROUTE06B};
static const LevelDef*LEVEL_current(void){return &level;}
static bool OBJECTIVEGFX_startCampaign(u16 x){return x!=0;}
static void OBJECTIVEGFX_place(u8 a,u8 b,s16 c,s16 d,bool e){}
static void OBJECTIVEGFX_prime(u8 a,bool b){}
static void OBJECTIVEGFX_activate(u8 a){activations++;}
static void OBJECTIVEGFX_hide(u8 a){assert(a<2);hidden[a]++;}
static void OBJECTIVEGFX_ground(bool a){}
static void OBJECTIVEGFX_update(void){}
static void OBJECTIVEGFX_draw(u16*a){}
static void MARKERS_alert(u16*a,s16 b,s16 c){}
static void MARKERS_destination(u16*a,s16 b,s16 c){}
static void SFX_playerHit(void){}
static void SFX_ambient(u8 a){}
static void sfxItemPickup(void){}
static void damagePlayer(u16 x){damage+=x;}
static u16 JOY_readJoypad(u8 x){return joy;}
static void OBJECTIVE_forceHUD(u16 x){restores++;}
static void HUD_drawObjective(const char*a,u16 b,const char*c,u16 d,const char*e){}
#endif
'''
MAIN=r'''
int main(void){
 for(u16 rate=50;rate<=60;rate+=10){
  fps=rate;level.route=&CAMPAIGN_ROUTE06B;currentLevel=8;CR_OPS_start();
  assert(CR_OPS_active());
  assert(CR_OPS_blocked(1000,176,16,16));
  assert(!CR_OPS_blocked(992,176,16,16));
  for(int i=0;i<16;i++)assert(CR_OPS_shotBlocked(1008,176,true));
  assert(campaignRouteOps.gateHp[0]==4); // shooting before pressure is safe
  px=960;py=192;joy=BUTTON_A;
  for(int i=0;i<fps*2;i++)CR_OPS_update();
  assert(campaignRouteOps.work[0]==0); // combat cannot operate the valve
  joy=0;for(int i=0;i<fps/2;i++)CR_OPS_update();
  assert(campaignRouteOps.work[0]==fps/2);
  px=800;for(int i=0;i<fps;i++)CR_OPS_update();
  assert(campaignRouteOps.work[0]==fps/2); // retreat preserves progress
  px=960;for(int i=0;i<fps;i++)CR_OPS_update();
  assert(campaignRouteOps.pressureMask==1);CR_OPS_drawHUD();
  for(int i=0;i<3;i++){assert(CR_OPS_shotBlocked(1008,176,true));assert(CR_OPS_blocked(1008,176,16,16));}
  assert(CR_OPS_shotBlocked(1008,176,false)); // sight checks cannot finish gate
  assert(campaignRouteOps.gateHp[0]==1);
  assert(CR_OPS_shotBlocked(1008,176,true));
  assert(CR_OPS_blocked(1008,176,16,16));
  assert(campaignRouteOps.gateClearTicks[0]==fps*4/5);
  assert(CR_OPS_shotBlocked(1008,176,true));
  for(int i=0;i<fps*4/5-1;i++)CR_OPS_update();
  assert(CR_OPS_blocked(1008,176,16,16));
  CR_OPS_update();assert(!CR_OPS_blocked(1008,176,16,16));
  assert(!CR_OPS_shotBlocked(1008,176,true));assert(hidden[0]>0);
  assert(campaignRouteOps.gateHp[1]==4); // second gate independent
  CR_OPS_drawHUD();px=1400;CR_OPS_drawHUD();assert(restores>0);
  px=2010;py=184;damage=0;campaignRouteOps.steamClock=0;
  for(int i=0;i<fps-1;i++)CR_OPS_update();assert(damage==0);
  CR_OPS_update();assert(damage==5); // exactly one second of warning
  px=1984;py=192;damage=0;joy=BUTTON_A;
  for(int i=0;i<fps*4;i++)CR_OPS_update();assert(damage==0); // safe work pocket
  joy=0;for(int i=0;i<fps*3/2;i++)CR_OPS_update();
  assert(campaignRouteOps.pressureMask==3);
  for(int i=0;i<4;i++)assert(CR_OPS_shotBlocked(2032,176,true));
  assert(CR_OPS_blocked(2032,176,16,16));
  for(int i=0;i<fps*4/5;i++)CR_OPS_update();
  assert(!CR_OPS_blocked(2032,176,16,16));assert(hidden[1]>0);
  CR_OPS_start();assert(campaignRouteOps.pressureMask==0 && campaignRouteOps.gateHp[0]==4);
  level.route=&otherRoute;currentLevel=7;assert(!CR_OPS_active());assert(!CR_OPS_blocked(1008,176,16,16));assert(!CR_OPS_shotBlocked(1008,176,true));
  currentLevel=0;assert(!CR_OPS_active());
  printf("PASS %uHz pressure,4-shot gates,0.8s collapse-before-clear,read-only probes,persistent work,warning,safe pocket,reset,isolation\n",rate);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='campaign-route-contract-') as directory:
 root=Path(directory)
 for path in HEADERS:
  p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('#include "fake_api.h"\n')
 (root/'fake_api.h').write_text(COMMON)
 (root/'test.c').write_text('#include "'+str(GAME/'src/levels/campaign_route_ops.c')+'"\n'+MAIN)
 subprocess.run(['clang','-std=c99','-Werror=implicit-function-declaration','-I'+str(root),str(root/'test.c'),'-o',str(root/'test')],check=True)
 subprocess.run([str(root/'test')],check=True)
