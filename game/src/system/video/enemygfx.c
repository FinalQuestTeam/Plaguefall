// Gera os tiles dos inimigos (insetos), a partir dos char-maps (insects_data.h).
// Rotação por vizinho-mais-próximo. A cor do corpo vem da família (PAL1).
//
// Só 3 direções são GERADAS na VRAM — N (0), NE (1) e E (2). As outras 5 saem por
// ESPELHAMENTO de hardware do sprite (bits H/V-flip), pois são reflexões dessas:
//   S=vflip(N)  SE=vflip(NE)  W=hflip(E)  NW=hflip(NE)  SW=hflip+vflip(NE)
// Isso corta o custo em VRAM de 8 → 3 direções (−62%). O CHEFE é a exceção: como
// é desenhado em 4 quadrantes manuais, mantém as 8 direções (flipar exigiria
// trocar as posições dos quadrantes).

#include "system/video/enemygfx.h"
#include "system/video/sprites/tiles.h"
#include "system/video/sprites/insects_data.h"
#include "enemies/enemies.h"
#include "levels/levels.h"              // LEVEL_typeLastPhase()

static const s16 COS8[8] = { 256, 181,   0, -181, -256, -181,    0,  181 };
static const s16 SIN8[8] = {   0, 181, 256,  181,    0, -181, -256, -181 };

// Cada direção 0..7 → qual das 3 geradas usar (N=0/NE=1/E=2) + flips de hardware.
//   dir:      N   NE  E   SE  S   SW  W   NW
#define GEN_DIRS 3
static const u8 DIR_SLOT [8] = { 0,  1,  2,  1,  0,  1,  2,  1 };
static const u8 DIR_HFLIP[8] = { 0,  0,  0,  0,  0,  1,  1,  1 };
static const u8 DIR_VFLIP[8] = { 0,  0,  0,  1,  1,  1,  0,  0 };

// Pools de slots por TAMANHO (16/24/32px). Slots uniformes dentro do pool evitam
// fragmentação. Cada tipo é gerado 1× e reaproveitado; quando um tipo não aparece
// mais em nenhuma fase futura (morto), seu slot pode ser tomado por outro. As
// contagens vêm do pico de tipos vivos simultâneos ao longo das 15 fases (só 3
// direções por tipo — ver topo do arquivo):
//   pequenos(12t): 5   médios(27t): 3   grandes(48t): 2
//   → 5×12 + 3×27 + 2×48 = 237 tiles = ENEMY_ROT_COUNT
// Quadros de animação por direção. Cada tipo comum guarda ANIM_FRAMES quadros
// (layout: quadro-maior, depois direção). Protótipo: só o besouro tem 2º quadro
// distinto; os demais duplicam o quadro A (custam a VRAM, mas não animam ainda).
#define ANIM_FRAMES     2
#define SLOT_TILES_S    (ANIM_FRAMES * GEN_DIRS * 4)      // 16px: 2×3×4  = 24
#define SLOT_TILES_M    (ANIM_FRAMES * GEN_DIRS * 9)      // 24px: 2×3×9  = 54
#define SLOT_TILES_L    (ANIM_FRAMES * GEN_DIRS * 16)     // 32px: 2×3×16 = 96
#define SLOTS_S 5
#define SLOTS_M 3
#define SLOTS_L 2
#define NO_OCC  0xFF                    // slot vazio

typedef struct { u8 occ; u16 base; } Slot;   // occ = tipo ocupante (ou NO_OCC)
static Slot slotsS[SLOTS_S], slotsM[SLOTS_M], slotsL[SLOTS_L];
static u16  enemyBase[ENEMY_TYPES];     // tile base (dir 0) atual de cada tipo
static bool resident[ENEMY_TYPES];      // tipo está num slot da VRAM agora?
static bool poolsReady;

// cor (índice PAL1) do corpo pela COR de comportamento
static u16 bodyColor(u8 color)
{
    switch (color)
    {
        case COLOR_RED:    return 3;
        case COLOR_YELLOW: return 4;
        case COLOR_PURPLE: return 8;
        case COLOR_ORANGE: return 12;
        case COLOR_GRAY:   return 13;
    }
    return 1;
}

// char-map do inseto pela forma+tamanho (quadrado=besouro, triângulo=mosca,
// pentágono=aranha)
static const char *const *pickArt(u8 shape, u16 size)
{
    switch (shape)
    {
        case SHAPE_TRIANGLE: return INS_FLY16;
        case SHAPE_PENTAGON: return (size >= 32) ? INS_SPIDER32 : INS_SPIDER24;
        default:             return (size >= 32) ? INS_BEETLE32
                                  : (size >= 24) ? INS_BEETLE24 : INS_BEETLE16;
    }
}

