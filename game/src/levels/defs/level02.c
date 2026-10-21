// Fase 2A (rota sem bomba na fase 1): vazia — entra o laranja (investida).

#include "levels/levels.h"
#include "levels/stage_scenes.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_YEL, ENEMY_SQ_ORG };

const LevelDef LEVEL02_def =
{
    .killTarget   = 12,
    .spawnSeconds = 5,
    .musicTrack   = MUSIC_TRACK_LADAINHA,
    .musEnemyMax  = 4,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ARENA02A,
    LVL_ROSTER(roster),
};
