// Tela COMO JOGAR: explica controles, inimigos (cor/forma), a elite (pentágonos)
// e os itens. Paginada — ESQ/DIR troca de página, B/START volta ao menu.
// Usa a fonte (PAL0) para o texto e os tiles já carregados (PAL1) para os ícones
// de cor dos inimigos e a arte 16x16 dos itens.

#include "system/video/screens/help.h"
#include "system/video/sprites/tiles.h"
#include "system/video/enemygfx.h"
#include "system/audio/music.h"
#include "system/audio/audio.h"
#include "core/game.h"
#include "enemies/enemies.h"

#define PAGES   5

// ícone 8x8 de cor de inimigo (TILE_ICON_*) na posição (col,row)
static void drawIcon8(u16 col, u16 row, u16 tile)
{
    VDP_setTileMapXY(BG_A,
        TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_USER_INDEX + tile), col, row);
}

// sprite do inimigo (inseto, de frente) na posição (col,row), do topo p/ baixo
static void drawEnemyIcon(u16 col, u16 row, u8 type)
{
    ENEMYGFX_drawOnMap(type, col, row);
}

// arte 16x16 de item (4 tiles em ordem de coluna) na posição (col,row)
static void drawItem16(u16 col, u16 row, u16 base, u16 icon)
{
    const u16 p = TILE_USER_INDEX + base;
    drawIcon8(35, row, icon); // mesma identidade no tamanho de HUD
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, p + 0), col,     row);
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, p + 1), col,     row + 1);
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, p + 2), col + 1, row);
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, p + 3), col + 1, row + 1);
}

// PÁGINA 1 — controles e objetivo
static void drawControls(void)
{
    VDP_drawText("CONTROLES", 2, 3);
    VDP_drawText("DIRECIONAL", 4, 5);  VDP_drawText("MOVER", 18, 5);
    VDP_drawText("BOTAO A", 4, 6);     VDP_drawText("ATIRAR", 18, 6);
    VDP_drawText("BOTAO C", 4, 7);     VDP_drawText("TROCAR ITEM (INVENTARIO)", 18, 7);
    VDP_drawText("BOTAO B", 4, 8);     VDP_drawText("USAR O ITEM SELECIONADO", 18, 8);
    VDP_drawText("START", 4, 9);       VDP_drawText("PAUSA", 18, 9);

    VDP_drawText("OBJETIVO", 2, 12);
    VDP_drawText("DERROTE A META DE INIMIGOS DE", 4, 14);
    VDP_drawText("CADA FASE. SAO 15 FASES.", 4, 15);
    VDP_drawText("PEGUE ITENS E USE-OS PELO", 4, 16);
    VDP_drawText("INVENTARIO PARA CHEGAR LONGE.", 4, 17);
}

// PÁGINA 2 — a chave dos inimigos (cor = comportamento, forma = resistência)
static void drawEnemies(void)
{
    VDP_drawText("INIMIGOS", 2, 3);

    VDP_drawText("A COR MOSTRA O COMPORTAMENTO", 2, 5);
    drawIcon8(3, 7,  TILE_ICON_RED); VDP_drawText("VERMELHO  ATIRA A DISTANCIA", 5, 7);
    drawIcon8(3, 9,  TILE_ICON_YEL); VDP_drawText("AMARELO   PERSEGUE VOCE", 5, 9);
    drawIcon8(3, 11, TILE_ICON_PUR); VDP_drawText("ROXO      BLINDADO CICLICO", 5, 11);
    drawIcon8(3, 13, TILE_ICON_ORG); VDP_drawText("LARANJA   INVESTIDA RAPIDA", 5, 13);

    VDP_drawText("O INSETO MOSTRA A FAMILIA", 2, 15);
    drawEnemyIcon(3, 17, ENEMY_SQ_RED);  VDP_drawText("SERRA-PAU RESISTENTE", 7, 17);
    drawEnemyIcon(3, 19, ENEMY_TRI_RED); VDP_drawText("MUTUCA    FRAGIL E AGRESSIVA", 7, 19);
    drawEnemyIcon(3, 21, ENEMY_PEN_RED); VDP_drawText("SAUVA     ELITE COM TRUQUE", 7, 21);
}

// PÁGINA 3 — a elite: truques dos pentágonos
static void drawElite(void)
{
    VDP_drawText("INIMIGOS ELITE - SAUVAS", 2, 3);
    VDP_drawText("CADA UMA TEM UM TRUQUE:", 2, 5);

    drawIcon8(3, 7,  TILE_ICON_RED); VDP_drawText("ARTILHEIRO  LEQUE DE TIROS", 5, 7);
    drawIcon8(3, 9,  TILE_ICON_YEL); VDP_drawText("ALCATEIA    DIVIDE-SE EM 2", 5, 9);
    drawIcon8(3, 11, TILE_ICON_PUR); VDP_drawText("FORTALEZA   INVOCA LACAIOS", 5, 11);
    drawIcon8(3, 13, TILE_ICON_ORG); VDP_drawText("METEORO     TELEPORTA E BATE", 5, 13);

    VDP_drawText("DICA: OS ROXOS FICAM INVULNERAVEIS", 2, 16);
    VDP_drawText("EM CICLOS. ESPERE O ESCUDO BAIXAR", 2, 17);
    VDP_drawText("(ELES PISCAM) PARA ACERTA-LOS.", 2, 18);
}

