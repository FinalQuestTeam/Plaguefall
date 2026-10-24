#include <assert.h>
#include <stdio.h>
typedef int VDPPlane;
#include "system/video/combatgfx.c"
u16 fps=60;
const u8 combat_shots[480]={0},combat_deaths[160000]={0};
static const EnemyDef small={.size=16},large={.size=32},boss={.size=48};
const EnemyDef *const ENEMY_DEFS[15]={&small,&small,&large,&small,&small,&small,&small,&small,&small,&small,&large,&small,&small,&small,&boss};
u16 DMA_getQueueTransferSize(void){return 0;}
u16 DMA_getQueueSize(void){return 0;}
u16 DMA_getMaxQueueSize(void){return 80;}
bool DMA_queueDma(u8 kind,void *source,u16 dest,u16 words,u16 step){(void)kind;(void)source;(void)dest;(void)words;(void)step;return true;}
int main(void){
 for(fps=50;fps<=60;fps+=10){
  for(u8 type=0;type<15;type++)if(type<12||type==14){
   COMBATGFX_clear();assert(!deathActiveCount&&!COMBATGFX_remaining());
   COMBATGFX_spawn(type,100,140);assert(deathActiveCount==1);
   u16 life=duration(type);assert(COMBATGFX_remaining()==life);
   for(u16 t=0;t<life;t++){
    assert(deathActiveCount==1);COMBATGFX_prepare(0);
    assert(combatDeaths[0].ready);COMBATGFX_update();
    assert(COMBATGFX_remaining()==life-t-1);
   }
   assert(!deathActiveCount);COMBATGFX_update();assert(!COMBATGFX_remaining());
  }
  COMBATGFX_clear();for(u8 i=0;i<4;i++)COMBATGFX_spawn(i,0,0);
  assert(deathActiveCount==4);COMBATGFX_spawn(0,0,0);assert(deathActiveCount==4);
  COMBATGFX_spawn(14,0,0);assert(deathActiveCount==1&&bossLayout);
  COMBATGFX_spawn(0,0,0);COMBATGFX_spawn(4,0,0);assert(deathActiveCount==3);
  COMBATGFX_spawn(8,0,0);assert(deathActiveCount==3);
  COMBATGFX_invalidate();assert(deathActiveCount==3);
  for(u16 t=0;t<fps;t++){COMBATGFX_prepare(0);COMBATGFX_update();}
  assert(!deathActiveCount&&!bossLayout&&!COMBATGFX_remaining());
 }
 puts("Death counter: all 13 species, 50/60Hz, expiry, saturation, boss replacement, invalidation and clear passed.");
}
