#ifndef TILES_H
#define TILES_H

// Mapa dos tiles procedurais na VRAM (a partir de TILE_USER_INDEX). É o "índice
// de assets" do jogo: cada bloco é gerado por system/video/tilegen.c e referenciado
// pelos módulos que desenham (sprites, HUD, elementos, itens, inimigos).
// Mantido separado de core/game.h por ser um concern de vídeo/gráficos.

// Os sprites dos inimigos (insetos) e do jogador (mech) NÃO ficam aqui: são
// gerados por direção nas regiões ENEMY_ROT / BOSS_ROT / CHARS (abaixo). Estes
// tiles base são só os elementos fixos (projéteis, cenário, itens, HUD, overlays).

// projéteis e cenário (8x8, 1 tile cada)
#define TILE_PSHOT      0   // tiro do jogador
#define TILE_ESHOT      1   // tiro inimigo
#define TILE_WALL       2   // parede (borda da arena)
#define TILE_LAVA       3   // lava
#define TILE_MUD        4   // lama

// itens (16x16 = 4 tiles em ordem de coluna)
#define TILE_HEART      5   // vida
#define TILE_BOMB       9   // carga de bomba
#define TILE_BULLET     13  // disparos (bala)
#define TILE_BOOT       17  // velocidade (botinha)
#define TILE_SHIELD     21  // invencibilidade (escudo)
#define TILE_CHAIN      25  // raio (reação em cadeia)
#define TILE_ICE        29  // gelo
#define TILE_FIRE       33  // fogo

// sombra do jogador (16x16)
#define TILE_SHADOW     37  // 4 tiles

// ícones 8x8 (1 tile cada): HUD, telas e cores dos inimigos
#define TILE_SKULL      41  // caveira do contador de mortes
#define TILE_BOMB_ICON  42  // bomba (HUD/inventário)
#define TILE_BOLT       43  // raio ativo (HUD/inventário)
#define TILE_SPARK      44  // nó do raio em cadeia
#define TILE_DOOR       45  // porta entre as fases teste
#define TILE_ICON_RED   46  // cor vermelha (tela "Como Jogar")
#define TILE_ICON_YEL   47  // cor amarela
#define TILE_ICON_PUR   48  // cor roxa
#define TILE_ICON_ORG   49  // cor laranja
#define TILE_ICON_SHIELD 50 // escudo (inventário)
#define TILE_ICON_ICE   51  // gelo (inventário)
#define TILE_ICON_FIRE  52  // fogo (inventário)
#define TILE_BLOOD      53  // quarto de poça de sangue (espelhado = poça 16x16)

// overlay de status (bloco 4x4 xadrez, índice 2) sobre o inimigo:
// gelo (ciano, PAL1) / fogo (vermelho, PAL0)
#define TILE_STATUS     54  // 16 tiles

// ícones 8x8 do HUD de objetivo (contador da linha 0)
#define TILE_ICON_HEART 70  // coração (COLETAR corações)
#define TILE_CLOCK      71  // relógio (tempo restante: SOBREVIVER / PROTEGER)
// objetivo PROTEGER: santa24x24 + ícone e brilho8x8 (mesmos endereços)
#define TILE_SAINT      72  // 9 tiles24x24 — Nossa Senhora Aparecida
#define TILE_ICON_SAINT 81  // 1 tile8x8 — indicador no HUD
#define TILE_SAINT_GLOW 82  // 1 tile8x8 — brilho da coroa, overlay existente
#define NUM_TILES       83

// Streamed enemy animation cache followed by independent menu icons.
#define ENEMY_ROT_BASE  NUM_TILES
#define ENEMY_MAX_FRAME_TILES 36 // largest frame: boss 48x48
#define ENEMY_DMA_FRAMES 4
#define ENEMY_CACHE_TILES 320 // bounded pool, 10KiB, allocated in 4-tile blocks
#define ENEMY_ICON_TILES 16
#define ENEMY_ICON_BASE (ENEMY_ROT_BASE + ENEMY_CACHE_TILES)
#define ENEMY_ROT_COUNT (ENEMY_CACHE_TILES + 15 * ENEMY_ICON_TILES)

#define BOSS_ROT_BASE   (ENEMY_ROT_BASE + ENEMY_ROT_COUNT)
#define BOSS_ROT_COUNT  72 // scratch only: two 48x48 story portraits
#define BOSS_DIR_TILES  36  // (48/8)² tiles por direção

#endif // TILES_H
