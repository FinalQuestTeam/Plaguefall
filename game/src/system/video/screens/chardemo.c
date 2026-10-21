// Assets: Damião, Dinorah e audição das trilhas originais.
// ESQ/DIR troca de aba; na música CIMA/BAIXO escolhe, A pausa, C muda o clima.

#include "system/video/screens/chardemo.h"
#include "system/video/enemygfx.h"
#include "system/video/sprites/tiles.h"
#include "system/video/actor_animation.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "core/game.h"     // fps
#include "heroi.h"
#include "dinorah.h"

#define CHARACTER_COUNT 2
#define GALLERY_COUNT 3
#define MUSIC_TAB 2
#define MUSIC_LIST_ROW 7
#define PREVIEW_FRAME_TILES 24
#define PREVIEW_VIEW_COUNT 5
#define PREVIEW_POSE_TILES (PREVIEW_VIEW_COUNT * PREVIEW_FRAME_TILES)

#if PREVIEW_POSE_TILES * ACTOR_IDLE_FRAMES > ENEMY_CACHE_TILES
#error Character gallery exceeds the borrowed enemy tile cache
#endif

static const char *const NAMES[GALLERY_COUNT] = { "DAMIAO", "DINORAH", "MUSICAS" };
static const u8 CANON[8] = { 0, 1, 2, 3, 4, 3, 2, 1 };

static void loadPreview(u8 which)
{
    const u32 *frames = (const u32 *)(which ? dinorah_frames : heroi_frames);
    VDP_resetSprites();
    VDP_updateSprites(1, DMA);
    ENEMYGFX_reset();
    // Dinorah's native frames use exactly the same palette as Damião.
    PAL_setColors(PAL2 * 16, (const u16 *)heroi_palette, 16, DMA);
    for (u8 pose = 0; pose < ACTOR_IDLE_FRAMES; pose++)
        for (u8 dir = 0; dir < PREVIEW_VIEW_COUNT; dir++)
            VDP_loadTileData(frames + (dir * ACTOR_VIEW_FRAMES + pose) * 192,
                TILE_USER_INDEX + ENEMY_ROT_BASE + pose * PREVIEW_POSE_TILES + dir * PREVIEW_FRAME_TILES,
                PREVIEW_FRAME_TILES, DMA);
}

// Posicao de referencia de cada personagem 32x48, ao redor do centro
// (160,112) num raio ~70 px — mesma ordem das direções (0=cima, horário)
static const struct { s16 x, y; } COMPASS[8] =
{
    { 144,  26 },   // 0 cima
    { 193,  47 },   // 1 cima-direita
    { 214,  96 },   // 2 direita
    { 193, 145 },   // 3 baixo-direita
    { 144, 166 },   // 4 baixo
    {  95, 145 },   // 5 baixo-esquerda
    {  74,  96 },   // 6 esquerda
    {  95,  47 },   // 7 cima-esquerda
};

static void drawLabels(u8 which)
{
    VDP_clearTextArea(0, 13, 40, 1);        // limpa a linha do nome (centro)
    const char *name = NAMES[which];
    u16 len = 0; while (name[len]) len++;
    VDP_drawText(name, (40 - len) / 2, 13);

    char buf[8];
    sprintf(buf, "%d/%d", which + 1, GALLERY_COUNT);
    VDP_drawText(buf, 19, 15);
}

static void centered(const char *text, u16 row)
{
    VDP_drawText(text, (40 - strlen(text)) / 2, row);
}

static void drawTabs(u8 which)
{
    static const u16 columns[GALLERY_COUNT] = { 1, 14, 28 };
    for (u8 i = 0; i < GALLERY_COUNT; i++)
    {
        char label[12];
        sprintf(label, "%c%s", i == which ? '>' : ' ', NAMES[i]);
        VDP_drawText(label, columns[i], 0);
    }
}

static void drawMusicList(u8 selected)
{
    for (u8 i = 0; i < MUSIC_TRACK_COUNT; i++)
    {
        const u16 row = MUSIC_LIST_ROW + i * 3;
        char label[28];
        sprintf(label, "%d. %s", i + 1, MUSIC_trackName(i));
        VDP_drawText(i == selected ? ">" : " ", 2, row);
        VDP_drawText(label, 4, row);
    }
}

static void drawMusicStatus(bool playing, bool combat)
{
    VDP_clearTextArea(0, 18, 40, 3);
    centered(playing ? (combat ? "TOCANDO - COMBATE" : "TOCANDO - CALMA")
                     : (combat ? "PAUSADO - COMBATE" : "PAUSADO - CALMA"), 18);
    char label[16];
    sprintf(label, "BPM: %d", MUSIC_bpm());
    centered(label, 20);
    VDP_clearTextArea(0, 24, 40, 1);
    centered(playing ? "A: PAUSAR  C: CALMA/COMBATE" : "A: OUVIR   C: CALMA/COMBATE", 24);
}

