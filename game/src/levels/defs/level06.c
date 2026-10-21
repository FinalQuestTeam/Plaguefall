// Fase 6A (protegeu o aliado na 5): lava — enxame de triângulos.

#include "levels/levels.h"
#include "levels/stage_scenes.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG };

const LevelDef LEVEL06_def =
{
    .killTarget   = 20,
    .spawnSeconds = 3,
    .lava         = STAGE06A_lava,
    .lavaCount    = LAYOUT_RECTS,
    .musicTrack   = MUSIC_TRACK_ENTARDECER,
    .musEnemyMax  = 4,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ARENA06A,
    LVL_ROSTER(roster),
};
