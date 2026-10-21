// Fase 3: lava — entra o roxo (escudo).

#include "levels/levels.h"
#include "levels/stage_scenes.h"

static const u8 roster[] = { ENEMY_SQ_YEL, ENEMY_SQ_PUR, ENEMY_SQ_ORG };

const LevelDef LEVEL03_def =
{
    .killTarget   = 14,
    .spawnSeconds = 4,
    .lava         = STAGE03_lava,
    .lavaCount    = LAYOUT_RECTS,
    .musicTrack   = MUSIC_TRACK_ENTARDECER,
    .musEnemyMax  = 4,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ARENA03,
    LVL_ROSTER(roster),
};
