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
static const char *const ICON_BOMB_ART[8] =
{
    "....o...",
    "....#...",
    ".######.",
    "#BBBBBB#",
    "#B#BBBB#",
    "#BBBBBB#",
    "#BBBBBB#",
    ".######.",
};

// raio (item raio ativo / ícone no inventário) — amarelo
static const char *const ICON_BOLT_ART[8] =
{
    "....###.",
    "...###..",
    "..###...",
    ".#####..",
    "...###..",
    "..###...",
    ".###....",
    "###.....",
};

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
static const char *const ICON_SHIELD_ART[8] =
{
    ".######.",
    ".#bbbb#.",
    ".#bbbb#.",
    ".#bbbb#.",
    "..#bb#..",
    "...##...",
    "........",
    "........",
};

// gelo (inventário): cristal ciano
static const char *const ICON_ICE_ART[8] =
{
    "...c....",
    "..ccc...",
    ".ccccc..",
    "ccccccc.",
    ".ccccc..",
    "..ccc...",
    "...c....",
    "........",
};

// fogo (inventário): chama com miolo claro
static const char *const ICON_FIRE_ART[8] =
{
    "...r....",
    "...rr...",
    "..rfr...",
    ".rffyr..",
    ".rfyyfr.",
    ".rfyyfr.",
    "..rffr..",
    "...rr...",
};

// coração pequeno 8x8 (HUD: COLETAR corações / vida do aliado no PROTEGER)
static const char *const ICON_HEART_ART[8] =
{
    ".##..##.",
    "########",
    "########",
    "########",
    ".######.",
    "..####..",
    "...##...",
    "........",
};

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
