// Training menus borrow/restore the same reversible panel as pause.
#include "levels/test.h"
#include "levels/operations.h"
#include "levels/levels.h"
#include "levels/graph.h"
#include "system/video/screens/mission.h"
#include "system/video/screens/panel.h"
#include "system/audio/audio.h"
#include "system/audio/music.h"
#include "system/audio/sfx.h"
#include "actors/player.h"
#include "actors/bomb.h"
#include "core/game.h"
bool testCampaignMode;
static const char *const names[TEST_ROOMS]={"GALERIA DE INIMIGOS","BANCADA DE ITENS","DEFESA DA SANTA","COLISÕES E PERIGOS","COMPORTAMENTO E CHEFE","CARGA E PERFORMANCE","DESLOCAMENTO","PROTEGER DINORAH","ANIMAÇÕES DE MORTE","REGRAS DE MORTE","DEMOLIÇÃO DOS NINHOS","RELIGAR A SUBESTAÇÃO","RECUPERAR CARREGAMENTO","CAÇAR TRANSMISSORES","SANGRAR A PRESSÃO","CORREDOR DE EVACUAÇÃO","ATRAIR O ENXAME","SEGURAR E ABANDONAR"};
static const char *const goals[TEST_ROOMS]={
    "13 INIMIGOS: ANIMAÇÕES E MORTES.","DUMMY, OITO ITENS E ALVOS EM CADEIA.",
    "PROTEJA A SANTA POR 30 SEGUNDOS.","TESTE MUROS, TIROS, LAVA E LAMA.",
    "ESCOLHA AMEAÇAS COM COMPORTAMENTO REAL.","8 BLINDADOS AGRUPADOS, TIROS REPOSTOS.",
    "ATRAVESSE ATÉ A SAÍDA SINALIZADA.","LEVE DINORAH VIVA ATÉ A SAÍDA.","VEJA AS MORTES DE DAMIÃO E DINORAH.",
    "TESTE AS PERDAS E RECUPERE O BORNAL.",
    "ARME 3 CARGAS SEM ATIRAR E SAIA.","LIGUE 2 GERADORES E O PAINEL CENTRAL.",
    "ENTREGUE 2 CAIXAS; A 3A DÁ BÔNUS.","DESTRUA OS 3 INSETOS MARCADOS.",
    "ABRA 3 VÁLVULAS E EVITE O CALOR.","QUEBRE 3 GRADES E LIBERE OS GRUPOS.",
    "ELIMINE 6 INSETOS COM A ARMADILHA.","DEFENDA O RÁDIO POR 25 S E RETIRE-SE."};