// char-map de um QUADRO de animação. Quadro 0 = pose base (pickArt). Quadro 1 =
// pose alternada por forma: besouro/aranha = pernas retraídas, mosca = asas
// erguidas. (O chefe não passa por aqui: 1 quadro só.)
static const char *const *frameArt(u8 shape, u16 size, u8 frame)
{
    if (frame == 0) return pickArt(shape, size);
    switch (shape)
    {
        case SHAPE_TRIANGLE: return INS_FLY16_B;                 // mosca
        case SHAPE_PENTAGON: return (size >= 32) ? INS_SPIDER32_B : INS_SPIDER24_B;
        default:             return (size >= 32) ? INS_BEETLE32_B
                                  : (size >= 24) ? INS_BEETLE24_B : INS_BEETLE16_B;
    }
}

// caractere do char-map → índice de cor (PAL1); 0xFFFF = vazio
static u16 colorOf(char ch, u16 body)
{
    switch (ch)
    {
        case 'b': return body;      // corpo (cor da família)
        case 'o': return 11;        // contorno escuro
        case 'h': return 1;         // brilho branco
        case 'w': return 7;         // asa cinza-claro
        case 'e': return 11;        // olho escuro
        case 'l': return 6;         // pata cinza-azulada
    }
    return 0xFFFF;                  // '.' vazio
}

// pinta o char-map rotacionado por `dir` em (size/8)² tiles (ordem coluna),
// a partir de baseTile no buffer
static void paintRot(u32 *buf, u16 baseTile, const char *const *art,
                     u16 size, u16 body, u8 dir)
{
    const s16 c = COS8[dir], s = SIN8[dir];
    const s16 mid = (s16) (size - 1);
    const u16 colTiles = size / 8;

    for (u16 oy = 0; oy < size; oy++)
    {
        for (u16 ox = 0; ox < size; ox++)
        {
            const s16 dx = (s16) (2 * ox - mid);
            const s16 dy = (s16) (2 * oy - mid);
            const s16 sx = (s16) (((( dx * c + dy * s) >> 8) + mid) >> 1);
            const s16 sy = (s16) ((((-(dx * s) + dy * c) >> 8) + mid) >> 1);
            if ((sx < 0) || (sx >= (s16) size) || (sy < 0) || (sy >= (s16) size)) continue;

            const u16 col = colorOf(art[sy][sx], body);
            if (col == 0xFFFF) continue;

            // 48x48 (chefe): layout em 4 quadrantes 24x24 (3x3 tiles) → desenhado
            // como 4 sprites (o hardware não faz sprite > 32x32). Demais: coluna.
            u16 tile;
            if (size == 48)
            {
                const u16 q = (u16) ((oy / 24) * 2 + (ox / 24));
                tile = baseTile + q * 9 + ((ox % 24) / 8) * 3 + ((oy % 24) / 8);
            }
            else tile = baseTile + (ox / 8) * colTiles + (oy / 8);

            buf[tile * 8 + (oy % 8)] |= (u32) col << ((7 - (ox % 8)) * 4);
        }
    }
}

// bases fixas dos slots de cada pool na região ENEMY_ROT (sequenciais e estáveis)
static void initPools(void)
{
    u16 base = ENEMY_ROT_BASE;
    for (u8 i = 0; i < SLOTS_S; i++) { slotsS[i].occ = NO_OCC; slotsS[i].base = base; base += SLOT_TILES_S; }
    for (u8 i = 0; i < SLOTS_M; i++) { slotsM[i].occ = NO_OCC; slotsM[i].base = base; base += SLOT_TILES_M; }
    for (u8 i = 0; i < SLOTS_L; i++) { slotsL[i].occ = NO_OCC; slotsL[i].base = base; base += SLOT_TILES_L; }
    poolsReady = TRUE;
}

// pool (e nº de slots) para o tamanho do inseto
static Slot *poolFor(u16 size, u8 *n)
{
    if (size <= 16) { *n = SLOTS_S; return slotsS; }
    if (size <= 24) { *n = SLOTS_M; return slotsM; }
    *n = SLOTS_L; return slotsL;
}

// escolhe um slot no pool para a fase `phase`: 1) vazio; 2) ocupante MORTO
// (última fase < phase → nunca mais aparece); 3) segurança: o de menor "última
// fase" (regenera depois se voltar — não deve ocorrer com os pools dimensionados)
static Slot *pickSlot(Slot *pool, u8 n, u8 phase, const u8 *last)
{
    for (u8 i = 0; i < n; i++) if (pool[i].occ == NO_OCC) return &pool[i];
    for (u8 i = 0; i < n; i++) if (last[pool[i].occ] < phase) return &pool[i];
    Slot *worst = &pool[0];
    for (u8 i = 1; i < n; i++) if (last[pool[i].occ] < last[worst->occ]) worst = &pool[i];
    return worst;
}

