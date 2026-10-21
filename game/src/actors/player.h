#ifndef PLAYER_H
#define PLAYER_H

#include <genesis.h>

// ===========================================================================
// CONFIG (balanceamento do jogador) — ajuste aqui
// ===========================================================================
#define PLAYER_SPEED        2   // velocidade base (px/frame)
#define PLAYER_START_HP     100 // vida inicial e teto
#define PLAYER_INV_TENTHS   3   // invencibilidade após dano (0,1 s) → 0,3 s
#define PLAYER_FIRE_TENTHS  8   // intervalo entre disparos (0,1 s) → 0,8 s (1,25/s)
#define PLAYER_DIAGONAL_RELEASE_MS 80 // tolerância entre soltar os dois eixos; só afeta a mira
#define PLAYER_SPEED_STEP   20  // bônus de velocidade por botinha (%)
#define PLAYER_SPEED_MAX    100 // bônus máximo de velocidade (%) → dobro no teto
#define PLAYER_SHIELD_TENTHS 30 // invencibilidade do item escudo (0,1 s) → 3,0 s
// ===========================================================================

extern s16 faceX, faceY;    // última direção entre as oito possíveis (usada pelo tiro)
extern s16 hp;

// centraliza o jogador e zera o estado de controle (NÃO mexe no hp)
void PLAYER_reset(void);

// vida cheia (início de jogo / pós-game-over)
void PLAYER_fullHp(void);

// serviços de vida usados por outros módulos (inimigos, lava, item de vida):
void damagePlayer(u16 dmg);     // dano com invencibilidade (pode dar game over)
void loseHp(u16 dmg);           // dano direto de ambiente (ignora invencibilidade)
void healPlayer(u16 amount);    // cura, limitada ao teto de 100

// bônus de velocidade (botinha): +PLAYER_SPEED_STEP%, teto PLAYER_SPEED_MAX%
void PLAYER_addSpeed(void);
void PLAYER_resetSpeed(void);   // volta a 0 (início / game over)
u8 PLAYER_speedBonus(void);     // bônus atual em % (para a caixa de infos do teste)

// invencibilidade temporária (item escudo): imune a tudo, inclusive lava
void PLAYER_grantShield(void);

// movimento, invencibilidade e tiro (botão A); chamar só com o jogo ativo
void PLAYER_update(u16 joy);

// sprite oculto neste frame? (pisca da invencibilidade)
bool PLAYER_hidden(void);

#endif // PLAYER_H
