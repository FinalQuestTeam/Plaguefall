// Fábrica de assets: geração procedural dos tiles (4bpp) e da paleta dos objetos.
// Roda uma vez no boot (TILEGEN_init). O buffer é alocado só durante a geração e
// liberado — não ocupa RAM permanente. O mapa de índices está em tiles.h.

#include "system/video/tilegen.h"
#include "system/video/sprites/tiles.h"
#include "system/video/sprites/icons_data.h"
#include "system/video/sprites/saint_data.h"
#include "core/game.h"
#include "elements/lava.h"
#include "elements/mud.h"
#include "items/items.h"
#include "insects.h"

#define TILEBUF_BYTES   (NUM_TILES * 8 * (u16) sizeof(u32))
static u32 *tileBuf;

// pixel em um bloco NxN em ordem de coluna (layout de sprite MD);
// colTiles = altura do sprite em tiles (2 para 16x16, 4 para 32x32)
static void setPix(u16 baseTile, u16 x, u16 y, u16 color, u16 colTiles)
{
    u16 tile = baseTile + (x / 8) * colTiles + (y / 8);
    tileBuf[tile * 8 + (y % 8)] |= (u32) color << ((7 - (x % 8)) * 4);
}

// desenha um tile 8x8 a partir de um mapa de caracteres (chave -> cor)
static void buildTile8(u16 tile, const char *const rows[8], char key, u16 color)
{
    for (u16 y = 0; y < 8; y++)
        for (u16 x = 0; x < 8; x++)
            if (rows[y][x] == key)
                tileBuf[tile * 8 + y] |= (u32) color << ((7 - x) * 4);
}