// gera as rotações de UM tipo no seu slot atual (enemyBase[t]): 3 direções
// (N/NE/E) para os inimigos comuns; 8 para o CHEFE (quadrantes, sem flip)
static void genType(u8 t)
{
    const EnemyDef *d = ENEMY_DEFS[t];
    const u16 size = d->size;
    const u16 tpd  = (size / 8) * (size / 8);   // tiles por direção
    // chefe: 8 direções (sem flip); comuns: 3 direções (N/NE/E). Ambos ANIM_FRAMES.
    const u8  ndir = (t == ENEMY_BOSS) ? 8 : GEN_DIRS;
    const u8  nfr  = ANIM_FRAMES;
    const u16 count = nfr * ndir * tpd;

    const u16 body = bodyColor(d->color);

    u32 *buf = MEM_alloc(count * 8 * (u16) sizeof(u32));
    memset(buf, 0, count * 8 * (u16) sizeof(u32));
    for (u8 f = 0; f < nfr; f++)
    {
        const char *const *art = (t == ENEMY_BOSS) ? (f ? INS_BOSS48_B : INS_BOSS48)
                                                    : frameArt(d->shape, size, f);
        for (u8 dir = 0; dir < ndir; dir++)
            paintRot(buf, (f * ndir + dir) * tpd, art, size, body, dir);
    }
    VDP_loadTileData(buf, TILE_USER_INDEX + enemyBase[t], count, DMA);
    MEM_free(buf);
}

void ENEMYGFX_loadForPhase(u8 phase, const u8 *types, u16 count)
{
    if (!poolsReady) initPools();
    const u8 *last = LEVEL_typeLastPhase();     // última fase de cada tipo (0 = nunca)

    for (u16 i = 0; i < count; i++)
    {
        const u8 t = types[i];
        if (resident[t]) continue;              // já na VRAM: reaproveita

        // CHEFE (48x48): região dedicada, fora dos pools
        if (t == ENEMY_BOSS)
        {
            enemyBase[t] = BOSS_ROT_BASE;
            genType(t);
            resident[t] = TRUE;
            continue;
        }

        u8 n;
        Slot *pool = poolFor(ENEMY_DEFS[t]->size, &n);
        Slot *s = pickSlot(pool, n, phase, last);
        if (s->occ != NO_OCC) resident[s->occ] = FALSE;   // descarta o ocupante

        enemyBase[t] = s->base;
        genType(t);
        s->occ = t;
        resident[t] = TRUE;
    }
}

void ENEMYGFX_reset(void)
{
    poolsReady = FALSE;                 // initPools() zera os slots na próxima carga
    for (u16 t = 0; t < ENEMY_TYPES; t++) resident[t] = FALSE;
}

u16 ENEMYGFX_dirTile(u8 type, u8 dir, u8 frame)
{
    const u16 size = ENEMY_DEFS[type]->size;
    const u16 tpd = (size / 8) * (size / 8);
    // chefe: 8 direções diretas (layout quadro-maior, depois direção)
    if (type == ENEMY_BOSS) return enemyBase[type] + (frame * 8 + dir) * tpd;
    // demais: 3 direções geradas (5 via flip), layout quadro-maior, depois direção
    return enemyBase[type] + (frame * GEN_DIRS + DIR_SLOT[dir]) * tpd;
}

// bits de espelhamento da direção (0 no chefe, que tem as 8 direções geradas)
u8 ENEMYGFX_dirFlipH(u8 type, u8 dir) { return (type == ENEMY_BOSS) ? 0 : DIR_HFLIP[dir]; }
u8 ENEMYGFX_dirFlipV(u8 type, u8 dir) { return (type == ENEMY_BOSS) ? 0 : DIR_VFLIP[dir]; }

void ENEMYGFX_drawOnMap(u8 type, u16 col, u16 row)
{
    const u16 nt = ENEMY_DEFS[type]->size / 8;      // tiles por lado (2/3/4)
    const u16 base = ENEMYGFX_dirTile(type, 0, 0);  // direção 0, quadro 0 = de frente
    for (u16 tc = 0; tc < nt; tc++)
        for (u16 tr = 0; tr < nt; tr++)
            VDP_setTileMapXY(BG_A,
                TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_USER_INDEX + base + tc * nt + tr),
                col + tc, row + tr);
}

u8 ENEMYGFX_faceDir(s16 dx, s16 dy)
{
    const s16 adx = dx < 0 ? -dx : dx;
    const s16 ady = dy < 0 ? -dy : dy;
    if (adx * 2 < ady) return dy < 0 ? 0 : 4;   // vertical: cima / baixo
    if (ady * 2 < adx) return dx > 0 ? 2 : 6;   // horizontal: direita / esquerda
    if (dx > 0)        return dy < 0 ? 1 : 3;   // diagonais à direita
    return               dy < 0 ? 7 : 5;        // diagonais à esquerda
}
