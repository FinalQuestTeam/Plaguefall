#ifndef ENEMIES_H
#define ENEMIES_H

#include <genesis.h>

#define MAX_ENEMIES     16      // tamanho do vetor (Alcateia divide e Fortaleza invoca)
#define ENEMY_CAP       15      // teto de inimigos ativos: só nasce novo se abrir vaga

// índice de cada inimigo em ENEMY_DEFS[] (== campo Enemy.type)
// Grade 4 cores × 3 formas. Cor = comportamento; forma = perfil.
#define ENEMY_SQ_RED    0       // Torreão   — quadrado atirador
#define ENEMY_SQ_YEL    1       // Batedor   — quadrado perseguidor
#define ENEMY_SQ_PUR    2       // Baluarte  — quadrado blindado (tanque)
#define ENEMY_SQ_ORG    3       // Aríete    — quadrado investida
#define ENEMY_TRI_RED   4       // Fuzileiro — triângulo atirador
#define ENEMY_TRI_YEL   5       // Caçador   — triângulo perseguidor
#define ENEMY_TRI_PUR   6       // Escudeiro — triângulo blindado
#define ENEMY_TRI_ORG   7       // Adaga     — triângulo investida
#define ENEMY_PEN_RED   8       // Artilheiro— pentágono atirador (leque)
#define ENEMY_PEN_YEL   9       // Alcateia  — pentágono perseguidor (divide)
#define ENEMY_PEN_PUR   10      // Fortaleza — pentágono blindado (invoca)
#define ENEMY_PEN_ORG   11      // Meteoro   — pentágono investida (teleporta)
#define ENEMY_DUMMY     12      // alvo de teste — parado, HP 20 (só na fase teste 1)
#define ENEMY_TARGET    13      // alvo frágil — parado, HP 1 (fase teste 2, p/ o raio)
#define ENEMY_BOSS      14      // CHEFE (Besouro) — bônus da última fase / fase teste 3
#define ENEMY_TYPES     15

// aliases retrocompatíveis (os 3 originais)
#define ENEMY_RED       ENEMY_SQ_RED
#define ENEMY_YELLOW    ENEMY_SQ_YEL
#define ENEMY_PURPLE    ENEMY_SQ_PUR

// formas — perfil de resistência/agressividade
#define SHAPE_SQUARE    0       // mais resistente
#define SHAPE_TRIANGLE  1       // mais agressivo/frágil
#define SHAPE_PENTAGON  2       // elite (+ truque extra)

// cores — comportamento base (legível pelo jogador só pela cor)
#define COLOR_RED       0       // atirador
#define COLOR_YELLOW    1       // perseguidor
#define COLOR_PURPLE    2       // blindado (escudo cíclico)
#define COLOR_ORANGE    3       // investida (dash)
#define COLOR_GRAY      4       // neutra (dummy de teste)

// truque extra do pentágono
#define EXTRA_NONE      0
#define EXTRA_SPREAD    1       // leque de tiros (vermelho)
#define EXTRA_SPLIT     2       // divide-se ao morrer (amarelo)
#define EXTRA_SUMMON    3       // invoca lacaios enquanto blindado (roxo)
#define EXTRA_TELEPORT  4       // teleporta antes de investir (laranja)

// parâmetros de perseguição
#define ENEMY_SPEED_FP  40      // ~0,63 px/frame em 26.6 (base)
#define RETARGET_FRAMES 16      // recalcula a direção a cada N frames

// brilho branco ao tomar dano (feedback visual): frames que o inimigo é desenhado
// com a paleta de flash (PAL0 branca) logo após um acerto que não o mata
#define HIT_FLASH_FRAMES 4

// separação anti-empilhamento (steering "separation"): inimigos muito próximos
// se afastam devagar, permitindo sobreposição parcial mas nunca total.
// A distância mínima entre centros = (ha+hb) * SEP_MIN_NUM / (1<<SEP_MIN_SHIFT).
// Fração com denominador potência de 2 → só mult + shift no laço (SEM divisão,
// caríssima no 68000). 3/4 ≈ 25% de sobreposição permitida (leve).
#define SEP_MIN_NUM     3       // numerador do fator de distância mínima
#define SEP_MIN_SHIFT   2       // denominador = 1<<SEP_MIN_SHIFT (aqui 4)
#define SEP_STRENGTH    4       // ganho do empurrão (26.6) por px de sobreposição
#define SEP_MAX         20      // teto do empurrão por inimigo/quadro (26.6 → ~0,3 px)

// resultado de ENEMIES_damageBox
#define ENEMY_HIT_NONE      0
#define ENEMY_HIT_DAMAGED   1   // acertou (ou escudo bloqueou), inimigo sobreviveu
#define ENEMY_HIT_KILLED    2

// status aplicável ao inimigo pelo tiro (modos gelo/fogo)
#define ENEMY_STATUS_NONE   0
#define ENEMY_STATUS_FREEZE 1   // congelado (parado, azulado) por ICE_FREEZE_SEC
#define ENEMY_STATUS_BURN   2   // queimando (dano por tempo) por FIRE_BURN_SEC

