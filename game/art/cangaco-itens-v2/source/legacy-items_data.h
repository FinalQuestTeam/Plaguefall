#ifndef ITEMS_DATA_H
#define ITEMS_DATA_H

// Char-maps 16x16 dos itens + legendas de cor (pintados por ITEMS_paintTile16 em
// cada items/item_*.c). Legenda '.' = vazio; demais chars mapeiam para cor da
// PAL1. Depende de TilePixel (definido em items/items.h) — inclua após items.h.

// ---- VIDA (coração vermelho) ----
static const char *const ITEM_HEART_ART[16] =
{
    "................",
    "..###......###..",
    ".#####....#####.",
    "#oo####..#######",
    "#o##############",
    "################",
    "################",
    ".##############.",
    "..############..",
    "...##########...",
    "....########....",
    ".....######.....",
    "......####......",
    ".......##.......",
    "................",
    "................",

};
static const TilePixel ITEM_HEART_LEG[] = { { '#', 3 }, { 'o', 1 } };

// ---- BOMBA (corpo escuro, pavio e faísca) ----
static const char *const ITEM_BOMB_ART[16] =
{
    "...........ss...",
    "..........ff....",
    ".........ff.....",
    "........ff......",
    "....OOOOOOOO....",
    "...O########O...",
    "..O##########O..",
    ".O##O#########O.",
    "O##OOO#########O",
    "O###O##########O",
    "O##############O",
    "O##############O",
    ".O############O.",
    "..O##########O..",
    "...O########O...",
    "....OOOOOOOO....",
};
static const TilePixel ITEM_BOMB_LEG[] =
{
    { '#', 11 },    // corpo escuro
    { 'O', 1 },     // brilho
    { 'f', 1 },     // pavio
    { 's', 5 },     // faísca (laranja)
};

// ---- DISPAROS (bala/latão) ----
static const char *const ITEM_SHOTS_ART[16] =
{
    "................",
    "......####......",
    ".....######.....",
    "....#o####o#....",
    "...#o######o#...",
    "..#o########o#..",
    "..#|########|#..",
    "..#|########|#..",
    "..#|########|#..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..############..",
    "..oooooooooooo..",
    "...##########...",
};
static const TilePixel ITEM_SHOTS_LEG[] =
{
    { '#', 4 },     // corpo (amarelo/latão)
    { 'o', 1 },     // ponta clara
    { '|', 1 },     // brilho
};

// ---- VELOCIDADE (botinha verde) ----
static const char *const ITEM_SPEED_ART[16] =
{
    "................",
    "..######........",
    "..#gggg#........",
    "..#g##g#........",
    "..#gggg#........",
    "..#gggg#........",
    "..#gggg#........",
    "..#gggg##.......",
    "..#gggggg#......",
    "..#ggg##gg#.....",
    "..#gggggggg#....",
    "..#ggggg##gg#...",
    "..#gggggggggg#..",
    "..############..",
    "..oooooooooooo..",
    "..oooooooooooo..",
};
static const TilePixel ITEM_SPEED_LEG[] =
{
    { 'g', 14 },    // corpo (verde)
    { '#', 1 },     // contorno
    { 'o', 1 },     // sola
};

// ---- ESCUDO (escudo azul com cruz) ----
static const char *const ITEM_SHIELD_ART[16] =
{
    "..############..",
    ".#bbbbbbbbbbbb#.",
    ".#bbbbb##bbbbb#.",
    ".#bbbbb##bbbbb#.",
    ".#bbbbb##bbbbb#.",
    ".#bb########bb#.",
    ".#bb########bb#.",
    ".#bbbbb##bbbbb#.",
    ".#bbbbb##bbbbb#.",
    ".#bbbbb##bbbbb#.",
    "..#bbbbbbbbbb#..",
    "...#bbbbbbbb#...",
    "....#bbbbbb#....",
    ".....#bbbb#.....",
    "......#bb#......",
    ".......##.......",
};
static const TilePixel ITEM_SHIELD_LEG[] =
{
    { 'b', 15 },    // corpo (azul)
    { '#', 1 },     // contorno e cruz (branco)
};

// ---- RAIO (relâmpago amarelo, item de cadeia) ----
static const char *const ITEM_CHAIN_ART[16] =
{
    "................",
    "................",
    "......####......",
    ".....####.......",
    "....####........",
    "...####.........",
    "..############..",
    ".........####...",
    "........####....",
    ".......####.....",
    "......####......",
    ".....####.......",
    "................",
    "................",
    "................",
    "................",
};
static const TilePixel ITEM_CHAIN_LEG[] = { { '#', 4 } };   // amarelo (raio)

// ---- GELO (cristal ciano) ----
static const char *const ITEM_ICE_ART[16] =
{
    "................",
    "................",
    ".......ii.......",
    "......icci......",
    ".....icccci.....",
    "....icwcccci....",
    "...icwwccccci...",
    "..icccccccccci..",
    "..icccccccccci..",
    "...icccccccci...",
    "....icccccci....",
    ".....icccci.....",
    "......icci......",
    ".......ii.......",
    "................",
    "................",
};
static const TilePixel ITEM_ICE_LEG[] = { { 'i',15 }, { 'c',2 }, { 'w',1 } };

// ---- FOGO (chama) ----
static const char *const ITEM_FIRE_ART[16] =
{
    "................",
    ".......rr.......",
    ".......rr.......",
    "......rffr......",
    ".....rfyyfr.....",
    "....rfyyyyfr....",
    "...rfyywwyyfr...",
    "..rfyywwwwyyfr..",
    "..rfyywwwwyyfr..",
    ".rfyywwwwwwyyfr.",
    ".rfyywwwwwwyyfr.",
    ".rfyywwwwwwyyfr.",
    "..rfyywwwwyyfr..",
    "..rfyywwwwyyfr..",
    "...rfyywwyyfr...",
    ".....rfyyfr.....",
};
static const TilePixel ITEM_FIRE_LEG[] = { { 'r',3 }, { 'f',12 }, { 'y',4 }, { 'w',1 } };

#endif // ITEMS_DATA_H
