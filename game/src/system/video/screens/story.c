// Tela de história — ver story.h (desta pasta). O roteiro vem de
// levels/story.c; a arte dos retratos de sprites/portraits_data.h.
//
// VRAM: os 2 retratos (36 tiles cada) são pintados na região do CHEFE
// (BOSS_ROT, livre fora da luta) — custo residente zero; ao fim da cena o
// cache do chefe é invalidado (ENEMYGFX_dropBoss) e regenera quando preciso.
// Paletas: retrato esquerdo em PAL2, direito em PAL3 (o início de fase
// restaura as duas: CHARS_load recarrega PAL2 e FLOOR_draw recarrega PAL3).

#include "system/video/screens/story.h"
#include "levels/story.h"
#include "system/video/sprites/tiles.h"         // BOSS_ROT_BASE
#include "system/video/sprites/portraits_data.h"
#include "system/video/spritelist.h"
#include "system/video/enemygfx.h"              // ENEMYGFX_dropBoss
#include "system/video/floor.h"
#include "system/audio/music.h"
#include "system/audio/sfx.h"                   // sfxItemPickup (blip da "voz")
#include "core/game.h"

// layout (tela 40x28): retrato ESQ em cima, DIR embaixo; caixas de 26 colunas
#define PORT_TILES      36          // 48x48 = 6x6 tiles
#define PORT_BASE       BOSS_ROT_BASE
#define ESQ_PX 2
#define ESQ_PY 2                    // retrato ESQ: (2,2)-(7,7)
#define ESQ_TX 9
#define ESQ_TY 2                    // nome na linha 2; texto nas linhas 4..7
#define DIR_PX 32
#define DIR_PY 19                   // retrato DIR: (32,19)-(37,24)
#define DIR_TX 4
#define DIR_TY 19                   // nome na linha 19; texto nas linhas 21..24
#define BOX_W  26                   // largura da caixa de texto (colunas)
#define BOX_H  4                    // linhas por fala
#define TYPE_SPEED 2                // letras por quadro (máquina de escrever)

static u32 seen[2];                 // cenas vistas no run: [ANTES]/[DEPOIS], bit = nó

static const StoryEntry *cur;       // cena em curso
static u8  lineIdx;                 // fala atual
static u8  slotPortrait[2];         // retrato carregado em cada canto (0xFF = nenhum)

static char wrapBuf[BOX_H][BOX_W + 1];  // fala atual quebrada por palavra
static u8  wrapLines;
static u16 typed, typeTotal;        // progresso da máquina de escrever
static u16 blinkTimer;
static bool blinkOn;

void STORYSCR_reset(void)
{
    seen[ANTES] = 0;
    seen[DEPOIS] = 0;
}

// ---------------------------------------------------------------------------
// Retratos (char-map 48x48 → 36 tiles na região emprestada do chefe)
// ---------------------------------------------------------------------------

static void loadPortrait(u8 slot, u8 which)
{
    if (slotPortrait[slot] == which) return;
    slotPortrait[slot] = which;

    u32 *buf = MEM_alloc(PORT_TILES * 8 * (u16) sizeof(u32));
    memset(buf, 0, PORT_TILES * 8 * (u16) sizeof(u32));

    const char *const *art = PORTRAIT_ART[which];
    for (u16 oy = 0; oy < 48; oy++)
    {
        for (u16 ox = 0; ox < 48; ox++)
        {
            const char ch = art[oy][ox];
            if (ch == '0') continue;
            const u16 col = (ch <= '9') ? (u16) (ch - '0') : (u16) (ch - 'a' + 10);
            const u16 tile = (oy / 8) * 6 + (ox / 8);
            buf[tile * 8 + (oy % 8)] |= (u32) col << ((7 - (ox % 8)) * 4);
        }
    }
    VDP_loadTileData(buf, TILE_USER_INDEX + PORT_BASE + slot * PORT_TILES,
                     PORT_TILES, DMA);
    MEM_free(buf);

    // ESQ usa PAL2, DIR usa PAL3 (restauradas pelo início de fase)
    PAL_setColors((u16) ((slot ? PAL3 : PAL2) * 16), PORTRAIT_PAL[which], 16, DMA);

    const u16 px = slot ? DIR_PX : ESQ_PX;
    const u16 py = slot ? DIR_PY : ESQ_PY;
    const u16 pal = slot ? PAL3 : PAL2;
    for (u16 tr = 0; tr < 6; tr++)
        for (u16 tc = 0; tc < 6; tc++)
            VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(pal, FALSE, FALSE, FALSE,
                TILE_USER_INDEX + PORT_BASE + slot * PORT_TILES + tr * 6 + tc),
                px + tc, py + tr);
}

// ---------------------------------------------------------------------------
// Texto (quebra por palavra + máquina de escrever)
// ---------------------------------------------------------------------------

