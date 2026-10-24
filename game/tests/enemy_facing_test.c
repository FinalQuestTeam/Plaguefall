// Production loader against a recording DMA; no renderer or emulator required.
#include <assert.h>
#include <stdio.h>
typedef int VDPPlane;
#include "system/video/enemygfx.c"

const u32 insect_frames[ENEMY_ASSET_LONGWORDS]={0},insect_icons[1920]={0},insect_shield_frames[ENEMY_ASSET_LONGWORDS]={0};
Enemy enemies[MAX_ENEMIES];
static const EnemyDef small={.size=16},medium={.size=24};
static const EnemyDef smallPurple={.size=16,.color=COLOR_PURPLE},large={.size=32,.color=COLOR_PURPLE};
static const EnemyDef orange={.size=16,.color=COLOR_ORANGE},boss={.size=48};
const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES]={
    &small,&small,&large,&orange,&small,&small,&smallPurple,&orange,
    &medium,&medium,&large,&orange,&medium,&medium,&boss};
s16 px,py,chaseX,chaseY;
u16 fps=60;
u8 currentLevel=1,testStage;
static u16 bytes,uploads;
static bool failDMA,preview;
static u8 previewDir,previewPose;
static u32 sourceWord;static bool lastShieldTransfer;
u16 DMA_getQueueTransferSize(void){return bytes;}
u16 DMA_getQueueSize(void){return uploads;}
u16 DMA_getMaxQueueSize(void){return 80;}
bool DMA_queueDma(u8 kind,void *source,u16 dest,u16 words,u16 step)
{
    (void)dest;assert(kind==DMA_VRAM && step==2);
    if(failDMA)return false;
    lastShieldTransfer=(uintptr_t)source>=(uintptr_t)insect_shield_frames && (uintptr_t)source<(uintptr_t)(insect_shield_frames+ENEMY_ASSET_LONGWORDS);
    sourceWord=((uintptr_t)source-(uintptr_t)(lastShieldTransfer?insect_shield_frames:insect_frames))/4;
    uploads++;bytes+=words*2;assert(uploads<=ENEMY_DMA_FRAMES);
    return true;
}
void VDP_loadTileData(const u32 *data,u16 tile,u16 count,u8 mode)
{(void)data;(void)tile;(void)count;(void)mode;}
void VDP_setTileMapXY(u16 plane,u16 attr,u16 col,u16 row)
{(void)plane;(void)attr;(void)col;(void)row;}
void COMBATGFX_invalidate(void){}
u16 COMBATGFX_remaining(void){return 0;}
void COMBATGFX_prepare(u16 transfers){assert(transfers==uploads);}
bool COUNTDOWN_active(void){return false;}
bool TEST_animation(u8 index,u8 *dir,u8 *pose)
{(void)index;if(preview){*dir=previewDir;*pose=previewPose;}return preview;}
static void tick(u16 frame){bytes=uploads=0;ENEMYGFX_prepare(frame);}
static Enemy *spawn(u8 type)
{
    memset(enemies,0,sizeof enemies);ENEMYGFX_reset();
    Enemy *e=&enemies[0];e->active=true;e->type=type;e->x=100;e->y=100;
    px=160;py=100;chaseX=168;chaseY=108;
    preview=false;currentLevel=1;failDMA=false;return e;
}
static void gallery(void)
{
    for(u8 type=0;type<ENEMY_TYPES;type++)if(type<ENEMY_DUMMY || type==ENEMY_BOSS)
        for(u8 dir=0;dir<8;dir++)for(u8 pose=0;pose<6;pose++)
        {
            spawn(type);currentLevel=0;testStage=1;preview=true;previewDir=dir;previewPose=pose;
            tick(0);assert(ENEMYGFX_ready(0));
            assert(slots[0].dir==dir && slots[0].pose==pose);
            assert(ENEMYGFX_entityFlipH(0)==(dir>=5));
            const EnemyArt *art=&ENEMY_ART[type];
            const u8 canonical[]={0,1,2,3,4,3,2,1};
            assert(sourceWord==art->offset+(canonical[dir]*6+pose)*art->words);
        }
    preview=false;currentLevel=1;
}
static void movement(void)
{
    static const s16 dx[]={0,64,64,64,0,-64,-64,-64};
    static const s16 dy[]={-64,-64,0,64,64,64,0,-64};
    for(u8 type=0;type<ENEMY_TYPES;type++)if(type<ENEMY_DUMMY || type==ENEMY_BOSS)
        for(u8 dir=0;dir<8;dir++)
        {
            Enemy *e=spawn(type);s16 half=ENEMY_SIZE(e)/2;
            chaseX=e->x+half+dx[dir];chaseY=e->y+half+dy[dir];
            px=chaseX-8;py=chaseY-8;tick(0);assert(slots[0].dir==dir);
            e->vx=dx[dir];e->vy=dy[dir];e->x+=dx[dir]/64;e->y+=dy[dir]/64;
            // Put the target behind the movement: the current heading wins.
            chaseX=px=e->x-dx[dir];chaseY=py=e->y-dy[dir];
            tick(0);assert(slots[0].dir==dir);
            e->frozen=10;tick(0);assert(slots[0].dir==dir);
            e->frozen=0;e->stun=10;e->vx=-e->vx;e->vy=-e->vy;
            e->x++;tick(0);assert(slots[0].dir==dir);
        }
}
static void attacks(void)
{
    for(u8 type=0;type<ENEMY_TYPES;type++)if(type==ENEMY_BOSS || ENEMY_DEFS[type]->color==COLOR_ORANGE)
    {
        Enemy *e=spawn(type);e->mode=1;e->vx=64;e->vy=64;
        px=py=0;chaseX=chaseY=0;tick(0);assert(slots[0].dir==3 && slots[0].pose<2);
        // Wind-up must keep the locked velocity after the motion grace ends.
        for(u16 f=0;f<8;f++){tick(f);assert(slots[0].dir==3);}
        e->mode=2;e->x++;e->y++;tick(0);assert(slots[0].dir==3);
    }
    Enemy *e=spawn(ENEMY_BOSS);e->tA=4*fps;e->vx=-64;e->vy=0;
    tick(0);e->x--;tick(0);assert(slots[0].dir==2); // retreat while facing player
    e=spawn(ENEMY_SQ_RED);chaseX=0;chaseY=108;tick(0);assert(slots[0].dir==6);
    e->aggroPlayer=true;tick(0);assert(slots[0].dir==2);
    // Overlapping centers have no heading: retain the last valid direction.
    px=e->x;py=e->y;tick(0);assert(slots[0].dir==2);
}
static void mirrorWithoutBandwidth(void)
{
    spawn(ENEMY_SQ_PUR);tick(0);assert(slots[0].dir==2);
    chaseX=0;bytes=6500;uploads=0;ENEMYGFX_prepare((fps+3)&~3);
    assert(!uploads && slots[0].dir==6 && ENEMYGFX_entityFlipH(0));
    // A failed upload keeps a complete old view, and a reused type stays hidden.
    chaseX=108;chaseY=0;failDMA=true;tick(0);assert(slots[0].dir==6);
    enemies[0].type=ENEMY_BOSS;tick(0);assert(!ENEMYGFX_ready(0));
    failDMA=false;
}

