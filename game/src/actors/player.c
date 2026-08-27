// Jogador: movimento em fixed-point 26.6, vida, invencibilidade e tiro.

#include "actors/player.h"
#include "core/game.h"
#include "core/stats.h"
#include "system/audio/sfx.h"
#include "system/video/screens/hud.h"
#include "actors/shots.h"

// tunáveis em actors/player.h (bloco CONFIG)

// estado compartilhado (declarado em game.h)
s16 px, py;
u8 playerSlowPct;

s16 faceX, faceY;
s16 hp;

static s32 pfx, pfy;            // posição em 26.6
static u16 invTimer;            // invencibilidade após dano (pisca)
static u16 shieldTimer;         // invencibilidade do item escudo (imune a tudo)
static u16 shotCooldown;        // frames até poder atirar de novo
static bool fireArmed;          // só atira após soltar A uma vez (evita que o A
                                // que confirmou o menu dispare ao entrar na fase)
static u8  speedPct;            // bônus de velocidade da botinha (0..MAX)

void PLAYER_addSpeed(void)   { if (speedPct < PLAYER_SPEED_MAX) speedPct += PLAYER_SPEED_STEP; }
void PLAYER_resetSpeed(void) { speedPct = 0; }
u8   PLAYER_speedBonus(void) { return speedPct; }
void PLAYER_grantShield(void) { shieldTimer = PLAYER_SHIELD_TENTHS * fps / 10; }

void PLAYER_reset(void)
{
    px = INNER_MIN_X + (INNER_MAX_X - INNER_MIN_X - 15) / 2;
    py = INNER_MIN_Y + (INNER_MAX_Y - INNER_MIN_Y - 15) / 2;
    pfx = (s32) px << 6;
    pfy = (s32) py << 6;
    playerSlowPct = 0;
    faceX = 1; faceY = 0;
    shotCooldown = 0;
    fireArmed = FALSE;          // exige soltar A antes do 1º tiro da fase
    invTimer = 0;
    shieldTimer = 0;
}

void PLAYER_fullHp(void)
{
    hp = PLAYER_START_HP;
}

// perda de HP direta (ignora os i-frames de dano, mas NÃO o escudo do item)
void loseHp(u16 dmg)
{
    if (shieldTimer) return;            // escudo: imune inclusive à lava

    hp -= dmg;
    phaseStats.damageTaken += dmg;      // condições de saída do grafo (SEM_DANO)
    HUD_drawLife(hp);

    if (hp <= 0)
    {
        gameOver = TRUE;
        VDP_drawText("GAME OVER", 15, 12);
        VDP_drawText("APERTE START", 14, 14);
    }
}

void damagePlayer(u16 dmg)
{
    if (invTimer || shieldTimer) return;    // invencível: ignora o dano

    // feedback sonoro do dano de INIMIGO (contato/projétil). O dano de ambiente
    // (lava) entra por loseHp e fica só com o som ambiente de crepitar.
    SFX_playerHit();
    loseHp(dmg);
    if (!gameOver) invTimer = PLAYER_INV_TENTHS * fps / 10;
}

void healPlayer(u16 amount)
{
    hp += amount;
    if (hp > PLAYER_START_HP) hp = PLAYER_START_HP;   // teto
    HUD_drawLife(hp);
}

void PLAYER_update(u16 joy)
{
    if (invTimer) invTimer--;
    if (shieldTimer) shieldTimer--;

    s16 mx = 0, my = 0;
    if (joy & BUTTON_LEFT)  mx = -1;
    if (joy & BUTTON_RIGHT) mx =  1;
    if (joy & BUTTON_UP)    my = -1;
    if (joy & BUTTON_DOWN)  my =  1;

    // velocidade em 26.6: base + bônus da botinha, depois lentidão da lama
    u16 speedFp = PLAYER_SPEED << 6;
    if (speedPct)      speedFp = (u16) (((u32) speedFp * (100 + speedPct)) / 100);
    if (playerSlowPct) speedFp = (u16) (((u32) speedFp * (100 - playerSlowPct)) / 100);

    pfx += mx * (s16) speedFp;
    pfy += my * (s16) speedFp;
    if (pfx < (s32) INNER_MIN_X << 6) pfx = (s32) INNER_MIN_X << 6;
    if (pfx > (s32) (INNER_MAX_X - 15) << 6) pfx = (s32) (INNER_MAX_X - 15) << 6;
    if (pfy < (s32) INNER_MIN_Y << 6) pfy = (s32) INNER_MIN_Y << 6;
    if (pfy > (s32) (INNER_MAX_Y - 15) << 6) pfy = (s32) (INNER_MAX_Y - 15) << 6;
    px = (s16) (pfx >> 6);
    py = (s16) (pfy >> 6);

    // direção do tiro = última direção cardinal pressionada
    if (mx || my)
    {
        if (mx && !my) { faceX = mx; faceY = 0; }
        else if (my && !mx) { faceX = 0; faceY = my; }
        else { faceX = mx; faceY = my; }
    }

    if (shotCooldown) shotCooldown--;
    if (!(joy & BUTTON_A)) fireArmed = TRUE;        // soltou A: arma o disparo
    if (fireArmed && (joy & BUTTON_A) && (shotCooldown == 0))    // B é a bomba
    {
        SHOTS_firePlayer();
        shotCooldown = PLAYER_FIRE_TENTHS * fps / 10;
    }
}

bool PLAYER_hidden(void)
{
    if (invTimer)    return (invTimer >> 2) & 1;
    if (shieldTimer) return (shieldTimer >> 2) & 1;    // pisca durante o escudo
    return FALSE;
}
