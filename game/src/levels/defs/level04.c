// Fase 4: travessia dos tuneis. Ondas duplas mantem pressao no percurso.

#include "levels/levels.h"
#include "levels/route_stages.h"

static const u8 roster[] = { ENEMY_SQ_RED, ENEMY_SQ_PUR, ENEMY_TRI_YEL };

const LevelDef LEVEL04_def =
{
    .objective    = OBJ_REACH,
    .modularTerrain = TRUE,
    .route        = &ROUTE04,
    .spawnSeconds = 2,
    .spawnCount   = 2,
    .mud          = ROUTE04_hazards,
    .mudCount     = sizeof(ROUTE04_hazards) / sizeof(ROUTE04_hazards[0]),
    .floor        = FLOOR_FOREST,
    .musicTrack   = MUSIC_TRACK_BREU,
    .musEnemyMax  = 4,
    .enemyCap     = 4,
    .shotCap      = 6,
    .arena        = &ROUTE_ARENA04,
    LVL_ROSTER(roster),
};
