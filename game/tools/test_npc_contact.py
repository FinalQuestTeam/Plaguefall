"""Native regression of production npc.c; no ROM/core build or gameplay claims.

Checks the mapped Santa can be hit at the solid pedestal from every side,
keeps legacy contact rules, and permits both outcomes of the 30-second defense.
"""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STUBS = {
    'genesis.h': '''#ifndef GENESIS_H
#define GENESIS_H
#include <stdint.h>
#include <stdbool.h>
typedef int16_t s16; typedef uint16_t u16; typedef uint8_t u8;
#define TRUE true
#define FALSE false
#endif
''',
    'core/game.h': '''#include <genesis.h>
extern s16 arenaMinX,arenaMinY,arenaMaxX,arenaMaxY;
extern u16 fps;
#define INNER_MIN_X arenaMinX
#define INNER_MIN_Y arenaMinY
#define INNER_MAX_X arenaMaxX
#define INNER_MAX_Y arenaMaxY
''',
    'levels/arena.h': '''#include <genesis.h>
typedef struct {s16 x,y,w,h;bool blocksShots;} ArenaRect;
typedef struct {ArenaRect footprint;} ArenaNpcVisual;
bool ARENA_npcInMap(void);
const ArenaNpcVisual *ARENA_npcVisual(void);
''',
    'system/video/flash.h': 'void FLASH_trigger(void);\n',
    'system/video/screens/hud.h': '',
    'enemies/enemies.h': '''#ifndef ENEMIES_H
#define ENEMIES_H
#include <genesis.h>
#define MAX_ENEMIES 16
typedef struct {s16 x,y;u8 type;bool active;} Enemy;
typedef struct {u8 size,contactDmg;} EnemyDef;
extern Enemy enemies[MAX_ENEMIES];
extern EnemyDef enemyDef;
#define ENEMY_DEF(e) (&enemyDef)
#define ENEMY_SIZE(e) (enemyDef.size)
void ENEMIES_knockbackFrom(Enemy *e,s16 x,s16 y);
#endif
''',
}
TEST = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "actors/npc.h"
#include "enemies/enemies.h"
#include "levels/arena.h"
Enemy enemies[MAX_ENEMIES]; EnemyDef enemyDef={24,12};
s16 arenaMinX=16,arenaMinY=96,arenaMaxX=367,arenaMaxY=367;
u16 fps=60; static bool mapped=true; static int flash,knocks; static s16 hitX,hitY;
bool ARENA_npcInMap(void){return mapped;}
const ArenaNpcVisual *ARENA_npcVisual(void){static const ArenaNpcVisual v={{176,176,40,48,false}};return mapped ? &v : NULL;}
void FLASH_trigger(void){flash++;}
void ENEMIES_knockbackFrom(Enemy *e,s16 x,s16 y){(void)e;knocks++;hitX=x;hitY=y;}
static bool overlaps_stone(Enemy *e){return e->x<216&&e->x+enemyDef.size>176&&e->y<224&&e->y+enemyDef.size>176;}
static void reset(void){memset(enemies,0,sizeof enemies);flash=knocks=0;NPC_spawn(176,200,100);}
static Enemy *touch(int side){Enemy *e=&enemies[0];int sz=enemyDef.size;e->active=true;
 if(side==0){e->x=196-sz/2;e->y=(mapped?176:208)-sz;}
 if(side==1){e->x=216;e->y=220-sz/2;}
 if(side==2){e->x=196-sz/2;e->y=224;}
 if(side==3){e->x=176-sz;e->y=220-sz/2;}
 return e;
}
static void contact_sides(void){mapped=true;
 for(int sz=16;sz<=32;sz+=8){enemyDef.size=sz;
  for(int side=0;side<4;side++){reset();Enemy *e=touch(side);assert(!overlaps_stone(e));NPC_update();assert(npcHp==88);assert(flash==1&&knocks>=1);assert(hitX==196&&hitY==220);}
 }
 enemyDef.size=24;reset();Enemy *e=touch(3);e->x--;NPC_update();assert(npcHp==100); /* one-pixel gap */
 reset();e=touch(1);e->x++;NPC_update();assert(npcHp==100);
 enemyDef.contactDmg=0;reset();touch(3);NPC_update();assert(npcHp==100);enemyDef.contactDmg=12;
}
static void timer(int rate){fps=rate;mapped=true;enemyDef.size=24;reset();touch(3);NPC_update();assert(npcHp==88);
 const int inv=25*rate/10;
 for(int t=0;t<inv;t++){NPC_update();assert(npcHp==88);}
 NPC_update();assert(npcHp==76);
 reset();touch(3);int death=0;
 for(int t=0;t<30*rate;t++){NPC_update();if(!NPC_alive()){death=t+1;break;}}
 assert(death>0&&death<30*rate);assert(npcHp==0);printf("%d Hz mapped: nine contacts defeat objective at frame %d (<30 s).\n",rate,death);
 reset();for(int t=0;t<30*rate;t++)NPC_update();assert(NPC_alive()&&npcHp==100); /* protected */
 mapped=false;reset();assert(NPC_size()==24);touch(3);NPC_update();assert(npcHp==100); /* exact edge stays legacy */
 enemies[0].x++;NPC_update();assert(npcHp==88&&hitX==188&&hitY==212);
 for(int t=0;t<50*rate/10;t++){NPC_update();assert(npcHp==88);}NPC_update();assert(npcHp==76);
 reset();enemies[0]=(Enemy){176,200,0,true};for(int t=0;t<30*rate;t++)NPC_update();assert(NPC_alive()&&npcHp==28);
}
int main(void){contact_sides();timer(60);timer(50);mapped=true;NPC_spawn(0,0,0);assert(NPC_size()==40&&npcX==171&&npcY==211);mapped=false;NPC_spawn(0,0,0);assert(NPC_size()==24&&npcX==179&&npcY==219);NPC_clear();assert(!NPC_active());NPC_update();assert(npcHp==0);puts("NPC contact, shock centers, pedestal access, legacy rules and timers passed.");return 0;}
'''


def main():
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    with tempfile.TemporaryDirectory(prefix='plaguefall-npc-contact-') as tmp:
        folder = Path(tmp)
        for name, data in STUBS.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
        (folder / 'test.c').write_text(TEST)
        binary = folder / 'npc-test'
        subprocess.run([*compiler, '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-I'+str(folder),
                        '-I'+str(ROOT / 'game/src'), str(folder / 'test.c'),
                        str(ROOT / 'game/src/actors/npc.c'), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
