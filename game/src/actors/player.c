// Jogador: movimento em fixed-point 26.6, vida, invencibilidade e tiro.

#include "actors/player.h"
#include "core/game.h"
#include "core/stats.h"
#include "system/audio/sfx.h"
#include "system/video/screens/hud.h"
#include "actors/shots.h"
#include "system/video/herogfx.h"
#include "levels/test.h"

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
static u16 diagonalRelease;     // tolerância para soltar uma diagonal sem perder a mira
static bool fireArmed;          // só atira após soltar A uma vez (evita que o A
                                // que confirmou o menu dispare ao entrar na fase)
static u8  speedPct;            // bônus de velocidade da botinha (0..MAX)

void PLAYER_addSpeed(void)   { if (speedPct < PLAYER_SPEED_MAX) speedPct += PLAYER_SPEED_STEP; }
void PLAYER_resetSpeed(void) { speedPct = 0; }
u8   PLAYER_speedBonus(void) { return speedPct; }
void PLAYER_grantShield(void) { shieldTimer = PLAYER_SHIELD_TENTHS * fps / 10; }
u16 PLAYER_shieldRemaining(void) { return shieldTimer; }
void PLAYER_restoreShield(u16 frames) { shieldTimer = frames; }

void PLAYER_reset(void)
{
    px = ARENA_startX();
    py = ARENA_startY();
    pfx = (s32) px << 6;
    pfy = (s32) py << 6;
    playerSlowPct = 0;
    faceX = 1; faceY = 0;
    shotCooldown = 0;
    diagonalRelease = 0;
    fireArmed = FALSE;          // exige soltar A antes do 1º tiro da fase
    invTimer = 0;
    shieldTimer = 0;
}

void PLAYER_observeFireRelease(u16 joy)
{
    if(!(joy&BUTTON_A))fireArmed=TRUE;
}
void PLAYER_waitFireRelease(void){fireArmed=FALSE;}

void PLAYER_fullHp(void)
{
    hp = PLAYER_START_HP;
}

// perda de HP direta (ignora os i-frames de dano, mas NÃO o escudo do item)
void loseHp(u16 dmg)
{
    if (hp<=0 || shieldTimer) return;   // dead actors cannot take more hits

    hp -= dmg;
    if(hp<=0 && TEST_noDefeat())hp=1;
    phaseStats.damageTaken += dmg;      // condições de saída do grafo (SEM_DANO)
    HUD_drawLife(hp);

    if (hp <= 0)
    {
        hp = 0;
        gameOver = TRUE;
    }
}

void damagePlayer(u16 dmg)
{
    if (hp<=0 || invTimer || shieldTimer) return;

    // feedback sonoro do dano de INIMIGO (contato/projétil). O dano de ambiente
    // (lava) entra por loseHp e fica só com o som ambiente de crepitar.
    SFX_playerHit();
    loseHp(dmg);
    if (!gameOver) invTimer = PLAYER_INV_TENTHS * fps / 10;
}

void healPlayer(u16 amount)
{
    if(hp<=0)return;
    hp += amount;
    if (hp > PLAYER_START_HP) hp = PLAYER_START_HP;   // teto
    HUD_drawLife(hp);
}

void PLAYER_update(u16 joy)
{
    if(hp<=0)return;
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

    ARENA_move(&pfx, &pfy, mx * (s16)speedFp, my * (s16)speedFp, 16);
    px = (s16) (pfx >> 6);
    py = (s16) (pfy >> 6);

    // O D-pad costuma liberar um eixo antes do outro. Preserve a diagonal
    // nessa transição curta; movimento continua imediato. Segurar o eixo
    // restante confirma a mudança cardinal, e um novo toque após parar é imediato.
    if (mx && my)
    {
        faceX = mx; faceY = my;
        diagonalRelease = (fps * PLAYER_DIAGONAL_RELEASE_MS + 999) / 1000;
    }
    else if (mx || my)
    {
        const bool releasingDiagonal = faceX && faceY &&
            ((mx == faceX && !my) || (my == faceY && !mx));
        if (releasingDiagonal && diagonalRelease) diagonalRelease--;
        if (!releasingDiagonal || !diagonalRelease)
        {
            faceX = mx; faceY = my;
            diagonalRelease = 0;
        }
    }
    else diagonalRelease = 0;

    HERO_prepare(HERO_direction(faceX,faceY));
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
    if(hp<=0)return FALSE; // the collapse must remain visible after a fatal hit
    if (shieldTimer) return FALSE;
    if (invTimer)    return (invTimer >> 2) & 1;
    return FALSE;
}
