// Experimental replacement only. Timing, displacement cap and arena movement
// stay unchanged. Compact bodies avoid repeated enemy/definition lookups.
static void ENEMIES_separate(void)
{
    static u8 tick;
    if(++tick&1)return;
    typedef struct {s16 x,y,pushX,pushY;u8 slot,half;} Body;
    Body bodies[MAX_ENEMIES],*end=bodies;
    for(u16 i=0;i<MAX_ENEMIES;i++)if(enemies[i].active) {
        const Enemy *e=&enemies[i];const u16 half=ENEMY_SIZE(e)/2;
        *end++=(Body){e->x+half,e->y+half,0,0,i,half};
    }
    for(Body *a=bodies;a<end;a++)for(Body *b=a+1;b<end;b++) {
        s16 dx=b->x-a->x,dy=b->y-a->y;
        const s16 minDist=((a->half+b->half)*SEP_MIN_NUM)>>SEP_MIN_SHIFT;
        s16 ax=dx<0 ? -dx : dx,ay=dy<0 ? -dy : dy;
        if(ax>=minDist || ay>=minDist)continue;
        s16 dist=ax>=ay ? ax+(ay>>1) : ay+(ax>>1);
        if(!dist) {
            dx=ax=1+(a->slot&3);dy=ay=1+(b->slot&3);
            dist=ax>=ay ? ax+(ay>>1) : ay+(ax>>1);
        } else if(dist>=minDist)continue;
        s16 push=(minDist-dist)*SEP_STRENGTH;
        if(push>SEP_MAX)push=SEP_MAX;
#ifdef SEPARATION_COMPASS
        // Eight directions use only comparisons and shifts in the pair loop.
        // Diagonal components stay gentle, at three quarters of axis strength.
        s16 vx=0,vy=0;
        if(ax>=ay*2)vx=push;
        else if(ay>=ax*2)vy=push;
        else vx=vy=(push*3)>>2;
        if(dx<0)vx=-vx;
        if(dy<0)vy=-vy;
#else
        // Normal-sized enemies preserve the original integer force exactly.
        // Boss/boss distances 32..35 need a bounded extension of the old LUT.
        const s16 reciprocal=dist<32 ? SEP_RECIP[dist] : dist==32 ? 2 : 1;
        const s16 k=push*reciprocal;
        const s16 vx=((s32)dx*k)>>6,vy=((s32)dy*k)>>6;
#endif
        a->pushX-=vx;a->pushY-=vy;b->pushX+=vx;b->pushY+=vy;
    }
    // At most fifteen contributions <=22 units per axis fit comfortably in
    // signed 16 bits. Keep the original per-enemy final cap of twenty units.
    for(Body *b=bodies;b<end;b++) {
        if(!(b->pushX|b->pushY))continue;
        s16 dx=b->pushX,dy=b->pushY;
        if(dx>SEP_MAX)dx=SEP_MAX;else if(dx<-SEP_MAX)dx=-SEP_MAX;
        if(dy>SEP_MAX)dy=SEP_MAX;else if(dy<-SEP_MAX)dy=-SEP_MAX;
        Enemy *e=&enemies[b->slot];
        ARENA_move(&e->fx,&e->fy,dx,dy,b->half*2);
        e->x=e->fx>>6;e->y=e->fy>>6;
    }
}
