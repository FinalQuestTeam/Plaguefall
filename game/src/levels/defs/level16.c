// Fase 16 — CHEFE (Escorpiao). Só o chefe (que invoca seus próprios lacaios).
// O chefe é gerado no início da fase (core/flow.c) e derrotá-lo encerra o jogo
// (tela de fim → título). Sem spawn regular; TRI_YEL entra no roster só para a
// arte dos lacaios ficar carregada na VRAM.

#include "levels/levels.h"

static const u8 roster[] = { ENEMY_BOSS, ENEMY_TRI_YEL };

const LevelDef LEVEL16_def =
{
    .killTarget   = 1,      // só para o HUD/preparação (a vitória é o chefe)
    .spawnSeconds = 99,     // sem spawn regular (o laço pula na fase final)
    .floor        = FLOOR_CAVE,     // covil do chefe: rocha úmida
    // música: tensão alta o tempo todo — já começa acelerada e chega ao pico
    // com poucos lacaios (o combate contra o chefe é intenso do início ao fim)
    .musCalmUntil = 1,
    .musEnemyMax  = 6,
    .musStepCalm  = 7,
    .musStepHot   = 5,
    .musicTrack   = MUSIC_TRACK_BREU,
    LVL_ROSTER(roster),
};
