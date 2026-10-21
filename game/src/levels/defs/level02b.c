// Fase 2B: rota de quem gastou bomba na fase 1 — mesma meta da 2A, mas com
// lama desde cedo (anda devagar, tem que mirar melhor; disciplina de recurso).

#include "levels/levels.h"
#include "levels/stage_scenes.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_YEL, ENEMY_SQ_ORG };

const LevelDef LEVEL02B_def =
{
    .killTarget   = 12,
    .spawnSeconds = 5,
    .mud          = STAGE02B_mud,
    .mudCount     = LAYOUT_RECTS,
    .floor        = FLOOR_FOREST,
    .musicTrack   = MUSIC_TRACK_ENTARDECER,
    .musEnemyMax  = 4,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ARENA02B,
    LVL_ROSTER(roster),
};
