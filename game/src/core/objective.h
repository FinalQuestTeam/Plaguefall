#ifndef OBJECTIVE_H
#define OBJECTIVE_H

#include <genesis.h>
#include "levels/levels.h"

// Sistema de objetivos de fase (orientado a dados por LevelDef.objective):
//   OBJ_KILL     — matar killTarget inimigos (padrão histórico)
//   OBJ_SURVIVE  — sobreviver objTarget segundos
//   OBJ_COLLECT  — coletar objTarget itens
//   OBJ_PROTECT  — manter o aliado (NPC) vivo por objTarget segundos
// A lógica por quadro (timer, NPC, contagem) e o HUD/preparação ficam aqui; o
// fluxo (ST_DONE/ST_OVER) continua em core/flow.c.

// retorno de OBJECTIVE_update
#define OBJ_ONGOING     0
#define OBJ_WON         1
#define OBJ_LOST        2

u16 OBJECTIVE_progress(void);
void OBJECTIVE_drawMarkers(u16 *n);
void OBJECTIVE_start(const LevelDef *def);      // início da fase: zera timers/NPC
u8   OBJECTIVE_update(u16 kills);               // por quadro: avança e avalia
void OBJECTIVE_addCollected(u8 itemType);       // hook: item coletado (só o alvo conta)
void OBJECTIVE_drawHUD(u16 kills);              // readout do objetivo (linha 0), com gate
void OBJECTIVE_forceHUD(u16 kills);             // idem, SEM o gate (redesenho garantido)
void OBJECTIVE_prepText(char *buf, const LevelDef *def);  // 1 linha p/ a preparação

u16 OBJECTIVE_secondsLeft(void);
u16 OBJECTIVE_collected(void);

#endif // OBJECTIVE_H