// PÁGINA 4 — itens de efeito imediato (aplicam ao coletar)
static void drawItems(void)
{
    VDP_drawText("ITENS - EFEITO NA HORA QUE PEGA", 2, 3);
    VDP_drawText("ICONE", 33, 5);

    drawItem16(3, 6,  TILE_HEART, TILE_ICON_HEART);  VDP_drawText("MARMITA DO ABRIGO", 6, 6);
    VDP_drawText("CURA 15 DE VIDA", 6, 7);
    drawItem16(3, 10, TILE_BULLET, TILE_ICON_SHOTS); VDP_drawText("DIVISOR DE DISPARO", 6, 10);
    VDP_drawText("+1 BALA (ATE 5)", 6, 11);
    drawItem16(3, 14, TILE_BOOT, TILE_ICON_SPEED);   VDP_drawText("SERVO DE PASSADA", 6, 14);
    VDP_drawText("+20% VELOCIDADE (ATE +100%)", 6, 15);

    VDP_drawText("OS DEMAIS ITENS VAO PARA O", 3, 19);
    VDP_drawText("INVENTARIO (VER PROXIMA PAGINA).", 3, 20);
}

// PÁGINA 5 — inventário: itens ativáveis (B usa, C troca)
static void drawInventoryHelp(void)
{
    VDP_drawText("INVENTARIO - B USA, C TROCA", 2, 3);
    VDP_drawText("ICONE", 33, 4);

    drawItem16(3, 5,  TILE_BOMB, TILE_BOMB_ICON);   VDP_drawText("CARGA DE DESMONTE", 6, 5);
    VDP_drawText("LIMPA A TELA", 6, 6);
    drawItem16(3, 8,  TILE_SHIELD, TILE_ICON_SHIELD); VDP_drawText("CAPACITOR DE PROTECAO", 6, 8);
    VDP_drawText("3 SEGUNDOS INVENCIVEL", 6, 9);
    drawItem16(3, 11, TILE_CHAIN, TILE_BOLT);  VDP_drawText("BOBINA DE SUBESTACAO", 6, 11);
    VDP_drawText("5 TIROS EM CADEIA", 6, 12);
    drawItem16(3, 14, TILE_ICE, TILE_ICON_ICE);    VDP_drawText("REFIL DE ARREFECIMENTO", 6, 14);
    VDP_drawText("CONGELA 5 S - 3 CARGAS", 6, 15);
    drawItem16(3, 17, TILE_FIRE, TILE_ICON_FIRE);   VDP_drawText("REFIL DE MACARICO", 6, 17);
    VDP_drawText("QUEIMA 6 S - 4 CARGAS", 6, 18);

    VDP_drawText("CARGA GASTA A CADA DISPARO.", 3, 21);
}

static void drawPage(u8 page)
{
    VDP_clearPlane(BG_A, TRUE);
    VDP_drawText("COMO JOGAR", 15, 0);

    switch (page)
    {
        case 0: drawControls();      break;
        case 1: drawEnemies();       break;
        case 2: drawElite();         break;
        case 3: drawItems();         break;
        case 4: drawInventoryHelp(); break;
    }

    char buf[16];
    sprintf(buf, "PAGINA %d/%d", page + 1, PAGES);
    VDP_drawText(buf, 15, 24);
    VDP_drawText("ESQ/DIR: MUDAR   A/B: VOLTAR", 6, 26);
}

void HELP_run(void)
{
    VDP_setTextPlane(BG_A);
    VDP_setTextPalette(PAL0);

    // a tela roda no menu (sem fase carregada): gera a arte dos 3 tipos exibidos.
    // 0xFF = fora da campanha (pode descartar qualquer tipo residente)
    static const u8 shown[] = { ENEMY_SQ_RED, ENEMY_TRI_RED, ENEMY_PEN_RED };
    ENEMYGFX_loadForPhase(0xFF, shown, 3);

    u8 page = 0;
    drawPage(page);

    u16 prev = JOY_readJoypad(JOY_1);   // captura o botão ainda pressionado do menu

    while (TRUE)
    {
        const u16 joy = JOY_readJoypad(JOY_1);
        const u16 pressed = joy & ~prev;
        prev = joy;

        AUDIO_frameBegin(); // mantém o loop da música tocando (via árbitro)
        MUSIC_update();
        AUDIO_frameEnd();

        if (pressed & BUTTON_RIGHT) { page = (page + 1) % PAGES;         drawPage(page); }
        if (pressed & BUTTON_LEFT)  { page = (page + PAGES - 1) % PAGES; drawPage(page); }
        if (pressed & (BUTTON_A | BUTTON_B | BUTTON_START)) break;

        SYS_doVBlankProcess();
    }

    VDP_clearPlane(BG_A, TRUE);
}
