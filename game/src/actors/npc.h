#ifndef NPC_H
#define NPC_H

#include <genesis.h>

// Aliado (NPC) do objetivo PROTEGER: fica parado num ponto da arena, tem vida e
// sofre dano ao ser encostado por inimigos (que o perseguem). Se a vida zera, a
// fase é perdida. Um único NPC por vez. Desenhado com o tile do coração (PAL1).

#define NPC_DEFAULT_HP  100     // vida do aliado quando o def não especifica
#define NPC_SIZE        24      // lado do aliado (antena 24x24)

extern s16 npcX, npcY;          // canto superior esquerdo (24x24), quando ativo
extern s16 npcHp;               // vida atual (<=0 = caiu)
extern s16 npcHpMax;            // vida máxima da fase (para o HUD)

void NPC_spawn(s16 x, s16 y, u16 hp);   // posiciona e define a vida (0,0 -> centro; hp 0 -> padrão)
void NPC_clear(void);           // desativa (fases sem NPC)
bool NPC_active(void);          // há um aliado na fase?
bool NPC_alive(void);           // ativo e com vida > 0?
bool NPC_hidden(void);          // piscando neste quadro (invencibilidade pós-dano)?
void NPC_update(void);          // dano por contato de inimigos (com i-frames)

#endif // NPC_H