typedef struct
{
    s16 x, y;               // posição em pixels (derivada de fx/fy)
    s32 fx, fy;             // posição 26.6
    s16 vx, vy;             // velocidade 26.6 por frame
    u16 fireTimer;          // cadência de tiro (cor vermelha)
    u16 retarget;           // recalcular direção de perseguição
    u16 stun;               // frames de recuo após colidir com o jogador
    u16 mudTime;            // frames seguidos pisando na lama
    u16 tA, tB;             // temporizadores do comportamento (escudo, dash, invocação)
    u8  mode;               // sub-estado (aproximar/telegrafar/investir; etc.)
    u8  slowPct;            // lentidão atual em % (aplicada por elementos)
    u8  type;               // índice em ENEMY_DEFS[]
    u8  hp;                 // tiros restantes para morrer
    u16 frozen;             // gelo: frames parado/azulado restantes (0 = normal)
    u16 burn;               // fogo: frames de queimadura restantes (0 = sem queimar)
    u16 burnTick;           // frames até o próximo dano da queimadura
    u16 hitFlash;           // frames restantes do brilho branco ao tomar dano
    u16 burnFlash;          // frames restantes do pulso vermelho a cada dano do fogo
    bool shielded;          // roxo: invulnerável enquanto o escudo está erguido
    bool aggroPlayer;       // PROTEGER: persegue o JOGADOR em vez do aliado (aggro dividido)
    bool active;
} Enemy;

// Definição (configuração) de um inimigo — uma por arquivo em enemies/defs/.
// Concentra todos os "botões" de ajuste; a lógica fica nas funções por cor.
// timerA/timerB são em DÉCIMOS DE SEGUNDO (convertidos por fps no comportamento).
typedef struct EnemyDef
{
    const char *name;
    u8  shape;          // SHAPE_*
    u8  color;          // COLOR_*  (== comportamento base)
    u8  size;           // 16 / 24 / 32 (lado do sprite em px)
    u8  hp;             // tiros para morrer
    u8  contactDmg;     // dano de contato no jogador
    u8  dropChance;     // % de derrubar item ao morrer por tiro
    u16 speedFp;        // velocidade de perseguição/dash (26.6); 0 = fixo
    u16 timerA, timerB; // cadências (0,1 s): tiro / escudo-off / dash-cooldown etc.
    u8  extra;          // EXTRA_* (truque do pentágono)
    void (*behavior)(Enemy *e, const struct EnemyDef *def);
} EnemyDef;

// tabela indexada por tipo (montada em enemies.c a partir dos arquivos defs/)
extern const EnemyDef *const ENEMY_DEFS[ENEMY_TYPES];

#define ENEMY_DEF(e)    (ENEMY_DEFS[(e)->type])
#define ENEMY_SIZE(e)   (ENEMY_DEF(e)->size)
// Yellow/purple logic runs in four cohorts; velocities/timers remain per frame.
// Red, orange, targets and boss retain the full update rate.
#define ENEMY_UPDATE_STEP(e) (((e)->type<12 && (((e)->type+1)&2)) ? 4 : 1)

extern Enemy enemies[MAX_ENEMIES];

// desativa todos os inimigos
void ENEMIES_clear(void);
bool ENEMIES_testKill(u16 index); // training-only preview through real death path

// tenta criar um inimigo longe do jogador, sorteado entre os tipos permitidos
void ENEMIES_trySpawn(const u8 *types, u8 typeCount);

// cria um inimigo do tipo dado numa posição específica (usado por divisão/invocação)
void ENEMIES_spawnAt(u8 type, s16 x, s16 y);

// quantos inimigos estão ativos (usado pela fase teste)
u16 ENEMIES_activeCount(void);

// centro do alvo de perseguição (jogador por padrão; NPC no objetivo PROTEGER)
extern s16 chaseX, chaseY;
void ENEMIES_setChaseTarget(s16 cx, s16 cy);

// PROTEGER: 1 a cada `n` inimigos persegue o JOGADOR em vez do aliado (0 = nenhum)
void ENEMIES_setAggroSplit(u8 n);

// empurra o inimigo para longe de (fromX,fromY) com stun (recuo/onda de choque)
void ENEMIES_knockbackFrom(Enemy *e, s16 fromX, s16 fromY);

// comportamento de todos os inimigos ativos + dano por contato + status
// (congelado/queimando). Retorna quantos morreram pela QUEIMADURA neste frame.
u16 ENEMIES_update(void);

// aplica um acerto (AABB w x h em x,y) no primeiro inimigo atingido, e um
// ENEMY_STATUS_* (congelar/queimar) se ele sobreviver.
// retorna ENEMY_HIT_NONE / ENEMY_HIT_DAMAGED / ENEMY_HIT_KILLED
u16 ENEMIES_damageBox(s16 x, s16 y, s16 w, s16 h, u8 status);

// mata todos os inimigos ativos (bomba); sem drop de itens;
// retorna quantos morreram
u16 ENEMIES_killAll(void);

// reação em cadeia (item raio): 1 de dano em até `maxTargets` inimigos dentro
// de `range` px de (cx, cy); retorna quantos morreram (com drop/divisão)
u16 ENEMIES_chainDamage(s16 cx, s16 cy, u8 maxTargets, u16 range);

// helpers de movimento (26.6, contidos na arena)
void ENEMIES_chase(Enemy *e, u16 speedFp);  // recalcula direção e integra
void ENEMIES_integrate(Enemy *e);           // só integra vx/vy e contém na arena

// comportamentos por cor (enemy_red/yellow/purple/orange.c)
void ENEMYRED_update(Enemy *e, const EnemyDef *def);     // atirador
void ENEMYYELLOW_update(Enemy *e, const EnemyDef *def);  // perseguidor
void ENEMYPURPLE_update(Enemy *e, const EnemyDef *def);  // blindado
void ENEMYORANGE_update(Enemy *e, const EnemyDef *def);  // investida
void ENEMYDUMMY_update(Enemy *e, const EnemyDef *def);   // alvo parado (no-op)
void ENEMYBOSS_update(Enemy *e, const EnemyDef *def);    // chefe (Besouro)

#endif // ENEMIES_H
