#ifndef ITEMS_H
#define ITEMS_H

#include <genesis.h>

#define MAX_ITEMS       8

// tipos de item
#define ITEM_HEART      0   // coração: cura 15 de vida (item_heart.c)
#define ITEM_BOMB       1   // carga de bomba (item_bomb.c)
#define ITEM_SHOTS      2   // bala: +1 disparo em leque, até 5 (item_shots.c)
#define ITEM_SPEED      3   // botinha: +20% velocidade, até +100% (item_speed.c)
#define ITEM_SHIELD     4   // escudo: invencibilidade por 3 s (item_shield.c)
#define ITEM_CHAIN      5   // raio: próximos 5 acertos em cadeia (item_chain.c)
#define ITEM_ICE        6   // gelo: 3 tiros que congelam o inimigo por 5 s (item_ice.c)
#define ITEM_FIRE       7   // fogo: 4 tiros que queimam (dano por tempo) (item_fire.c)
#define ITEM_BAG        8   // equipamento pré-morte, com recuperação conforme a etapa
#define ITEM_DROP_TYPES 8   // itens comuns; a bolsa não entra no sorteio/treino
#define ITEM_TYPES      9
#define ITEM_TTL_FOREVER 0xFFFF

// itens que vão para o INVENTÁRIO (ativados com B, trocados com C) em vez de
// aplicar na coleta. A bomba ocupa a posição 0 (espelha BOMB_count()).
#define ITEM_IS_INVENTORY(t) \
    ((t) == ITEM_BOMB || (t) == ITEM_CHAIN || (t) == ITEM_SHIELD || \
     (t) == ITEM_ICE  || (t) == ITEM_FIRE)

typedef struct
{
    s16 x, y;               // posição (16x16)
    u16 ttl;                // frames até desaparecer
    u8 type;
    bool active;
} Item;

// legenda de cores para o desenho por caracteres (char -> índice de cor PAL1)
typedef struct { char ch; u16 color; } TilePixel;

// Definição (configuração) de um item — uma por arquivo em items/.
// Concentra os "botões" de ajuste: peso do drop, ícone e efeito.
typedef struct
{
    const char *name;
    u8  weight;                         // peso no sorteio de qual item cai (%)
    u16 tile;                           // tile base do ícone (16x16)
    void (*buildTile)(u32 *tileBuf);    // gera o tile procedural
    void (*apply)(void);                // efeito ao coletar
} ItemDef;

// tabela indexada por tipo (registro em items.c; dado em items/defs/*.c)
extern const ItemDef *const ITEM_DEFS[ITEM_TYPES];

extern Item items[MAX_ITEMS];

// pinta um tile 16x16 (4 tiles) a partir de um mapa 16x16 de caracteres e uma
// legenda de cores — método ÚNICO de desenho de todos os itens
void ITEMS_paintTile16(u32 *tileBuf, u16 baseTile,
                       const char *const rows[16],
                       const TilePixel *legend, u8 legendCount);

// desenha os tiles dos itens no buffer de tiles procedurais
void ITEMS_buildTiles(u32 *tileBuf);

// remove todos os itens do chão
void ITEMS_clear(void);

// chamado quando um inimigo morre em (cx, cy) (centro): sorteia a chance de
// drop do tipo de inimigo e, se cair, qual item aparece (peso por item)
void ITEMS_tryDrop(s16 cx, s16 cy, u8 enemyType);

// TTL e coleta pelo jogador
void ITEMS_update(void);

// coloca um item na posição (x, y) com vida longa (usado pela fase teste)
void ITEMS_spawnAt(u8 type, s16 x, s16 y);

// fase teste (items/test_items.c): garante 1 de cada tipo no chão; reset zera o
// estado de reabastecimento (chamado por ITEMS_clear)
void ITEMS_testEnsure(void);
void ITEMS_testReset(void);

// adiciona os sprites dos itens à cadeia (recebe e retorna o índice corrente)
u16 ITEMS_draw(u16 n);

// efeitos por tipo (item_heart.c, item_bomb.c, item_shots.c, ...)
void ITEMHEART_buildTile(u32 *tileBuf);
void ITEMHEART_apply(void);
void ITEMBOMB_buildTile(u32 *tileBuf);
void ITEMBOMB_apply(void);
void ITEMSHOTS_buildTile(u32 *tileBuf);
void ITEMSHOTS_apply(void);
void ITEMSPEED_buildTile(u32 *tileBuf);
void ITEMSPEED_apply(void);
void ITEMSHIELD_buildTile(u32 *tileBuf);
void ITEMSHIELD_apply(void);
void ITEMCHAIN_buildTile(u32 *tileBuf);
void ITEMCHAIN_apply(void);
void ITEMICE_buildTile(u32 *tileBuf);
void ITEMICE_apply(void);
void ITEMFIRE_buildTile(u32 *tileBuf);
void ITEMFIRE_apply(void);
void ITEMBAG_buildTile(u32 *tileBuf);
void ITEMBAG_apply(void);

#endif // ITEMS_H
