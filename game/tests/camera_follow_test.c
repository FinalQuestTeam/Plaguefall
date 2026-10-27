#include <assert.h>
#include <stdio.h>
#include "levels/camera_follow.h"

int main(void)
{
    ArenaRect focus[]={{640,24,160,160,FALSE},{824,24,160,160,FALSE}};
    ArenaNpcVisual santa={.focusTop=192};
    ArenaScene scene={.cameraPlayerY=240,.cameraFocus=focus,.cameraFocusCount=2,.npcVisual=&santa};
    const ArenaDef corridor={.width=3072,.height=320,.scene=&scene};
    const ArenaDef tall={.width=768,.height=544,.scene=&scene};
    const ArenaDef small={.width=320,.height=224,.scene=&scene};
    for(int rate=50;rate<=60;rate+=10) {
        s16 x,y;
        CAMERAFOLLOW_target(&corridor,900,220,&x,&y);
        assert(x==748 && y==89);
        // Long idle at a facade and the Santa: metadata cannot pan the camera.
        for(int frame=0;frame<rate*10;frame++) {
            scene.cameraPlayerY=frame%2 ? 184 : 240;
            scene.cameraSouthStart=frame%2 ? 192 : 224;
            focus[0].x=640+frame%200;santa.focusTop=160+frame%100;
            CAMERAFOLLOW_target(&corridor,900,220,&x,&y);
            assert(x==748 && y==89);
        }
        // Full speed in eight directions, reverse and stop. No residual drift.
        for(int mx=-1;mx<=1;mx++)for(int my=-1;my<=1;my++) {
            if(!mx && !my)continue;
            for(int speed=2;speed<=4;speed+=2) {
                int px=400,py=300;CAMERAFOLLOW_target(&tall,px,py,&x,&y);
                for(int frame=0;frame<24;frame++) {
                    s16 oldX=x,oldY=y;int sign=frame<12 ? 1 : -1;
                    px+=sign*mx*speed;py+=sign*my*speed;
                    CAMERAFOLLOW_target(&tall,px,py,&x,&y);
                    assert(x-oldX==sign*mx*speed && y-oldY==sign*my*speed);
                }
                const s16 stoppedX=x,stoppedY=y;
                for(int frame=0;frame<rate*5;frame++) {
                    CAMERAFOLLOW_target(&tall,px,py,&x,&y);
                    assert(x==stoppedX && y==stoppedY);
                }
            }
        }
        // Restart and a different stage immediately compute their spawn view.
        CAMERAFOLLOW_target(&tall,64,296,&x,&y);assert(x==0 && y==165);
        CAMERAFOLLOW_target(&corridor,48,208,&x,&y);assert(x==0 && y==77);
        CAMERAFOLLOW_target(&small,152,131,&x,&y);assert(x==0 && y==0);
        for(int px=16;px<=3040;px+=8)for(int py=96;py<=272;py+=8) {
            x=-30000;y=30000;CAMERAFOLLOW_safe(&corridor,px,py,&x,&y);
            assert(x>=0 && x<=2752 && y>=0 && y<=96);
            assert(px-8-x>=0 && px+24-x<=320 && py-31-y>=24 && py+17-y<=224);
        }
    }
    puts("Camera follow:10s stationary focus,8directions, reversals,5s stops, stage reset and full-body bounds passed at50/60Hz.");
}
