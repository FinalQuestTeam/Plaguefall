#ifndef STORY_SCREEN_H
#define STORY_SCREEN_H

#include <genesis.h>
#include "levels/story.h"       // ANTES/DEPOIS (momentos da cena)

// Tela de HISTÓRIA (diálogos entre fases) — toca as cenas do roteiro em
// levels/story.c: dois retratos 48x48 fixos e janelas de rádio, texto em
// máquina de escrever. A avança/completa a fala; START pula a cena inteira.
// Cada cena toca UMA vez por run (bitmask interna).

void STORYSCR_reset(void);              // novo jogo: zera as cenas já vistas

// se o nó tem cena inédita no momento dado (ANTES/DEPOIS), desenha a tela,
// marca como vista e devolve TRUE (entre no estado ST_STORY); senão FALSE
bool STORYSCR_start(u8 node, u8 when);

// por quadro no ST_STORY; devolve TRUE quando a cena terminou (ou foi pulada)
bool STORYSCR_update(u16 pressed);
// Release only after the flow has faded the completed scene out.
void STORYSCR_close(void);
// Preserve the outgoing console until the mission content is committed.
bool STORYSCR_closeToMission(void);

#endif // STORY_SCREEN_H
