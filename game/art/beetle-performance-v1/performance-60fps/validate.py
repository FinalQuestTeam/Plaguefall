"""Native sanitizer checks using the actual captured baseline/candidate functions."""
from pathlib import Path
import argparse,re,subprocess,tempfile

def function(source,name):
    start=re.search(r'^.*\b'+name+r'\([^;\n{}]*\)\s*\{',source,re.M).start()
    opening=source.index('{',start);depth=1;end=opening+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('baseline',type=Path);ap.add_argument('candidate',type=Path);args=ap.parse_args()
    base=args.baseline;candidate=args.candidate
    names=['outside','occupied','ARENA_blocked','ARENA_shotBlocked','ARENA_playerShotBlocked','ARENA_move']
    common='''#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
typedef uint8_t u8;typedef int16_t s16;typedef uint16_t u16;typedef int32_t s32;typedef uint32_t u32;
#define TRUE true
#define FALSE false
#define VIDEO_HEIGHT_OFFSET 16
#define PAL1 1
#define TILE_USER_INDEX 16
#define TILE_PSHOT 0
#define TILE_ESHOT 1
#define SHOT_BASE 638
#define TILE_ATTR_FULL(p,prio,v,h,t) (((h)<<11)+((v)<<12)+((p)<<13)+((prio)<<15)+(t))
static s16 arenaMinX,arenaMaxX,arenaMinY,arenaMaxY,solidLeft,solidRight,solidTop,solidBottom;
static u32 collisionRows[64][8],shotRows[64][8];
static bool hasShotSolids,shotsReady;static void *world;
typedef struct {s32 x,y,vx,vy;u8 mode,dmg;bool active;u8 renderPose;}FShot;
'''
    code=common
    for root,prefix in [(base,'ref_'),(candidate,'')]:
        source=(root/'src/levels/arena.c').read_text();part='\n'.join(function(source,n) for n in names)
        if prefix:
            for n in names:part=re.sub(r'\b'+n+r'\b',prefix+n,part)
        code+=part
    source=(base/'src/system/video/combatgfx.c').read_text()
    code+=function(source,'COMBATGFX_shotAttr').replace('COMBATGFX_shotAttr','ref_shotAttr')
    source=(candidate/'src/system/video/combatgfx.c').read_text()
    code+=source[source.index('static const u16 attrs[80]'):source.index('const u16 *COMBATGFX_shotTable')]
    code+=function(source,'COMBATGFX_cachedShotAttr')
    source=(candidate/'src/system/video/spritelist.c').read_text()
    code+='typedef struct{u16 y,size_link,attribut,x;} VDPSprite; static VDPSprite vdpSpriteCache[80];static s16 cameraX,cameraY;\n#define SPRITE_SIZE(w,h) ((((w)-1)<<2)|((h)-1))\n'
    code+=function((candidate/'src/system/video/combatgfx.c').read_text(),'COMBATGFX_shotTable')
    code+=source[source.index('static u16 bandLoad'):source.index('void SPRITES_draw(void)')]
    header=(candidate/'src/enemies/enemies.h').read_text()
    code+=re.search(r'^#define ENEMY_UPDATE_STEP.*$',header,re.M)[0]+'\n'
    code+='''static uint32_t rng=0x12345678;
static unsigned rnd(unsigned n){rng=rng*1664525u+1013904223u;return rng%n;}
static void solid(unsigned x,unsigned y,unsigned w,unsigned h,bool shots){
    if(!w||!h)return;
    if((s16)x<solidLeft)solidLeft=x;if((s16)y<solidTop)solidTop=y;
    if((s16)(x+w)>solidRight)solidRight=x+w;if((s16)(y+h)>solidBottom)solidBottom=y+h;
    for(unsigned yy=y/8;yy<(y+h)/8;yy++)for(unsigned xx=x/8;xx<(x+w)/8;xx++){
        u32 bit=0x80000000u>>(xx&31);collisionRows[yy][xx>>5]|=bit;
        if(shots)shotRows[yy][xx>>5]|=bit;
    }
    hasShotSolids|=shots;
}
int main(void){
    assert(sizeof(FShot)==20);
    struct{u8 type;}e;
    for(e.type=0;e.type<15;e.type++)assert(ENEMY_UPDATE_STEP(&e)==(e.type<12&&(e.type%4==1||e.type%4==2)?4:1));
    unsigned movements=0,queries=0;
    for(unsigned scene=0;scene<3;scene++){
        world=(void*)1;arenaMinX=16;arenaMinY=112;arenaMaxX=scene==2?2031:495;arenaMaxY=scene==2?495:367;
        solidLeft=solidTop=32767;solidRight=solidBottom=-32768;
        memset(collisionRows,0,sizeof collisionRows);memset(shotRows,0,sizeof shotRows);hasShotSolids=false;
        if(scene==0){solid(48,104,72,8,false);solid(272,96,56,8,false);}
        if(scene==2)for(unsigned j=0;j<24;j++)solid(16+rnd(246)*8,112+rnd(40)*8,8+rnd(6)*8,8+rnd(6)*8,j&1);
        for(unsigned j=0;j<60000;j++){
            s16 x=(s16)rnd(arenaMaxX+50)-20,y=(s16)rnd(arenaMaxY+50)-20;
            u16 size=16+8*rnd(5);
            assert(ARENA_blocked(x,y,size,size)==ref_ARENA_blocked(x,y,size,size));
            assert(ARENA_shotBlocked(x,y)==ref_ARENA_shotBlocked(x,y));
            assert(ARENA_playerShotBlocked(x,y)==ref_ARENA_playerShotBlocked(x,y));queries+=3;
            if(ref_ARENA_blocked(x,y,size,size))continue;
            s32 ax=x*64+rnd(64),ay=y*64+rnd(64),bx=ax,by=ay;
            s16 dx=(s16)rnd(641)-320,dy=(s16)rnd(641)-320;
            ARENA_move(&ax,&ay,dx,dy,size);ref_ARENA_move(&bx,&by,dx,dy,size);
            assert(ax==bx&&ay==by);movements++;
        }
    }
    unsigned attributes=0;
    for(unsigned ready=0;ready<2;ready++)for(unsigned style=0;style<256;style++)for(unsigned j=0;j<128;j++){
        FShot s={0};s.vx=(s32)rnd(769)-384;s.vy=(s32)rnd(769)-384;shotsReady=ready;
        u16 expected=ref_shotAttr(style,s.vx,s.vy);
        assert(COMBATGFX_cachedShotAttr(&s,style)==expected);
        assert(COMBATGFX_cachedShotAttr(&s,style)==expected);attributes+=2;
    }
    for(unsigned scene=0;scene<2048;scene++){
        u16 n=0;beginSprites();
        for(unsigned attempt=0;attempt<120;attempt++){
            s16 x=(s16)rnd(400)-40,y=(s16)rnd(300)-40;u16 old=n;
            switch(rnd(5)){
                case 0:emitSmall(&n,x,y,1);break;
                case 1:emitActor(&n,x,y,1);assert(n==old||n==old+2);break;
                case 2:emitBoss(&n,x,y,1);assert(n==old||n==old+4);break;
                default:SPRITES_emit(&n,x,y,(u8)(rnd(4)*5),1);break;
            }
            assert(n<=80);
        }
        assert(finishSprites(n)==n);
        for(unsigned line=0;line<224;line++){
            unsigned count=0,width=0;
            for(unsigned i=0;i<n;i++){
                VDPSprite *sprite=&vdpSpriteCache[i];s16 y=(sprite->y&511)-128;
                unsigned size=sprite->size_link>>8,h=((size&3)+1)*8;
                if((s16)line>=y&&(s16)line<y+(s16)h){count++;width+=(((size>>2)&3)+1)*8;}
            }
            assert(count<=20&&width<=320);
        }
    }
    // Exercise the specialized projectile batch, including clipped positions.
    FShot shots[16]={0};shotsReady=true;
    for(unsigned j=0;j<16;j++){shots[j].active=true;shots[j].x=(30+j*16)*64;shots[j].y=160*64;shots[j].vy=128;}
    beginSprites();assert(drawShots(0,shots,16,false)==16);
    puts("2048 randomized mixed SAT scenes obey 80 global / 20 sprites / 320 pixels per scanline; actors and boss admitted atomically.");
    printf("%u collision queries; %u valid-start movements exactly equal; %u cached projectile attributes equal; cadence type map passed.\\n",queries,movements,attributes);
}
'''
    with tempfile.TemporaryDirectory(prefix='plaguefall-60-native-') as temp:
        root=Path(temp);(root/'test.c').write_text(code)
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Wno-misleading-indentation','-fsanitize=address,undefined',str(root/'test.c'),'-o',str(root/'test')],check=True)
        subprocess.run([str(root/'test')],check=True)
if __name__=='__main__':main()