static void drawPage(u8 which, u8 selected)
{
    VDP_clearPlane(BG_A, TRUE);
    drawTabs(which);
    centered("ESQ/DIR: ABAS  B/START: SAIR", 26);
    if (which < CHARACTER_COUNT)
    {
        loadPreview(which);
        drawLabels(which);
    }
    else
    {
        VDP_resetSprites();
        VDP_updateSprites(1, DMA);
        centered("TRILHA SONORA", 3);
        centered("CIMA/BAIXO: ESCOLHER", 5);
        drawMusicList(selected);
    }
}

void CHARDEMO_run(void)
{
    VDP_setScreenWidth320();
    VDP_setTextPlane(BG_A);
    VDP_setTextPalette(PAL0);
    VDP_clearPlane(BG_A, TRUE);
    PAL_setColor(0, RGB24_TO_VDPCOLOR(0x101018));   // fundo azul bem escuro

    u8 which = 0;
    u8 selected = MUSIC_TRACK_BAIAO;
    bool playing = TRUE, combat = FALSE;
    bool refreshStatus = FALSE;
    u16 lastBpm = 0xFFFF;
    u16 animTick = 0;
    const u16 idleStep = ACTOR_IDLE_TICKS(fps);
    drawPage(which, selected);

    u16 prev = JOY_readJoypad(JOY_1);

    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        const u16 pressed = joy & ~prev;
        prev = joy;

        if (pressed & (BUTTON_B | BUTTON_START)) break;
        if (which < CHARACTER_COUNT && (pressed & BUTTON_A)) break;

        if (pressed & (BUTTON_RIGHT|BUTTON_LEFT))
        {
            if (which == MUSIC_TAB) MUSIC_endPreview();
            which = (which + ((pressed & BUTTON_RIGHT) ? 1 : GALLERY_COUNT - 1)) % GALLERY_COUNT;
            animTick = 0;
            playing = TRUE;
            if (which == MUSIC_TAB)
            {
                MUSIC_previewTrack(selected);
                MUSIC_setEnemies(combat ? MUSIC_ENEMY_MAX : 0);
                refreshStatus = TRUE;
            }
            drawPage(which, selected);
        }
        else if (which == MUSIC_TAB)
        {
            if (pressed & (BUTTON_UP | BUTTON_DOWN))
            {
                selected = (selected + ((pressed & BUTTON_DOWN) ? 1 : MUSIC_TRACK_COUNT - 1)) % MUSIC_TRACK_COUNT;
                MUSIC_previewTrack(selected);
                MUSIC_setEnemies(combat ? MUSIC_ENEMY_MAX : 0);
                playing = TRUE;
                drawMusicList(selected);
                refreshStatus = TRUE;
            }
            if (pressed & BUTTON_A)
            {
                playing = !playing;
                if (!playing) AUDIO_silenceAll();
                refreshStatus = TRUE;
            }
            if (pressed & BUTTON_C)
            {
                combat = !combat;
                MUSIC_setEnemies(combat ? MUSIC_ENEMY_MAX : 0);
                refreshStatus = TRUE;
            }
        }

        AUDIO_frameBegin();
        if (which != MUSIC_TAB || playing) MUSIC_update();
        AUDIO_frameEnd();

        if (which == MUSIC_TAB)
        {
            if (refreshStatus || MUSIC_bpm() != lastBpm)
            {
                drawMusicStatus(playing, combat);
                lastBpm = MUSIC_bpm();
                refreshStatus = FALSE;
            }
            SYS_doVBlankProcess();
            continue;
        }

        // os 8 sprites (uma direção em cada ponto da bússola)
        const u8 pose = animTick / idleStep;
        if (++animTick >= idleStep * ACTOR_IDLE_FRAMES) animTick = 0;
        u16 n = 0;
        for (u8 d = 0; d < 8; d++)
        {
            const u16 tile = TILE_USER_INDEX + ENEMY_ROT_BASE +
                pose * PREVIEW_POSE_TILES + CANON[d] * PREVIEW_FRAME_TILES;
            const u8 flip = d >= 5;
            VDP_setSpriteFull(n, COMPASS[d].x, COMPASS[d].y - 16, SPRITE_SIZE(4, 4),
                TILE_ATTR_FULL(PAL2, TRUE, FALSE, flip, tile), n + 1); n++;
            VDP_setSpriteFull(n, COMPASS[d].x, COMPASS[d].y + 16, SPRITE_SIZE(4, 2),
                TILE_ATTR_FULL(PAL2, TRUE, FALSE, flip, tile + 16), n + 1); n++;
        }
        VDP_setSpriteLink(n - 1, 0);
        VDP_updateSprites(n, DMA_QUEUE);

        SYS_doVBlankProcess();
    }

    MUSIC_endPreview();
    VDP_resetSprites();
    VDP_updateSprites(1, DMA_QUEUE);
    VDP_clearPlane(BG_A, TRUE);
}