// quebra a fala em até BOX_H linhas de BOX_W colunas (por palavra); o que
// não couber é descartado (fala longa demais = erro de roteiro)
static void wrapText(const char *text)
{
    wrapLines = 0;
    typeTotal = 0;
    u16 i = 0;
    while (text[i] && wrapLines < BOX_H)
    {
        while (text[i] == ' ') i++;             // come espaços do início
        if (!text[i]) break;

        u16 len = 0, lastSpace = 0;
        while (text[i + len] && len < BOX_W)
        {
            if (text[i + len] == ' ') lastSpace = len;
            len++;
        }
        if (text[i + len] && text[i + len] != ' ' && lastSpace)
            len = lastSpace;                    // não corta palavra no meio

        memcpy(wrapBuf[wrapLines], &text[i], len);
        wrapBuf[wrapLines][len] = 0;
        typeTotal += len;
        wrapLines++;
        i += len;
    }
}

// posição da letra n (0..typeTotal-1) dentro das linhas quebradas
static void typedPos(u16 n, u16 *row, u16 *col)
{
    for (u16 r = 0; r < wrapLines; r++)
    {
        const u16 len = strlen(wrapBuf[r]);
        if (n < len) { *row = r; *col = n; return; }
        n -= len;
    }
    *row = 0; *col = 0;
}

static const StoryLine *line(void) { return &cur->lines[lineIdx]; }

// origem da caixa de texto da fala atual
static void boxOrigin(u16 *x, u16 *y)
{
    if (line()->side == LADO_DIR) { *x = DIR_TX; *y = DIR_TY + 2; }
    else                          { *x = ESQ_TX; *y = ESQ_TY + 2; }
}

// desenha a próxima letra da fala (máquina de escrever)
static void typeOne(void)
{
    u16 bx, by, row, col;
    boxOrigin(&bx, &by);
    typedPos(typed, &row, &col);
    char s[2] = { wrapBuf[row][col], 0 };
    VDP_drawText(s, bx + col, by + row);
    typed++;
}

// abre a fala atual: limpa as duas caixas, garante o retrato e escreve o nome
static void startLine(void)
{
    VDP_clearTextArea(ESQ_TX, ESQ_TY, BOX_W + 2, BOX_H + 2);   // caixa de cima
    VDP_clearTextArea(DIR_TX, DIR_TY, BOX_W + 2, BOX_H + 2);   // caixa de baixo

    const StoryLine *l = line();
    loadPortrait(l->side == LADO_DIR ? 1 : 0, l->portrait);

    char buf[16];
    sprintf(buf, "%s:", PORTRAIT_NAME[l->portrait]);
    if (l->side == LADO_DIR) VDP_drawText(buf, DIR_TX, DIR_TY);
    else                     VDP_drawText(buf, ESQ_TX, ESQ_TY);

    wrapText(l->text);
    typed = 0;
    blinkTimer = 0;
    blinkOn = FALSE;
}

// ---------------------------------------------------------------------------
// Fluxo da cena
// ---------------------------------------------------------------------------

bool STORYSCR_start(u8 node, u8 when)
{
    const StoryEntry *e = STORY_find(node, when);
    if (!e) return FALSE;
    if (seen[when] & ((u32) 1 << node)) return FALSE;   // já tocou neste run
    seen[when] |= (u32) 1 << node;

    cur = e;
    lineIdx = 0;
    slotPortrait[0] = slotPortrait[1] = 0xFF;

    MUSIC_setEnemies(0);            // cena: música calma
    SPRITES_hide();
    SYS_doVBlankProcess();          // aplica a lista vazia já neste quadro
    VDP_clearPlane(BG_A, TRUE);
    FLOOR_clear();

    VDP_drawText("A AVANCA", 4, 27);
    VDP_drawText("START PULA", 26, 27);
    startLine();
    return TRUE;
}

// marcador de "fala completa" piscando no canto da caixa ativa
static void blinkMarker(void)
{
    if (blinkTimer) { blinkTimer--; return; }
    blinkTimer = 16;
    blinkOn = !blinkOn;
    u16 bx, by;
    boxOrigin(&bx, &by);
    VDP_drawText(blinkOn ? ">" : " ", bx + BOX_W, by + BOX_H - 1);
}

// fim da cena: devolve a região do chefe ao dono (cache invalida e regenera)
static bool endScene(void)
{
    ENEMYGFX_dropBoss();
    return TRUE;
}

bool STORYSCR_update(u16 pressed)
{
    if (pressed & BUTTON_START) return endScene();      // pula a cena inteira

    if (typed < typeTotal)                              // fala em curso
    {
        if (pressed & BUTTON_A)                         // A: completa a fala
        {
            while (typed < typeTotal) typeOne();
            return FALSE;
        }
        for (u8 i = 0; i < TYPE_SPEED && typed < typeTotal; i++) typeOne();
        if ((typed & 7) == 0) sfxItemPickup();          // blip da "voz"
        return FALSE;
    }

    blinkMarker();                                      // fala completa
    if (pressed & BUTTON_A)                             // A: próxima fala
    {
        lineIdx++;
        if (lineIdx >= cur->count) return endScene();
        startLine();
    }
    return FALSE;
}