const char *TEST_name(u8 room){return names[(room>=1 && room<=TEST_ROOMS) ? room-1 : 0];}
void TEST_goal(char *text){strcpy(text,goals[testStage-1]);}
static void menuFrame(void)
{
    AUDIO_frameBegin();MUSIC_update();SFX_update();AUDIO_frameEnd();SYS_doVBlankProcess();
}
static void roomPage(u8 selected,bool endings,bool full)
{
    const u8 count=endings ? TEST_ENDING_COUNT : NODE_COUNT;
    const u8 first=!endings && selected>=9 ? selected-8 : 0;
    if(full) {
        char right[16];sprintf(right,endings ? "%u FINAIS" : "%u FASES",count);
        PANEL_page(endings ? "FINAIS DA CAMPANHA" : "FASES DA CAMPANHA",right);
        PANEL_text(endings ? "     IGREJA  POVO    DINORAH" : "CIMA/BAIXO: ESCOLHER FASE",2,3,PANEL_ACCENT);
        PANEL_text(endings ? "A: ASSISTIR   B/START: VOLTAR" : "A: ENTRAR  C: PÁGINA  B: VOLTAR",2,26,PANEL_LIGHT);
    }
    PANEL_selection(5+(selected-first)*2);
    for(u16 row=0;row<9;row++) {
        const u8 i=first+row;
        VDP_clearText(2,5+row*2,36);
        if(i>=count)continue;
        char text[48];
        if(endings)sprintf(text,"%c %u. %s  %s  %s",i==selected ? '>' : ' ',i+1,
            (i&1) ? "RUÍNAS" : "DE PÉ ",(i&2) ? "PERDAS" : "SALVO ",(i&4) ? "MORTA" : "VIVA");
        else sprintf(text,"%c %s. %s",i==selected ? '>' : ' ',GRAPH[i+1].name,MISSION_name(i+1));
        PANEL_text(text,2,5+row*2,i==selected ? PANEL_LIGHT : PANEL_BODY);
    }
    // The tab legend on row24 is static. Clearing/repainting it for every
    // selection can expose a blank scan in PAL; only the goal row changes.
    VDP_clearTextArea(2,23,36,1);
    if(endings)PANEL_text("CIMA/BAIXO: ESCOLHER  START: PULAR",2,23,PANEL_BODY);
    else {char goal[64];MISSION_goal(goal,selected+1);PANEL_wrap(goal,2,23,36,1,PANEL_BODY);}
    if(full)PANEL_text("ESQ/DIR: FASES / FINAIS",2,24,PANEL_ACCENT);
}
u8 TEST_chooseRoom(u8 initial)
{
    AUDIO_silenceAll();if(!PANEL_begin())return 0;
    bool endings=initial>=TEST_ENDING_FIRST && initial<TEST_ENDING_FIRST+TEST_ENDING_COUNT;
    u8 phase=(initial>TEST_ROOMS && initial<=TEST_ROOMS+NODE_COUNT) ? initial-TEST_ROOMS-1 : 0;
    u8 ending=endings ? initial-TEST_ENDING_FIRST : 0;
    u8 selected=endings ? ending : phase;
    roomPage(selected,endings,TRUE);u16 previous=JOY_readJoypad(JOY_1);
    while(TRUE) {
        menuFrame();const u16 joy=JOY_readJoypad(JOY_1),pressed=joy&~previous;previous=joy;
        if(pressed&(BUTTON_B|BUTTON_START)){PANEL_end();return 0;}
        if(pressed&BUTTON_A){PANEL_end();return endings ? TEST_ENDING_FIRST+selected : TEST_ROOMS+selected+1;}
        if(pressed&(BUTTON_LEFT|BUTTON_RIGHT)) {
            if(endings)ending=selected;else phase=selected;
            endings=!endings;selected=endings ? ending : phase;
            roomPage(selected,endings,TRUE);continue;
        }
        const u8 count=endings ? TEST_ENDING_COUNT : NODE_COUNT;
        if(pressed&BUTTON_UP)selected=(selected+count-1)%count;
        else if(pressed&BUTTON_DOWN)selected=(selected+1)%count;
        else if((pressed&BUTTON_C) && !endings)selected=selected+9<count ? selected+9 : 0;
        else continue;
        roomPage(selected,endings,FALSE);
    }
}
void TEST_pauseSelection(u8 selected)
{
    char text[32];
    static const char *const entries[]={"CONTINUAR","CONFIGURAR TESTE","REINICIAR SALA","TROCAR SALA","COMO JOGAR","VOLTAR AO TÍTULO"};
    PANEL_selection(13+selected*2);
    for(u16 i=0;i<6;i++) {
        sprintf(text,"%c %s",i==selected ? '>' : ' ',entries[i]);
        PANEL_text(text,2,13+i*2,i==selected ? PANEL_LIGHT : PANEL_BODY);
    }
}
void TEST_pauseDraw(u8 selected)
{
    char right[16],text[64];sprintf(right,"SALA %u/%u",testStage,TEST_ROOMS);
    PANEL_page("PAUSADO",right);PANEL_text(TEST_name(testStage),2,5,PANEL_ACCENT);
    TEST_goal(text);PANEL_wrap(text,2,7,36,1,PANEL_BODY);
    sprintf(text,"VIDA: %03u/100       BOMBAS: %u",hp<0 ? 0 : hp,BOMB_count());PANEL_text(text,2,10,PANEL_BODY);
    TEST_pauseSelection(selected);
    PANEL_text("A: OK    B/START: CONTINUAR",2,26,PANEL_LIGHT);
}
static u8 *field(TestSettings *s,u8 row,u8 *limit)
{
    *limit=2;
    if(testStage>=OPS_FIRST_ROOM){
        if(!row){*limit=3;return &s->attacks;}
        if(row==1){*limit=5;return &s->dummyHp;}
        if(row==2){*limit=6;return &s->status;}return &s->noDefeat;
    }
    switch(testStage) {
        case TEST_RULE_ROOM:
            switch(row){case 0:*limit=3;return &s->kind;case 1:*limit=5;return &s->dummyHp;
                case 2:*limit=6;return &s->status;case 3:*limit=4;return &s->count;
                default:*limit=4;return &s->shots;}
        case TEST_DEATH_ROOM:
            switch(row){case 0:*limit=3;return &s->selected;case 1:return &s->direction;
                case 2:*limit=3;return &s->slow;case 3:return &s->repeat;default:*limit=0;return NULL;}
        case 1:
            switch(row){case 0:return &s->animation;case 1:*limit=9;return &s->direction;
                case 2:*limit=3;return &s->slow;case 3:*limit=13;return &s->selected;case 4:return &s->repeat;default:*limit=0;return NULL;}
        case 2:
            switch(row){case 0:*limit=3;return &s->dummyHp;case 1:return &s->chain;case 2:return &s->restock;default:*limit=3;return &s->initialHp;}
        case 3:case 7:case 8:if(!row){*limit=3;return &s->attacks;}return &s->noDefeat;
        case 4:*limit=3;return &s->initialHp;
        case 5:if(!row){*limit=14;return &s->kind;}if(row==1){*limit=4;return &s->count;}return &s->noDefeat;
        default:
            switch(row){case 0:*limit=4;return &s->count;case 1:*limit=4;return &s->kind;
                case 2:*limit=3;return &s->shots;case 3:*limit=4;return &s->status;
                case 4:return &s->deaths;default:return &s->noDefeat;}
    }
}
static const char *label(u8 row)
{
    static const char *const rules[]={"ETAPAS DA CAMPANHA","TIRO INICIAL","VELOC. INICIAL","ITENS INICIAIS","BOMBAS INICIAIS"};
    static const char *const actors[]={"PERSONAGEM","LADO DA QUEDA","TEMPO","REPETIR MORTE","MOSTRAR MORTE"};
    static const char *const gallery[]={"ANIMAÇÃO","DIREÇÃO","TEMPO","INIMIGO","REPETIR MORTE","MOSTRAR MORTE"};
    static const char *const items[]={"VIDA DO DUMMY","ALVOS CADEIA","REPOR ITENS","VIDA INICIAL"};
    static const char *const defense[]={"ATAQUES","SEM DERROTA"};
    static const char *const behavior[]={"TIPO","QUANTIDADE","SEM DERROTA"};
    static const char *const load[]={"QUANTIDADE","TIPO","TIROS / GRUPO","STATUS","MORTES EM LOOP","SEM DERROTA"};
    if(testStage>=OPS_FIRST_ROOM){static const char *const ops[]={"REFORÇOS","TIRO INICIAL","VELOC. INICIAL","SEM DERROTA"};return ops[row];}
    switch(testStage){case TEST_RULE_ROOM:return rules[row];case TEST_DEATH_ROOM:return actors[row];case 1:return gallery[row];case 2:return items[row];case 3:case 7:case 8:return row ? "DAMIÃO SEM DERROTA" : defense[row];case 4:return "VIDA INICIAL";case 5:return behavior[row];default:return load[row];}
}
static void value(char *text,u8 row)
{
    const TestSettings *s=&testSettings[testStage-1];
    static const char *const directions[]={"N","NE","L","SE","S","SO","O","NO","GIRAR 8 DIREÇÕES"};
    if(testStage==TEST_RULE_ROOM) {
        static const char *const ranges[]={"1 A 5","6 A 11","12 A 16"};
        switch(row){case 0:strcpy(text,ranges[s->kind]);return;
            case 1:sprintf(text,"%u PROJÉTEIS",s->dummyHp+1);return;
            case 2:sprintf(text,"+%u%% (NÍVEL %u)",s->status*PLAYER_SPEED_STEP,s->status);return;
            case 3:sprintf(text,"%u / 3",s->count);return;
            default:sprintf(text,"%u / 3",s->shots);return;}
    }
    if(testStage>=OPS_FIRST_ROOM && (row==1 || row==2)){
        if(row==1)sprintf(text,"%u PROJÉTEIS",s->dummyHp+1);
        else sprintf(text,"+%u%%",s->status*PLAYER_SPEED_STEP);return;
    }
    if(testStage==TEST_DEATH_ROOM) {
        switch(row){case 0:strcpy(text,s->selected==2 ? "OS DOIS" : s->selected ? "DINORAH" : "DAMIÃO");return;
            case 1:strcpy(text,s->direction ? "ESQUERDA" : "DIREITA");return;
            case 2:sprintf(text,"1/%u X",1u<<s->slow);return;
            case 3:strcpy(text,s->repeat ? "SIM" : "NÃO");return;
            default:strcpy(text,"A: REPRODUZIR");return;}
    }
    if(testStage==1) {
        switch(row){case 0:strcpy(text,s->animation ? "CAMINHADA" : "REPOUSO");return;
            case 1:strcpy(text,directions[s->direction]);return;case 2:sprintf(text,"1/%u X",1u<<s->slow);return;
            case 3:strcpy(text,ENEMY_DEFS[s->selected==12 ? ENEMY_BOSS : s->selected]->name);return;
            case 4:strcpy(text,s->repeat ? "SIM" : "NÃO");return;default:strcpy(text,"A: REPRODUZIR");return;}
    }
    if(testStage==2 && (row==0 || row==3)){static const u8 hp[]={1,20,100},life[]={25,50,100};sprintf(text,"%u",row==0 ? hp[s->dummyHp] : life[s->initialHp]);return;}
    if((TEST_objectiveRoom() || testStage>=OPS_FIRST_ROOM) && !row){static const char *const attacks[]={"PAUSADOS","CAMPANHA","PRESSÃO CONTÍNUA"};strcpy(text,attacks[s->attacks]);return;}
    if(testStage==4){static const u8 life[]={25,50,100};sprintf(text,"%u",life[s->initialHp]);return;}
    if(testStage==6 && row==1){static const char *const kinds[]={"BALUARTE+FORTALEZA","BALUARTE","FORTALEZA","ESCUDEIRO"};strcpy(text,kinds[s->kind]);return;}
    if((testStage==5 && !row)){strcpy(text,s->kind ? ENEMY_DEFS[s->kind==13 ? ENEMY_BOSS : s->kind-1]->name : "MISTO");return;}
    if((testStage==5 && row==1) || (testStage==6 && !row)) {
        static const u8 count[]={1,4,8,16};if(testStage==5 && s->kind==13)strcpy(text,"1 + LACAIOS");else sprintf(text,"%u",count[s->count]);return;
    }
    if(testStage==6 && row==2){static const u8 shots[]={0,6,16};sprintf(text,"%u",shots[s->shots]);return;}
    if(testStage==6 && row==3){static const char *const statuses[]={"NATURAL","ESCUDO","GELO","FOGO"};strcpy(text,statuses[s->status]);return;}
    u8 limit;u8 *v=field(&testSettings[testStage-1],row,&limit);strcpy(text,v && *v ? "SIM" : "NÃO");
}
static void configPage(u8 selected,u8 count,bool full)
{
    char right[16],text[48];
    if(full) {
        sprintf(right,"SALA %u",testStage);
        PANEL_page("CONFIGURAR TESTE",right);PANEL_text(TEST_name(testStage),2,4,PANEL_ACCENT);
    }
    PANEL_selection(6+selected*2);
    for(u16 i=0;i<count;i++) {
        const u16 pal=i==selected ? PANEL_LIGHT : PANEL_BODY;
        PANEL_text(label(i),2,6+i*2,pal);value(text,i);
        VDP_clearTextArea(21,6+i*2,17,1);PANEL_text(text,21,6+i*2,pal);
    }
    if(!full)return;
    if(testStage==2) {
        PANEL_text("1 MARMITA       2 BOMBA",2,16,PANEL_BODY);
        PANEL_text("3 DIVISOR       4 SERVO",2,17,PANEL_BODY);
        PANEL_text("5 ESCUDO        6 RAIO",2,18,PANEL_BODY);
        PANEL_text("7 GELO          8 FOGO",2,19,PANEL_BODY);
    }
    if(testStage>=OPS_FIRST_ROOM) {
        PANEL_wrap(goals[testStage-1],2,15,36,2,PANEL_BODY);
        PANEL_text("PONTOS: PARE SEM ATIRAR PARA USAR",2,18,PANEL_BODY);

    }
    if(testStage==TEST_RULE_ROOM) {
        PANEL_text("A: MORRER / START: REPETIR DERROTA",2,17,PANEL_BODY);
        PANEL_text("B: REPOR EQUIPAMENTO E ZERAR MORTES",2,18,PANEL_BODY);
        PANEL_text("C: TROCAR ETAPAS E REPOR",2,19,PANEL_BODY);
    }
    if(testStage==6) {
        PANEL_text("PADRÃO: 8 BLINDADOS + 16/16 TIROS",2,18,PANEL_BODY);
        PANEL_text("SEM MORTES: GRUPO MANTIDO VIVO",2,19,PANEL_BODY);
    }
    PANEL_text("CIMA/BAIXO: ESCOLHER",2,21,PANEL_BODY);
    PANEL_text("ESQUERDA/DIREITA: AJUSTAR",2,23,PANEL_BODY);
    PANEL_text("A: APLICAR E REINICIAR  B: VOLTAR",2,26,PANEL_LIGHT);
}
bool TEST_configure(void)
{
    AUDIO_silenceAll();if(!PANEL_begin())return FALSE;
    static const u8 rows[TEST_ROOMS]={6,4,2,1,3,6,2,2,5,5,4,4,4,4,4,4,4,4};const u8 count=rows[testStage-1];u8 selected=0;
    const TestSettings backup=testSettings[testStage-1];
    configPage(selected,count,TRUE);u16 previous=JOY_readJoypad(JOY_1);
    while(TRUE) {
        menuFrame();const u16 joy=JOY_readJoypad(JOY_1),pressed=joy&~previous;previous=joy;
        if(pressed&(BUTTON_B|BUTTON_START)){testSettings[testStage-1]=backup;PANEL_end();return FALSE;}
        if(pressed&BUTTON_A) {
            PANEL_end();
            if((testStage==1 && selected==5) || (testStage==TEST_DEATH_ROOM && selected==4)){TEST_requestDeath();return FALSE;}
            return TRUE;
        }
        if(pressed&BUTTON_UP){selected=(selected+count-1)%count;configPage(selected,count,FALSE);}
        else if(pressed&BUTTON_DOWN){selected=(selected+1)%count;configPage(selected,count,FALSE);}
        else if(pressed&(BUTTON_LEFT|BUTTON_RIGHT)) {
            u8 limit;u8 *v=field(&testSettings[testStage-1],selected,&limit);
            if(v && limit)*v=(*v+((pressed&BUTTON_RIGHT)?1:limit-1))%limit;
            configPage(selected,count,FALSE);
        }
    }
}
