#ifndef ICONS_DATA_H
#define ICONS_DATA_H

// Char-maps 8x8 dos ícones de HUD/telas (pintados por tilegen.c com buildTile8;
// as legendas char -> cor da PAL1 ficam lá, junto da geração). Legenda '.' = vazio.
// A arte 16x16 dos itens está em items_data.h; personagens/insetos nos demais _data.h.

// caveira do contador de mortes (HUD)
static const char *const ICON_SKULL_ART[8] =
{
    "........",
    "..####..",
    ".######.",
    ".#.##.#.",
    ".######.",
    "..####..",
    "..#.#.#.",
    "........",
};

// bomba (inventário, posição 0): corpo, brilho e faísca

// raio (item raio ativo / ícone no inventário) — amarelo

// nó do raio em cadeia (losango amarelo com miolo branco)
static const char *const ICON_SPARK_ART[8] =
{
    "........",
    "...#....",
    "..###...",
    ".##o##..",
    "..###...",
    "...#....",
    "........",
    "........",
};

// escudo (inventário)

// gelo (inventário): cristal ciano

// fogo (inventário): chama com miolo claro

// coração pequeno 8x8 (HUD: COLETAR corações / vida do aliado no PROTEGER)

// relógio 8x8 (HUD: tempo restante em SOBREVIVER / PROTEGER)
static const char *const ICON_CLOCK_ART[8] =
{
    "..####..",
    ".#....#.",
    "#..#...#",
    "#..#...#",
    "#..###.#",
    "#.....#.",
    ".#....#.",
    "..####..",
};

#endif // ICONS_DATA_H
