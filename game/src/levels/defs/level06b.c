// Fase 6B: RETIRADA — o aliado caiu na fase 5 (rota OBJ_FALHOU do grafo).
// A fase 6 com o cerco fechado: mesmo enxame, spawn mais apertado.

#include "levels/levels.h"
#include "levels/stage_scenes.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG };

const LevelDef LEVEL06B_def =
{
    .killTarget   = 20,
    .spawnSeconds = 2,
    .lava         = STAGE06B_lava,
    .lavaCount    = LAYOUT_RECTS,
    // retirada: a música já entra tensa (calma só sem NENHUM inimigo)
    .musCalmUntil = 1,
    .musEnemyMax  = 4,
    .musStepCalm  = 8,
    .musStepHot   = 6,
    .musicTrack   = MUSIC_TRACK_BREU,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ARENA06B,
    LVL_ROSTER(roster),
};