static void shieldTransitions(void)
{
    const u8 kinds[3]={2,6,10},canonical[8]={0,1,2,3,4,3,2,1};
    for(u16 k=0;k<3;k++)for(u8 dir=0;dir<8;dir++)for(u8 pose=0;pose<6;pose++){
        Enemy *e=spawn(kinds[k]);currentLevel=0;testStage=1;preview=true;previewDir=dir;previewPose=pose;
        tick(0);assert(!lastShieldTransfer&&slots[0].pose==pose);
        const EnemyArt *art=&ENEMY_ART[e->type];
        u32 expected=art->offset+(canonical[dir]*6+pose)*art->words;
        assert(sourceWord==expected);
        e->shielded=true;tick(0);assert(lastShieldTransfer&&slots[0].pose==(pose|128)&&sourceWord==expected);
        e->shielded=false;tick(0);assert(!lastShieldTransfer&&slots[0].pose==pose&&sourceWord==expected);
    }
    preview=false;currentLevel=1;
}

int main(void)
{
    for(fps=50;fps<=60;fps+=10){gallery();movement();attacks();mirrorWithoutBandwidth();shieldTransitions();}
    puts("Shield on/off ROM banks in all 144 purple poses per region; 1248 gallery frames; all 13 actors in 8 directions at 50/60Hz; movement, ice, recoil, locked charges, retreat, aggro, DMA failure and mirroring passed.");
    return 0;
}
