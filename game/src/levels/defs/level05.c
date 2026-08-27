// Fase 5: vazia — triângulos atirador/caçador, PROTEGENDO o aliado.
// Bifurca no grafo: protegeu → 6A; o aliado caiu (OBJ_FALHOU) → 6B (retirada).

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_TRI_RED, ENEMY_TRI_YEL, ENEMY_SQ_ORG };

const LevelDef LEVEL05_def =
{
    .objective    = OBJ_PROTECT,    // aliado no centro (npcX/Y 0 = centro)
    .objTarget    = 30,             // segurar por 30 s
    .spawnSeconds = 4,
    LVL_ROSTER(roster),
};
