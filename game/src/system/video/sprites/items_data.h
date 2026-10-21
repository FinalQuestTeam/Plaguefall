#ifndef ITEMS_DATA_H
#define ITEMS_DATA_H
// Generated from indexed PNGs by art/cangaco-itens-v2/export.py.
// PAL1 unchanged; index 0 transparent. Include after items/items.h.

// Marmita do abrigo
static const char *const ITEM_HEART_ART[16] =
{
    "................",
    "....11..........",
    "...111111.......",
    "..1111111111....",
    "..131111111311..",
    "...133311111111.",
    "..1133a331111111",
    "113aaaaaa3311111",
    "13aaa131aaa33111",
    "1331131311aaa31.",
    "13333111111aa31.",
    "133333311113331.",
    ".13333333333331.",
    "..113333333331..",
    "....113333311...",
    "......11111.....",
};
static const TilePixel ITEM_HEART_LEG[] = { { '1', 1 }, { '3', 3 }, { 'a', 10 } };

// Carga de desmonte
static const char *const ITEM_BOMB_ART[16] =
{
    "................",
    "................",
    "................",
    "................",
    "................",
    "...1111111111...",
    ".11b44444444411.",
    ".1b4444444444b1.",
    "1b444444444444b1",
    "14bbbbb444444b41",
    "14b4bbbb44444b41",
    "14b44bbbb4444b41",
    "14b44bbbbb444b41",
    "14b4444bbbb44b41",
    "14b44444bbbb4b41",
    ".11111111111111.",
};
static const TilePixel ITEM_BOMB_LEG[] = { { '1', 1 }, { '4', 4 }, { 'b', 11 } };

// Divisor de disparo
static const char *const ITEM_SHOTS_ART[16] =
{
    "................",
    "................",
    "................",
    "......1111......",
    ".....131131.....",
    "..11.131131.11..",
    ".13111133111131.",
    ".1111.1331.1111.",
    "1113311331133111",
    "1333311331133331",
    ".13333133133331.",
    "..133313313331..",
    "...1333333331...",
    "....13333331....",
    ".....113311.....",
    "......1111......",
};
static const TilePixel ITEM_SHOTS_LEG[] = { { '1', 1 }, { '3', 3 } };

// Servo de passada
static const char *const ITEM_SPEED_ART[16] =
{
    ".....11111111...",
    "....16eeeee61...",
    "....1e66666661..",
    "....1eeeee1ee1..",
    "....16eee11e61..",
    ".....1eee1ee11..",
    ".....1ee1111e1..",
    ".....1eeee1ee1..",
    "......1ee11e61..",
    ".....16ee1ee1...",
    "....16ee1eee61..",
    "..11eee1eeeee1..",
    ".1eeeeeeeeee61..",
    ".1eeeeee616661..",
    ".16666661.1111..",
    "..111111........",
};
static const TilePixel ITEM_SPEED_LEG[] = { { '1', 1 }, { '6', 6 }, { 'e', 14 } };

// Capacitor de protecao
static const char *const ITEM_SHIELD_ART[16] =
{
    "......111.......",
    "......1f1.......",
    ".11111fff11111..",
    "1fffffffffffff1.",
    "1fffff111fffff1.",
    "1fffff111fffff1.",
    "1fffff111fffff1.",
    ".1f111111111f1..",
    ".1f111111111f1..",
    ".1f111111111f1..",
    ".1ffff111ffff1..",
    ".11fff111fff11..",
    "..1fff111ff11...",
    "...111fff111....",
    ".....1fff1......",
    "......111.......",
};
static const TilePixel ITEM_SHIELD_LEG[] = { { '1', 1 }, { 'f', 15 } };

// Bobina de subestacao
static const char *const ITEM_CHAIN_ART[16] =
{
    "..........11....",
    ".........141....",
    "........1441....",
    ".......1141.....",
    "......14441.....",
    ".....11441......",
    "....144441......",
    "....144441111...",
    "...111444441....",
    "......144411....",
    "......14441.....",
    ".....14441......",
    "....1a44a1......",
    "....1aaaa1......",
    "....1aaaa1......",
    ".....1111.......",
};
static const TilePixel ITEM_CHAIN_LEG[] = { { '1', 1 }, { '4', 4 }, { 'a', 10 } };

// Refil de arrefecimento
static const char *const ITEM_ICE_ART[16] =
{
    "................",
    "................",
    ".....111111.....",
    "...1122222211...",
    "...1222222221...",
    "...12f2ff2f21...",
    ".11f1ffffff1f11.",
    "1f222222222222f1",
    "1ffffffffffffff1",
    "1222222112222221",
    "1222221221222221",
    "1222211111122221",
    "1222212112122221",
    "1222222222222221",
    "1ffffffffffffff1",
    ".11111111111111.",
};
static const TilePixel ITEM_ICE_LEG[] = { { '1', 1 }, { '2', 2 }, { 'f', 15 } };

// Refil de macarico
static const char *const ITEM_FIRE_ART[16] =
{
    "....1111111.....",
    "....1333331.....",
    "....1333331.....",
    "..11333333311...",
    ".1331133311331..",
    ".1ccccccccccc1..",
    ".1ccccc1ccccc1..",
    ".1ccccc11cccc1..",
    ".1cccc111cccc1..",
    ".1ccc1111cccc1..",
    ".1cc11111c1cc1..",
    ".1cc111c111cc1..",
    ".1cc11cc111cc1..",
    ".1cc11ccc11cc1..",
    ".13cc1ccc1cc31..",
    "..11111111111...",
};
static const TilePixel ITEM_FIRE_LEG[] = { { '1', 1 }, { '3', 3 }, { 'c', 12 } };

#endif
