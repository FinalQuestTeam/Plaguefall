// Arma do jogador: potência (leque de balas), item raio (reação em cadeia),
// disparo (botão A) e atualização/colisão dos projéteis do jogador.

#include "actors/shots.h"
#include "core/game.h"
#include "actors/player.h"
#include "system/audio/sfx.h"
#include "enemies/enemies.h"
#include "levels/levels.h"
#include "system/video/projection.h"
#include "system/video/herogfx.h"
#include "levels/test.h"

static u8 shotPower = 1;         // balas por disparo (1..SHOTS_MAX_POWER)
static u8 shotMode;              // SHOTMODE_* ativo (raio/gelo/fogo)
static u8 modeCharges;           // acertos restantes do modo

void SHOTS_resetPower(void) { shotPower = 1; }
void SHOTS_addPower(void)   { if (shotPower < SHOTS_MAX_POWER) shotPower++; }
u8   SHOTS_power(void)      { return shotPower; }

void SHOTS_setMode(u8 mode, u8 charges) { shotMode = mode; modeCharges = charges; }
u8   SHOTS_mode(void)        { return shotMode; }
u8   SHOTS_modeCharges(void) { return modeCharges; }
void SHOTS_grantChain(void) { SHOTS_setMode(SHOTMODE_CHAIN, SHOTS_CHAIN_HITS); }
void SHOTS_resetChain(void) { shotMode = SHOTMODE_NONE; modeCharges = 0; }
bool SHOTS_hasChain(void)   { return shotMode == SHOTMODE_CHAIN && modeCharges > 0; }

// cria um projétil do jogador em (fx, fy) 26.6 com velocidade (vx, vy) 26.6 e o
// modo especial `mode` (SHOTMODE_*), que decide o efeito ao acertar
static void spawnPShot(s32 fx, s32 fy, s32 vx, s32 vy, u8 mode)
{
    const u16 cap = currentLevel==0 ? TEST_shotLimit() : (LEVEL_current()->shotCap ? LEVEL_current()->shotCap : MAX_PSHOTS);
    for (u16 i = 0; i < cap; i++)
    {
        if (pshots[i].active) continue;
        pshots[i].x = fx;
        pshots[i].y = fy;
        pshots[i].vx = vx;
        pshots[i].vy = vy;
        pshots[i].mode = mode;
        pshots[i].active = TRUE;
        pshots[i].renderPose=0;
        return;
    }
}

void SHOTS_firePlayer(void)
{
    // a velocidade do tiro escala junto com o bônus da botinha, para a bala
    // nunca ficar mais lenta que o personagem
    u16 spd = PSHOT_SPEED * 64;
    const u8 bonus = PLAYER_speedBonus();
    if (bonus) spd = (u16) (((u32) spd * (100 + bonus)) / 100);

    // direção do jogador normalizada, na velocidade `spd` (26.6)
    const s16 dx = faceX * 64, dy = faceY * 64;
    u32 mag = getApproximatedDistance(dx, dy);
    if (mag == 0) mag = 1;
    const s32 bvx = ((s32) dx * spd) / (s32) mag;
    const s32 bvy = ((s32) dy * spd) / (s32) mag;

    // Use the barrel of the frame actually queued for display. Do not clamp
    // the origin to the floor: that teleported bullets away from the weapon.
    // Collision handles shots aimed into a wall; N/S shots along it stay aligned.
    s16 mx,my;
    HERO_muzzle(&mx,&my);
    const s16 sx=mx-4,sy=my+VIDEO_HEIGHT_OFFSET-4;
    const s32 fx=(s32)sx*64,fy=(s32)sy*64;

    // modo especial deste disparo: consome 1 carga no tiro (mesmo que erre)
    u8 vmode = SHOTMODE_NONE;
    if (modeCharges)
    {
        vmode = shotMode;
        if (--modeCharges == 0) shotMode = SHOTMODE_NONE;
    }

    // leque de `shotPower` balas em torno da direção; ~14° por passo (k = o/8),
    // com o índice `o` em meios-passos (-(power-1)..+(power-1), passo 2)
    const s16 span = shotPower - 1;
    for (s16 o = -span; o <= span; o += 2)
        spawnPShot(fx, fy, bvx - (bvy * o) / SHOTS_ARC_SHEAR,
                   bvy + (bvx * o) / SHOTS_ARC_SHEAR, vmode);

    SFX_playerShot();
}

__attribute__((noinline)) u16 SHOTS_updatePlayer(void)
{
    u16 killed = 0;
    bool boundsReady=FALSE;
    s16 left=32767,top=32767,right=-32768,bottom=-32768;

    for (u16 i = 0; i < MAX_PSHOTS; i++)
    {
        if (!pshots[i].active) continue;
        pshots[i].x += pshots[i].vx;
        pshots[i].y += pshots[i].vy;

        const s16 sx = (s16) (pshots[i].x >> 6);
        const s16 sy = (s16) (pshots[i].y >> 6);

        if (arenaActive ? ARENA_playerShotBlocked(sx,sy) :
            ((sx < INNER_MIN_X) || (sx > INNER_MAX_X - 7) ||
             (sy < INNER_MIN_Y) || (sy > INNER_MAX_Y - 7)))
        {
            pshots[i].active = FALSE;
            continue;
        }

        if(!boundsReady) {
            left=top=32767;right=bottom=-32768;
            for(u16 j=0;j<MAX_ENEMIES;j++)if(enemies[j].active) {
                const Enemy *e=&enemies[j];const s16 size=ENEMY_SIZE(e);
                if(e->x<left)left=e->x;if(e->y<top)top=e->y;
                if(e->x+size>right)right=e->x+size;
                if(e->y+size>bottom)bottom=e->y+size;
            }
            boundsReady=TRUE;
        }
        if(sx>=right || sx+8<=left || sy>=bottom || sy+8<=top)continue;

        // status pelo modo do PRÓPRIO tiro (a carga já foi gasta no disparo)
        const u8 pm = pshots[i].mode;
        const u8 status = (pm == SHOTMODE_ICE)  ? ENEMY_STATUS_FREEZE
                        : (pm == SHOTMODE_FIRE) ? ENEMY_STATUS_BURN
                                                : ENEMY_STATUS_NONE;

        // colisão com inimigos (AABB 8x8); damageBox aplica o status no acertado
        const u16 hit = ENEMIES_damageBox(sx, sy, 8, 8, status);
        if (hit != ENEMY_HIT_NONE)
        {
            pshots[i].active = FALSE;   // o tiro é consumido mesmo sem matar
            if (hit == ENEMY_HIT_KILLED){killed++;boundsReady=FALSE;}

            if (pm == SHOTMODE_CHAIN)   // raio: reação em cadeia no acerto
            {killed += ENEMIES_chainDamage(sx, sy, SHOTS_CHAIN_TARGETS, SHOTS_CHAIN_RANGE);boundsReady=FALSE;}
        }
    }

    return killed;
}
