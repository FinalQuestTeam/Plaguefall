// Fase 6B: RETIRADA — o aliado caiu na fase 5 (rota OBJ_FALHOU do grafo).
// Dinorah atravessa a retirada por terra; Damiao cobre o percurso.

#include "levels/levels.h"
#include "levels/route_stages.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_TRI_ORG };

const LevelDef LEVEL06B_def =
{
    .objective    = OBJ_ESCORT,
    .modularTerrain = TRUE,
    .route        = &ROUTE06B,
    .spawnSeconds = 2,
    .lava         = ROUTE06B_hazards,
    .lavaCount    = 8,
    // retirada: a música já entra tensa (calma só sem NENHUM inimigo)
    .musCalmUntil = 1,
    .musEnemyMax  = 4,
    .musStepCalm  = 8,
    .musStepHot   = 6,
    .musicTrack   = MUSIC_TRACK_BREU,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ROUTE_ARENA06B,
    LVL_ROSTER(roster),
};
