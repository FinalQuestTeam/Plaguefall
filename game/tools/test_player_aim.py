"""Exercise production player.c with staggered diagonal releases, at 50/60Hz."""
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
typedef int16_t s16; typedef uint16_t u16; typedef int32_t s32;
typedef uint32_t u32; typedef uint8_t u8;
#define TRUE true
#define FALSE false
#define BUTTON_UP 1
#define BUTTON_DOWN 2
#define BUTTON_LEFT 4
#define BUTTON_RIGHT 8
#define BUTTON_A 64
void VDP_drawText(const char *,u16,u16);
#endif
''',
    'core/game.h': '''#include <genesis.h>
extern u16 fps; extern bool gameOver; extern s16 px,py;
s16 ARENA_startX(void); s16 ARENA_startY(void);
void ARENA_move(s32 *,s32 *,s16,s16,u16);
''',
    'system/audio/sfx.h': 'void SFX_playerHit(void);\n',
    'system/video/screens/hud.h': '#include <genesis.h>\nvoid HUD_drawLife(s16);\n',
    'actors/shots.h': 'void SHOTS_firePlayer(void);\n',
    'levels/levels.h': '#include <genesis.h>\nextern u8 currentLevel, testStage;\n',
    'system/video/herogfx.h': '#include <genesis.h>\nu8 HERO_direction(s16,s16);\nvoid HERO_prepare(u8);\n',
}
TEST = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "actors/player.h"
#include "core/game.h"
#include "core/stats.h"
#include "system/video/herogfx.h"
u16 fps; bool gameOver; PhaseStats phaseStats;
u8 currentLevel=1, testStage;
static unsigned shots,prepared; static s16 shotX,shotY;
s16 ARENA_startX(void){return 100;} s16 ARENA_startY(void){return 100;}
void ARENA_move(s32 *x,s32 *y,s16 dx,s16 dy,u16 size){(void)size;*x+=dx;*y+=dy;}
void HUD_drawLife(s16 life){(void)life;}
void VDP_drawText(const char *s,u16 x,u16 y){(void)s;(void)x;(void)y;}
void SFX_playerHit(void){}
bool TEST_noDefeat(void){return false;}
u8 HERO_direction(s16 x,s16 y){return (u8)((y+1)*3+x+1);}
void HERO_prepare(u8 dir){prepared=dir;}
void SHOTS_firePlayer(void){assert(prepared==HERO_direction(faceX,faceY));shots++;shotX=faceX;shotY=faceY;}
static void reset(void){PLAYER_reset();PLAYER_resetSpeed();PLAYER_fullHp();shots=0;gameOver=false;PLAYER_update(0);}
static void hold(u16 input,unsigned ticks){while(ticks--)PLAYER_update(input);}
static void expect(s16 x,s16 y,const char *label){
    if(faceX!=x||faceY!=y){fprintf(stderr,"%uHz %s: expected (%d,%d), got (%d,%d)\n",fps,label,x,y,faceX,faceY);abort();}
}
static u16 buttons(s16 x,s16 y){return (x<0?BUTTON_LEFT:x>0?BUTTON_RIGHT:0)|(y<0?BUTTON_UP:y>0?BUTTON_DOWN:0);}
static void staggered_releases(void){
    for(s16 x=-1;x<=1;x+=2)for(s16 y=-1;y<=1;y+=2)for(int releaseX=0;releaseX<2;releaseX++){
        // Simulate 1–3 sampled frames between letting go of each axis.
        for(unsigned gap=1;gap<=3;gap++){
            reset();hold(buttons(x,y),8);expect(x,y,"moving diagonal");
            s16 beforeX=px,beforeY=py;
            hold(buttons(releaseX?0:x,releaseX?y:0),gap);
            assert((releaseX?px==beforeX:py==beforeY));
            assert((releaseX?py!=beforeY:px!=beforeX)); // movement is never delayed
            PLAYER_update(0);expect(x,y,"staggered diagonal stop");
            s16 stoppedX=px,stoppedY=py;
            hold(0,fps);expect(x,y,"diagonal idle");
            assert(px==stoppedX&&py==stoppedY);
            hold(BUTTON_A,2*fps);expect(x,y,"stationary autofire");
            assert(shots>=2&&shotX==x&&shotY==y);
            assert(px==stoppedX&&py==stoppedY);
        }
    }
}
static void intentional_turns(void){
    for(s16 x=-1;x<=1;x+=2)for(s16 y=-1;y<=1;y+=2){
        for(int axis=0;axis<2;axis++){
            reset();hold(buttons(x,y),8);
            hold(buttons(axis?0:x,axis?y:0),fps/5);
            expect(axis?0:x,axis?y:0,"sustained cardinal turn");
            PLAYER_update(0);expect(axis?0:x,axis?y:0,"cardinal idle after intentional turn");
        }
        reset();hold(buttons(x,y),8);PLAYER_update(0);
        PLAYER_update(buttons(x,0));expect(x,0,"new cardinal press after idle");
        reset();hold(buttons(x,y),8);PLAYER_update(buttons(-x,0));expect(-x,0,"opposite turn is immediate");
        reset();hold(buttons(x,y),8);PLAYER_update(buttons(-x,-y));expect(-x,-y,"diagonal turn is immediate");
        reset();hold(buttons(x,y),8);hold(buttons(x,0),1);hold(buttons(x,y),1);hold(buttons(0,y),1);PLAYER_update(0);
        expect(x,y,"thumb rolls across diagonal before stopping");
        reset();hold(buttons(x,y),8);hold(buttons(x,0),1);PLAYER_reset();
        PLAYER_update(BUTTON_UP);expect(0,-1,"reset clears release state");
    }
    const s16 dirs[4][2]={{1,0},{-1,0},{0,1},{0,-1}};
    for(int i=0;i<4;i++){
        reset();PLAYER_update(buttons(dirs[i][0],dirs[i][1]));PLAYER_update(0);
        expect(dirs[i][0],dirs[i][1],"cardinal stop remains responsive");
    }
}
int main(void){for(fps=50;fps<=60;fps+=10){staggered_releases();intentional_turns();printf("%uHz: all four diagonal idles, both release orders, stationary autofire and deliberate turns passed.\n",fps);}return 0;}
'''


def main():
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    with tempfile.TemporaryDirectory(prefix='plaguefall-player-aim-') as tmp:
        folder = Path(tmp)
        for name,data in STUBS.items():
            path = folder/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(data)
        (folder/'test.c').write_text(TEST)
        binary = folder/'player-aim'
        subprocess.run([*compiler,'-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                        '-I'+str(folder),'-I'+str(ROOT/'game/src'),str(folder/'test.c'),
                        str(ROOT/'game/src/actors/player.c'),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)


if __name__ == '__main__':
    main()
