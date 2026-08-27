#ifndef ENEMYGFX_H
#define ENEMYGFX_H

#include <genesis.h>

// Sprites dos inimigos (insetos) em 8 direções, geradas na VRAM POR FASE (não no
// boot): só os tipos que aparecem na fase atual ocupam a região ENEMY_ROT (ver
// sprites/tiles.h). Isso deixa o start instantâneo e economiza VRAM. Cada inimigo
// encara o jogador ao se mover, como o mech do jogador.

// garante na VRAM a arte dos `count` tipos em `types` para o nó `phase` do
// grafo da campanha. Cada tipo é gerado no máximo 1× e reaproveitado; slots são
// organizados em pools por tamanho e um tipo "morto" (fora do alcance do nó —
// GRAPH_reachableTypes) pode ceder seu slot. Idempotente: rechamar com o mesmo
// roster não regenera nada. Use phase=0xFF para "fora da campanha" (fase teste,
// tela de ajuda): todos os tipos de campanha ficam elegíveis a descarte.
void ENEMYGFX_loadForPhase(u8 phase, const u8 *types, u16 count);

// invalida o cache: a região ENEMY_ROT foi usada por outra coisa (a arte de fundo
// do título) e todo tipo residente precisa ser gerado de novo na próxima fase
void ENEMYGFX_reset(void);

// invalida SÓ o chefe: a tela de história usa a região BOSS_ROT como rascunho
// dos retratos; a arte do chefe regenera quando ele voltar a ser preciso
void ENEMYGFX_dropBoss(void);

// tile base da direção `dir` (0=cima, horário até 7) e `frame` de animação do
// tipo. Só 3 direções são geradas (N/NE/E); as outras 5 reaproveitam espelhadas,
// então combine com ENEMYGFX_dirFlipH/V. Comuns têm ANIM_FRAMES quadros; o chefe
// não anima (passe frame=0). (O chefe tem as 8 direções geradas.)
u16 ENEMYGFX_dirTile(u8 type, u8 dir, u8 frame);

// bits de espelhamento (0/1) da direção — passe a TILE_ATTR_FULL(flipH/flipV)
u8 ENEMYGFX_dirFlipH(u8 type, u8 dir);
u8 ENEMYGFX_dirFlipV(u8 type, u8 dir);

// desenha o inimigo (de frente) no tilemap BG_A com o canto superior em (col,row);
// ocupa size/8 tiles de lado. Usado pelas telas (preparação/pausa/ajuda) — exige
// a arte do tipo já residente (ENEMYGFX_loadForPhase).
void ENEMYGFX_drawOnMap(u8 type, u16 col, u16 row);

// converte um vetor (ex.: do inimigo até o jogador) na direção 0..7 mais próxima
u8 ENEMYGFX_faceDir(s16 dx, s16 dy);

#endif // ENEMYGFX_H
