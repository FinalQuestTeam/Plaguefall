#ifndef SFX_H
#define SFX_H

#include <genesis.h>

// efeitos sonoros PSG (canal 1 = tiro do jogador, canal 2 = coleta de item /
// dano sofrido, canal 0 = ambiente, ruído = tiro inimigo / explosão da bomba)
void SFX_playerShot(void);
void SFX_enemyShot(void);
void sfxItemPickup(void);   // blip ascendente ao coletar item (usado por items.c)
void SFX_playerHit(void);   // tom grave descendente: dano de INIMIGO no jogador
void SFX_bombBlast(void);
void SFX_radioTick(void);
void SFX_countPulse(bool go);
void SFX_silence(void);
void SFX_update(void);      // decaimento por frame; chamar sempre no loop

// som ambiente do canal 0 (lava crepitando, passos na lama). Definir a cada
// quadro: sem chamada, permanece o último; use SFX_AMB_NONE para silenciar.
#define SFX_AMB_NONE    0
#define SFX_AMB_LAVA    1
#define SFX_AMB_MUD     2
void SFX_ambient(u8 kind);

#endif // SFX_H
