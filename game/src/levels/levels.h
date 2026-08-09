#ifndef LEVELS_H
#define LEVELS_H

#include <genesis.h>
#include "elements/elements.h"
#include "enemies/enemies.h"
#include "system/video/floor.h"        // FLOOR_STONE / FLOOR_FOREST

#define LEVEL_COUNT     16      // 1..15 campanha + 16 = chefe (Lacraia)

// objetivos de fase (campo LevelDef.objective; ver core/objective.c)
#define OBJ_KILL        0       // matar killTarget inimigos (padrão)
#define OBJ_SURVIVE     1       // sobreviver objTarget segundos
#define OBJ_COLLECT     2       // coletar objTarget itens
#define OBJ_PROTECT     3       // proteger o aliado (NPC) por objTarget segundos

// descrição de uma fase: elementos, condições de vitória e regras de spawn
typedef struct
{
    const TileRect *lava;   // retângulos de lava (NULL se não houver)
    u16 lavaCount;
    const TileRect *mud;    // poças de lama (NULL se não houver)
    u16 mudCount;
    u16 killTarget;         // inimigos a matar para completar a fase
    u8 spawnSeconds;        // intervalo de aparição de inimigos (segundos)
    u8 spawnCount;          // inimigos por aparição (0/1 = simples, 2 = duplas...)
    const u8 *enemyTypes;   // tipos de inimigo que aparecem na fase
    u8 enemyTypeCount;
    u8 floor;               // chão da arena: FLOOR_STONE (0, padrão) ou FLOOR_FOREST
    u8 objective;           // OBJ_* (0 = OBJ_KILL, padrão)
    u16 objTarget;          // segundos (SURVIVE/PROTECT) ou itens (COLLECT)
    u8 collectItem;         // OBJ_COLLECT: qual item conta (ITEM_*); só ele conta
    s16 npcX, npcY;         // posição do aliado (OBJ_PROTECT; 0,0 = centro)
    u16 npcHp;              // vida do aliado (OBJ_PROTECT; 0 = padrão)
    // curva de BPM da música (0 em cada campo = usa o padrão global de music.h).
    // Deixa ajustar o "perigo" sonoro por fase (ex.: chefe já começa agressivo).
    u8 musCalmUntil;       // inimigos até a música ficar calma
    u8 musEnemyMax;        // inimigos que leva ao BPM máximo
    u8 musStepCalm;        // frames/passo calmo   (BPM = 900/frames; maior = + lento)
    u8 musStepHot;         // frames/passo no perigo (menor = + rápido)
} LevelDef;

// uma fase por arquivo em levels/defs/ (level01.c .. level16.c)
extern const LevelDef
    LEVEL01_def, LEVEL02_def, LEVEL03_def, LEVEL04_def, LEVEL05_def,
    LEVEL06_def, LEVEL07_def, LEVEL08_def, LEVEL09_def, LEVEL10_def,
    LEVEL11_def, LEVEL12_def, LEVEL13_def, LEVEL14_def, LEVEL15_def,
    LEVEL16_def;

// fases teste (dados em levels/defs/test.c; lógica em levels/test.c)
extern const LevelDef TEST_def, TEST2_def, TEST3_def, TEST4_def, TEST5_def, TEST6_def;

// terrenos reutilizáveis (definidos em levels/layouts.c) — todos com 2 retângulos.
// LAVA/MUD_PAIR: um elemento por fase. COMBO_*: lava e lama juntas (cantos opostos).
#define LAYOUT_RECTS    2
extern const TileRect LAVA_PAIR[LAYOUT_RECTS], MUD_PAIR[LAYOUT_RECTS];
extern const TileRect COMBO_LAVA[LAYOUT_RECTS], COMBO_MUD[LAYOUT_RECTS];

// atalho para preencher o roster de inimigos de uma fase
#define LVL_ROSTER(a)   .enemyTypes = (a), .enemyTypeCount = (sizeof(a) / sizeof((a)[0]))

extern u8 currentLevel;         // 1..LEVEL_COUNT (0 = fase teste)
extern u8 testStage;            // fase teste: 1 (dummy) ou 2 (alvos p/ o raio)

// definição da fase atual
const LevelDef *LEVEL_current(void);

// desenha a fase n SEM zerar os elementos (usado ao retomar do pause)
void LEVEL_draw(u8 n);

// desenha a fase n e zera o estado dos elementos (começar/recomeçar)
void LEVEL_load(u8 n);

// gera na VRAM só a arte dos inimigos da fase n (por etapas; use antes de mostrar
// os sprites da fase, ex.: na tela de preparação). LEVEL_load já chama isto.
void LEVEL_loadGfx(u8 n);

// vetor [ENEMY_TYPES]: última fase (1..LEVEL_COUNT) em que cada tipo aparece
// (0 = nunca). Usado pelo descarte de sprites de inimigo por vida (enemygfx.c).
const u8 *LEVEL_typeLastPhase(void);

// atualização por frame dos elementos da fase atual (ex.: dano da lava)
void LEVEL_update(void);

// zera o estado dos elementos
void LEVEL_reset(void);

// escreve as condições/informações da fase n em 3 linhas a partir de (x, y):
// meta de mortes, intervalo de spawn e lista de inimigos
void LEVEL_drawInfo(u8 n, u16 x, u16 y);

#endif // LEVELS_H
