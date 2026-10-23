#ifndef SHOTS_H
#define SHOTS_H

#include <genesis.h>

#define MAX_PSHOTS      16      // comporta o leque de até 5 balas por volley
#define MAX_ESHOTS      16

// ===========================================================================
// CONFIG (balanceamento dos tiros) — ajuste aqui
// ===========================================================================
#define SHOTS_MAX_POWER 5       // limite de balas por disparo
#define SHOTS_CHAIN_HITS 5      // acertos com reação em cadeia por item raio
#define SHOTS_CHAIN_TARGETS 3   // inimigos atingidos por cadeia
#define SHOTS_CHAIN_RANGE 80    // alcance (px) da cadeia

// ---- modos de tiro especiais (itens do inventário; um por vez) ----
#define SHOTMODE_NONE   0
#define SHOTMODE_CHAIN  1       // raio: reação em cadeia (SHOTS_CHAIN_HITS acertos)
#define SHOTMODE_ICE    2       // gelo: congela o inimigo acertado
#define SHOTMODE_FIRE   3       // fogo: queimadura (dano por tempo) no acertado
#define ICE_CHARGES     3       // cargas do gelo
#define FIRE_CHARGES    4       // cargas do fogo
#define ICE_FREEZE_SEC  5       // duração do congelamento
#define FIRE_BURN_SEC   6       // duração da queimadura
#define FIRE_TICK_SEC   2       // intervalo do dano da queimadura (1 de dano/tick)
#define PSHOT_SPEED     3       // velocidade do tiro do jogador (px/frame)
#define ESHOT_SPEED     2       // velocidade do tiro inimigo (px/frame)
#define ESHOT_DAMAGE    10      // dano do tiro inimigo no jogador
#define SHOTS_ARC_SHEAR 8       // abertura do leque (maior = arco mais fechado)
// Boca da arma: âncoras por desenho/quadro em res/heroi/muzzle.json.
// ===========================================================================

// 26.6 fixed. mode is SHOTMODE_* for player shots, visual style1..4 for enemies.
// dmg is enemy damage to the player (default ESHOT_DAMAGE; boss uses more).
typedef struct { s32 x, y; s32 vx, vy; u8 mode; u8 dmg; bool active; } FShot;

extern FShot pshots[MAX_PSHOTS];
extern FShot eshots[MAX_ESHOTS];

// remove todos os projéteis (não mexe no poder de tiro)
void SHOTS_clear(void);

// poder de tiro: nº de balas por disparo (1..SHOTS_MAX_POWER)
void SHOTS_resetPower(void);    // volta a 1 (início / treino / nova tentativa)
void SHOTS_addPower(void);      // +1 bala (item), respeitando o teto
u8   SHOTS_power(void);         // nº de balas por disparo (caixa de infos do teste)

// modo de tiro especial (raio/gelo/fogo): um por vez, com `charges` acertos
void SHOTS_setMode(u8 mode, u8 charges);
u8   SHOTS_mode(void);           // SHOTMODE_* atual
u8   SHOTS_modeCharges(void);    // cargas restantes do modo

// reação em cadeia (item raio) — atalhos sobre o sistema de modos
void SHOTS_grantChain(void);    // ativa o modo cadeia (SHOTS_CHAIN_HITS acertos)
void SHOTS_resetChain(void);    // desativa qualquer modo (início / nova tentativa)
bool SHOTS_hasChain(void);      // modo cadeia ativo? (indicador do HUD)

// dispara na direção atual do jogador (faceX/faceY), em leque conforme o poder
void SHOTS_firePlayer(void);

// avança projéteis do jogador, testa acerto em inimigos;
// devolve quantos inimigos foram mortos neste frame (para o contador)
u16 SHOTS_updatePlayer(void);

// avança projéteis inimigos e testa acerto no jogador
void SHOTS_updateEnemy(void);

// dispara projétil(is) inimigo(s) mirado(s) no jogador — usado pelos comportamentos
// style1..4 identifies the firing species; stored in mode for enemy shots only.
void SHOTS_enemyTarget(s16 x,s16 y);
void fireEnemyShot(s16 ex, s16 ey, u8 style);
void fireEnemySpread(s16 ex, s16 ey, u8 count, u8 style);
void fireEnemySpreadDmg(s16 ex, s16 ey, u8 count, u8 dmg, u8 style);

#endif // SHOTS_H
