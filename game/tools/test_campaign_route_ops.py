"""Host contract checks for the actual6B operation C code, independent of VDP.

The source under test is included unchanged. Only hardware/rendering services
are stubs; the pressure, contact, shot, timing and work-position logic is real.
"""
from pathlib import Path
import subprocess,tempfile
GAME=Path(__file__).resolve().parents[1]
HEADERS=['genesis.h','levels/campaign_route_ops.h','levels/campaign_routes.h','levels/levels.h','levels/graph.h','core/objective.h','core/game.h','actors/player.h','actors/dinorah.h','system/video/objectivegfx.h','system/video/markers.h','system/video/spritelist.h','system/video/screens/hud.h','system/video/sprites/tiles.h','system/audio/sfx.h']
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
#define N_6A 7
#define N_6B 8
#define HUD_HEIGHT 24
#define PAL1 1
#define SPRITE_SIZE(w,h) 0
#define TILE_ATTR_FULL(a,b,c,d,e) e
#define OART_GATE 5
#define OART_VALVE 4
#define SFX_AMB_LAVA 0
#define TILE_BOMB_ICON 1
#define TILE_ICON_SHOTS 3
#define TILE_CLOCK 2
typedef struct{s16 x,y,w,h;bool blocksShots;}ArenaRect;
typedef struct{s16 x,y;u8 pauseSeconds;}RoutePoint;
typedef struct{int dummy;}RouteDef;
typedef struct{const RouteDef*route;}LevelDef;
typedef struct{u16 work[2],steamClock,damageTimer;u8 gateHp[2],pressureMask;u16 gateClearTicks[2];}CampaignRouteOperations;
extern CampaignRouteOperations campaignRouteOps;
static RouteDef CAMPAIGN_ROUTE06A,CAMPAIGN_ROUTE06B,otherRoute;
static ArenaRect CAMPAIGN_ROUTE06_gates[2]={{1008,160,32,64,1},{2032,160,32,64,1}};
static RoutePoint CAMPAIGN_ROUTE06B_valves[2]={{968,176,0},{1992,176,0}};
static u8 currentLevel=8;static u16 fps=60,joy=0;static s16 px=48,py=160,cameraX=0,cameraY=0;static int damage,activations,restores,hidden[2];
static u16 loadedMask,lastBar,lastSpriteY,barCalls,gatePlaces,valvePlaces;static const char *lastLabel;
static u16 divu(u32 a,u16 b){return a/b;}
static u16 ARENA_workBar(u16 value,u16 max){lastBar=value;barCalls++;return 1421;}
static bool SPRITES_emit(u16 *n,s16 x,s16 y,u8 size,u16 attr){lastSpriteY=y;(*n)++;return TRUE;}
static LevelDef level={&CAMPAIGN_ROUTE06B};
static const LevelDef*LEVEL_current(void){return &level;}
static bool OBJECTIVEGFX_startCampaign(u16 x){loadedMask=x;return x!=0;}
static void OBJECTIVEGFX_place(u8 a,u8 b,s16 c,s16 d,bool e){if(b==OART_GATE)gatePlaces++;if(b==OART_VALVE)valvePlaces++;}
static void OBJECTIVEGFX_prime(u8 a,bool b){}
static void OBJECTIVEGFX_activate(u8 a){activations++;}
static void OBJECTIVEGFX_hide(u8 a){assert(a<2);hidden[a]++;}
static void OBJECTIVEGFX_ground(bool a){}
static void OBJECTIVEGFX_update(void){}
static void OBJECTIVEGFX_draw(u16*a){}
static void MARKERS_alert(u16*a,s16 b,s16 c){}
static void MARKERS_destination(u16*a,s16 b,s16 c){}
static u8 shootHits;static int shootBadges;
static void MARKERS_shoot(u16*a,s16 b,s16 c,u8 hits){shootHits=hits;shootBadges++;}
static void SFX_playerHit(void){}
static void SFX_ambient(u8 a){}
static void sfxItemPickup(void){}
static void damagePlayer(u16 x){damage+=x;}
static u16 JOY_readJoypad(u8 x){return joy;}
static void OBJECTIVE_forceHUD(u16 x){restores++;}
static void HUD_drawObjective(const char*a,u16 b,const char*c,u16 d,const char*e){lastLabel=a;}
#endif
'''
MAIN=r'''
int main(void){
 // Equivalent narrow overlap across the complete authored relative range.
 ArenaRect rect={1000,160,16,64,1};
 for(int x=-4096;x<=4096;x++)for(int w=8;w<=32;w+=8){
  bool expected=x<rect.x+rect.w && x+w>rect.x;
  assert(overlap(&rect,x,176,w,16)==expected);
 }
 for(int y=-4096;y<=4096;y++)for(int h=8;h<=32;h+=8){
  bool expected=y<rect.y+rect.h && y+h>rect.y;
  assert(overlap(&rect,1008,y,8,h)==expected);
 }

 for(u16 rate=50;rate<=60;rate+=10){
  fps=rate;level.route=&CAMPAIGN_ROUTE06B;currentLevel=8;CR_OPS_start();
  assert(CR_OPS_active());assert(loadedMask==((1u<<OART_GATE)|(1u<<OART_VALVE)));
  assert(CR_OPS_blocked(1000,176,16,16));
  assert(!CR_OPS_blocked(992,176,16,16));
  for(int i=0;i<16;i++)assert(CR_OPS_shotBlocked(1008,176,true));
  assert(campaignRouteOps.gateHp[0]==4); // shooting before pressure is safe
  px=960;py=192;joy=BUTTON_A;
  for(int i=0;i<fps*2;i++)CR_OPS_update();
  assert(campaignRouteOps.work[0]==0); // combat cannot operate the valve
  shootBadges=0;cameraX=900;u16 noShots=0;CR_OPS_draw(&noShots);assert(shootBadges==0);cameraX=0;
  joy=0;for(int i=0;i<fps/2;i++)CR_OPS_update();
  assert(campaignRouteOps.work[0]==fps/2);
  cameraX=900;u16 sprites=0;barCalls=0;CR_OPS_draw(&sprites);
  assert(barCalls==1 && lastBar>=30 && lastBar<=35 && lastSpriteY==148);
  assert(CR_OPS_drawHUD() && !strcmp(lastLabel,"ABRINDO"));
  joy=BUTTON_A;assert(CR_OPS_drawHUD() && !strcmp(lastLabel,"VÁLVULA"));joy=0;
  cameraX=0;px=800;for(int i=0;i<fps;i++)CR_OPS_update();
  assert(campaignRouteOps.work[0]==fps/2); // retreat preserves progress
  px=960;for(int i=0;i<fps;i++)CR_OPS_update();
  assert(campaignRouteOps.pressureMask==1);assert(CR_OPS_drawHUD());
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
  assert(!CR_OPS_drawHUD());px=1400;assert(!CR_OPS_drawHUD());assert(restores>0);
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
  level.route=&CAMPAIGN_ROUTE06A;currentLevel=N_6A;valvePlaces=gatePlaces=0;CR_OPS_start();
  assert(CR_OPS_active() && campaignRouteOps.pressureMask==3);
  assert(loadedMask==(1u<<OART_GATE) && gatePlaces==2 && valvePlaces==0);
  assert(CR_OPS_gateBlockMask()==3);
  cameraX=900;shootBadges=0;u16 hints=0;CR_OPS_draw(&hints);assert(shootBadges==1 && shootHits==0);
  assert(CR_OPS_shotBlocked(1008,176,true));CR_OPS_draw(&hints);assert(shootHits==1);
  CR_OPS_start();cameraX=0;
  px=1000;py=176;damage=0;
  for(int n=0;n<fps*4;n++)CR_OPS_update();
  assert(damage==0 && campaignRouteOps.work[0]==0 && campaignRouteOps.work[1]==0);
  assert(campaignRouteOps.steamClock==0);
  assert(CR_OPS_shotBlocked(1008,176,false));assert(campaignRouteOps.gateHp[0]==4);
  for(int n=0;n<4;n++)assert(CR_OPS_shotBlocked(1008,176,true));
  assert(CR_OPS_blocked(1008,176,16,16));
  for(int n=0;n<fps*4/5;n++)CR_OPS_update();
  assert(!CR_OPS_blocked(1008,176,16,16) && CR_OPS_gateBlockMask()==2);
  char prep[64];assert(CR_OPS_prepText(prep,&level) && strstr(prep,"PORTÕES") && !strstr(prep,"VÁLVULAS"));
  level.route=&otherRoute;currentLevel=9;assert(!CR_OPS_active());assert(!CR_OPS_blocked(1008,176,16,16));assert(!CR_OPS_shotBlocked(1008,176,true));
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
