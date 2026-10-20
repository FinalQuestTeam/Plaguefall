#ifndef ENEMYGFX_H
#define ENEMYGFX_H
#include <genesis.h>

// Native 16/24/32px enemies and a 48px boss; at most four frame transfers
// per VBlank, in a bounded 10KiB pool. Eight views reuse three H-flips.
void ENEMYGFX_loadForPhase(u8 phase,const u8 *types,u16 count);
void ENEMYGFX_reset(void);
void ENEMYGFX_dropBoss(void);
void ENEMYGFX_prepare(u16 frame);
bool ENEMYGFX_ready(u16 index);
u16 ENEMYGFX_entityTile(u16 index);
u8 ENEMYGFX_entityFlipH(u16 index);
// Legacy menu/target API: tile base points at a small static icon.
u16 ENEMYGFX_dirTile(u8 type,u8 dir,u8 frame);
u8 ENEMYGFX_dirFlipH(u8 type,u8 dir);
u8 ENEMYGFX_dirFlipV(u8 type,u8 dir);
void ENEMYGFX_drawOnMap(u8 type,u16 col,u16 row);
u8 ENEMYGFX_faceDir(s16 dx,s16 dy);
#endif
