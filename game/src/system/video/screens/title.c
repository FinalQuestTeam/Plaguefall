// Tela inicial: título + menu (Novo Jogo / Fase Teste / Como Jogar), modo normal
// do VDP. A música já toca aqui. A opção Como Jogar abre a tela de explicação e
// volta ao menu; só Novo Jogo e Fase Teste são devolvidas ao main.
//
// O fundo é a arte de img/bg.jpg em char-map (system/video/titlebg.c), no BG_B;
// o menu fica no BG_A por cima. As telas de ajuda/personagens escondem a arte
// (texto sobre fundo limpo) e ela volta ao retornar ao menu.

#include "system/video/screens/title.h"
#include "system/video/screens/help.h"
#include "system/video/screens/chardemo.h"
#include "system/video/titlebg.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "core/game.h"     // fps

// ordem do menu (Fase Teste por último); cada posição mapeia p/ uma ação TITLE_*
#define MENU_N      4
#define ROW_0       13
#define ROW_1       15
#define ROW_2       17
#define ROW_3       19

static const u16 menuRows[MENU_N]    = { ROW_0, ROW_1, ROW_2, ROW_3 };
static const char *const menuText[MENU_N] =
    { "NOVO JOGO", "COMO JOGAR", "PERSONAGENS", "FASE TESTE" };
static const u8 menuAction[MENU_N]   =
    { TITLE_NEW_GAME, TITLE_HELP, TITLE_CHARS, TITLE_TEST };

static void drawMenu(void)
{
    VDP_setTextPlane(BG_A);
    VDP_setTextPalette(PAL0);
    VDP_clearPlane(BG_A, TRUE);

    VDP_drawText("R E D R E X", 15, 6);
    VDP_drawText("ARENA SHOOTER", 14, 9);
    for (u16 i = 0; i < MENU_N; i++)
        VDP_drawText(menuText[i], 16, menuRows[i]);
}

u8 TITLE_run(void)
{
    AUDIO_silenceAll();         // cala o PSG antes da carga do fundo (sem nota presa
    VDP_setScreenWidth320();    // ao voltar da fase/pausa); a música retoma no loop
    TITLEBG_load();             // arte do fundo na VRAM (PAL1/PAL2) ...
    TITLEBG_draw();             // ... e no BG_B, atrás do menu
    drawMenu();

    u8 sel = 0;                 // posição no menu
    u16 prev = JOY_readJoypad(JOY_1);
    u16 lock = fps * 3 / 10;    // ignora input por ~0,3 s (evita seleção acidental)

    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        const u16 pressed = joy & ~prev;
        prev = joy;             // atualizado sempre: botão segurado não dispara

        AUDIO_frameBegin();     // engata o loop ao fim da intro (via árbitro)
        MUSIC_update();
        AUDIO_frameEnd();

        if (lock)
        {
            lock--;
        }
        else
        {
            if (pressed & BUTTON_UP)   sel = (sel + MENU_N - 1) % MENU_N;
            if (pressed & BUTTON_DOWN) sel = (sel + 1) % MENU_N;
            if (pressed & (BUTTON_START | BUTTON_A))
            {
                const u8 act = menuAction[sel];
                if (act != TITLE_HELP && act != TITLE_CHARS)
                    break;                          // Novo Jogo / Fase Teste

                TITLEBG_clear();                    // texto dessas telas sem a arte atrás
                TITLEBG_release();                  // elas usam a VRAM/paletas do jogo
                if (act == TITLE_HELP) HELP_run();  // Como Jogar: explica e volta
                else                   CHARDEMO_run(); // Personagens: vitrine e volta
                TITLEBG_load();                     // repinta a arte por cima de novo
                TITLEBG_draw();
                drawMenu();
                prev = JOY_readJoypad(JOY_1);        // re-sincroniza (evita eco)
                lock = fps / 2;                      // trava curta ao retornar
            }
        }

        // cursor ">" na opção selecionada
        for (u16 i = 0; i < MENU_N; i++)
            VDP_drawText(sel == i ? ">" : " ", 14, menuRows[i]);

        SYS_doVBlankProcess();
    }

    VDP_clearPlane(BG_A, TRUE);
    TITLEBG_clear();
    TITLEBG_release();          // devolve VRAM e paletas ao jogo
    return menuAction[sel];     // devolve a AÇÃO (Novo Jogo / Fase Teste)
}