static void buildTiles(void)
{
    tileBuf = MEM_alloc(TILEBUF_BYTES);
    memset(tileBuf, 0, TILEBUF_BYTES);

    // o jogador (Rex) e os inimigos (insetos) são gerados por direção em
    // chars.c / enemygfx.c (regiões CHARS / ENEMY_ROT), não aqui.

    // projéteis 8x8 (tile único)
    for (u16 y = 0; y < 8; y++)
    {
        for (u16 x = 0; x < 8; x++)
        {
            s16 dx = (s16) (2 * x) - 7;
            s16 dy = (s16) (2 * y) - 7;
            if (dx * dx + dy * dy <= 49)
            {
                tileBuf[TILE_PSHOT * 8 + y] |= (u32) 4 << ((7 - x) * 4);
                tileBuf[TILE_ESHOT * 8 + y] |= (u32) 5 << ((7 - x) * 4);
            }
        }
    }

    // parede: bloco sólido com linha de brilho
    for (u16 y = 0; y < 8; y++)
    {
        for (u16 x = 0; x < 8; x++)
        {
            u16 c = ((x == 0) || (y == 0)) ? 7 : 6;
            tileBuf[TILE_WALL * 8 + y] |= (u32) c << ((7 - x) * 4);
        }
    }

    // ícones 8x8 de HUD/telas — a arte (char-maps) fica em sprites/icons_data.h;
    // aqui só a legenda char -> cor da PAL1 de cada um
    buildTile8(TILE_SKULL, ICON_SKULL_ART, '#', 1);         // caveira (contador)

    buildTile8(TILE_BOMB_ICON, ICON_BOMB_ART, 'B', 11);     // bomba: corpo
    buildTile8(TILE_BOMB_ICON, ICON_BOMB_ART, '#', 1);      //   contorno/brilho
    buildTile8(TILE_BOMB_ICON, ICON_BOMB_ART, 'o', 5);      //   faísca

    buildTile8(TILE_BOLT, ICON_BOLT_ART, '#', 4);           // raio — amarelo

    // ícones do HUD de objetivo (o coração fica branco quando desenhado com PAL0)
    buildTile8(TILE_ICON_HEART, ICON_HEART_ART, '#', 3);    // coração (índice 3)
    buildTile8(TILE_CLOCK, ICON_CLOCK_ART, '#', 1);         // relógio claro
    // Santa24x24, indicador e brilho: mesmos11 tiles da antiga antena.
    // Arte indexada exportada; nenhuma paleta, alocação ou peça extra.
    memcpy(tileBuf + TILE_SAINT * 8, SAINT24_DATA, sizeof SAINT24_DATA);
    memcpy(tileBuf + TILE_ICON_SAINT * 8, SAINT_ICON_DATA, sizeof SAINT_ICON_DATA);
    memcpy(tileBuf + TILE_SAINT_GLOW * 8, SAINT_HALO_DATA, sizeof SAINT_HALO_DATA);

    // porta 8x8 (área de passagem entre as fases teste): painel verde com
    // borda clara — ladrilhado num retângulo, forma um portão/portal
    for (u16 y = 0; y < 8; y++)
    {
        for (u16 x = 0; x < 8; x++)
        {
            bool edge = (x == 0) || (x == 7) || (y == 0) || (y == 7);
            tileBuf[TILE_DOOR * 8 + y] |= (u32) (edge ? 1 : 14) << ((7 - x) * 4);
        }
    }

    // nó do raio em cadeia (losango amarelo com miolo branco)
    buildTile8(TILE_SPARK, ICON_SPARK_ART, '#', 4);         // amarelo
    buildTile8(TILE_SPARK, ICON_SPARK_ART, 'o', 1);         // miolo branco

    // sombra do jogador: círculo pequeno escuro 16x16 (cor 11) sob o mech —
    // destaca do chão sem cobrir a arena. Desenhado atrás dos sprites (spritelist.c).
    for (u16 y = 0; y < 16; y++)
    {
        for (u16 x = 0; x < 16; x++)
        {
            const s16 dx = (s16) (2 * x - 15);
            const s16 dy = (s16) (2 * y - 15);
            if (dx * dx + dy * dy <= 15 * 15) setPix(TILE_SHADOW, x, y, 11, 2);
        }
    }

    // ícones 8x8 dos inimigos (quadrado colorido com borda clara) para as
    // telas de fase/pausa — cores idênticas às dos sprites (PAL1: 3/4/8)
    static const struct { u16 tile; u16 color; } enemyIcon[4] =
    {
        { TILE_ICON_RED, 3 },
        { TILE_ICON_YEL, 4 },
        { TILE_ICON_PUR, 8 },
        { TILE_ICON_ORG, 12 },
    };
    for (u16 k = 0; k < 4; k++)
    {
        for (u16 y = 0; y < 8; y++)
        {
            for (u16 x = 0; x < 8; x++)
            {
                bool edge = (x == 0) || (x == 7) || (y == 0) || (y == 7);
                u16 c = edge ? 1 : enemyIcon[k].color;
                tileBuf[enemyIcon[k].tile * 8 + y] |= (u32) c << ((7 - x) * 4);
            }
        }
    }

    // overlay de status: 16 tiles idênticos (bloco 4x4) em xadrez no índice 2,
    // desenhado por cima do inimigo (spritelist.c). A paleta define a cor:
    // PAL1 → ciano (gelo/congelado), PAL0 → vermelho (fogo/queimando).
    for (u16 t = 0; t < 16; t++)
        for (u16 yy = 0; yy < 8; yy++)
            for (u16 xx = 0; xx < 8; xx++)
                if (((xx + yy) & 1) == 0)
                    tileBuf[(TILE_STATUS + t) * 8 + yy] |= (u32) 2 << ((7 - xx) * 4);

    // ícones do inventário no HUD (escudo, gelo, fogo). Bomba e raio já têm
    // ícone (TILE_BOMB_ICON / TILE_BOLT).
    buildTile8(TILE_ICON_SHIELD, ICON_SHIELD_ART, 'b', 15);
    buildTile8(TILE_ICON_SHIELD, ICON_SHIELD_ART, '#', 1);

    buildTile8(TILE_ICON_ICE, ICON_ICE_ART, 'c', 2);

    buildTile8(TILE_ICON_FIRE, ICON_FIRE_ART, 'r', 3);
    buildTile8(TILE_ICON_FIRE, ICON_FIRE_ART, 'f', 12);
    buildTile8(TILE_ICON_FIRE, ICON_FIRE_ART, 'y', 4);

    // poça de sangue (verde): quarto de disco denso no canto (0,0); a poça 16x16
    // é montada por 4 cópias espelhadas deste tile (blood.c) → mancha arredondada.
    for (u16 y = 0; y < 8; y++)
        for (u16 x = 0; x < 8; x++)
        {
            const u16 d2 = x * x + y * y;
            u16 c = 0;
            if (d2 <= 40)                       c = 14;                    // verde (corpo)
            else if (d2 <= 60 && ((x + y) & 1)) c = (((x * 3 + y) & 3)) ? 14 : 11;  // borda salpicada
            if (c) tileBuf[TILE_BLOOD * 8 + y] |= (u32) c << ((7 - x) * 4);
        }

    // tiles dos elementos de fase e dos itens
    LAVA_buildTile(tileBuf);
    MUD_buildTile(tileBuf);
    ITEMS_buildTiles(tileBuf);

    VDP_loadTileData(tileBuf, TILE_USER_INDEX, NUM_TILES, DMA);

    MEM_free(tileBuf);      // buffer só serve na geração; libera a RAM
    tileBuf = NULL;
}

// paleta dos objetos (PAL1); pública porque a arte do título toma a PAL1 emprestada
void TILEGEN_palette(void)
{
    // PAL0 é o texto (letras no índice 15). Os índices 1..14 ficam livres, então
    // são pintados de BRANCO: viram a "paleta de flash" — um inimigo que toma dano
    // é desenhado com PAL0 e aparece todo branco por alguns quadros, sem gastar
    // nenhum tile de VRAM (a VRAM está no limite por causa da arte do título).
    for (u16 i = 1; i <= 15; i++) PAL_setColor(i, RGB24_TO_VDPCOLOR(0xF0F0F0));

    // exceção: PAL0 índice 2 = VERMELHO. Os tiles do overlay (TILE_STATUS, xadrez
    // no índice 2) desenhados com PAL0 saem vermelhos → overlay de "queimando",
    // igual ao ciano do gelo mas em vermelho. Os pequenos implantes ciano dos
    // inimigos também ficam vermelhos durante o flash de dano.
    PAL_setColor(2, RGB24_TO_VDPCOLOR(0xE02020));

    // Shared object/enemy PAL1 keeps semantic item/status indices.
    PAL_setColors(PAL1 * 16, (const u16 *) insect_palette, 16, DMA);
}

void TILEGEN_init(void)
{
    TILEGEN_palette();
    buildTiles();
}
