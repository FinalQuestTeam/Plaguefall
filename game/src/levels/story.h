#ifndef STORY_H
#define STORY_H

#include <genesis.h>

// HISTÓRIA (diálogos entre fases): o roteiro é a tabela em levels/story.c —
// edite SÓ lá. A tela que toca as cenas fica em system/video/screens/story.c.
// Sistema: doc/plano-historia.md. Universo e campanha: doc/historia/README.md.

// lado da fala (retrato esquerdo em cima; retrato direito embaixo)
#define LADO_ESQ    0
#define LADO_DIR    1

// momento da cena em relação à fase (nó do grafo)
#define ANTES       0   // ao chegar no nó, antes da tela de preparação
#define DEPOIS      1   // ao vencer o nó, antes do mapa de rotas (ou do fim)

// retratos (a ARTE, na mesma ordem, vive em sprites/portraits_data.h)
#define P_REX       0   // humano com implantes, retrato do concept v3
#define P_COMANDO   1   // padre que coordena a resistencia pelo radio
#define P_LACRAIA   2   // a matriz local do enxame (chefe)
#define P_PARCEIRA  3   // garota do concept v2, retrato de conversa

typedef struct
{
    u8 side;                // LADO_ESQ / LADO_DIR
    u8 portrait;            // P_* (pode trocar a cada fala)
    const char *text;       // a fala (MAIÚSCULA SEM ACENTO; quebra automática)
} StoryLine;

typedef struct
{
    u8 node;                // nó do grafo (N_* de levels/graph.h)
    u8 when;                // ANTES / DEPOIS
    const StoryLine *lines;
    u8 count;
} StoryEntry;

extern const StoryEntry STORY[];
extern const u16 STORY_COUNT;

// cena do nó n no momento when; NULL se o nó não tem cena nesse momento
const StoryEntry *STORY_find(u8 node, u8 when);

#endif // STORY_H
