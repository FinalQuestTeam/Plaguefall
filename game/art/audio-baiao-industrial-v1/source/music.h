#ifndef MUSIC_H
#define MUSIC_H

#include <genesis.h>

// Motor de música PSG com ANDAMENTO DINÂMICO (pronto para o jogo).
// A faixa (song_data.h) toca em loop; o BPM sobe conforme a "ameaça" (nº de
// inimigos), dando sensação de perigo. O tempo escala de forma UNIFORME — as
// notas/harmonia não mudam; a ameaça também adensa pulsos e acentos metálicos.
// A faixa original Baiao de Ferrugem mistura síncopes de baião e textura industrial.
// Transições de BPM são SUAVIZADAS (glide), sem saltos bruscos.
//
// NÃO escreve no PSG direto: a cada quadro REQUISITA voz ao árbitro (audio.c),
// que resolve música×SFX por prioridade. Uso: AUDIO_frameBegin(); MUSIC_update();
// (SFX_update();) AUDIO_frameEnd() a cada quadro; MUSIC_init() no boot;
// MUSIC_setEnemies(ENEMIES_activeCount()) quando a contagem mudar; e
// MUSIC_setRamp(...) no início da fase p/ a curva de BPM daquela fase.

// ===========================================================================
// CONFIG — curva de BPM × ameaça (ajuste aqui). BPM = 900 / frames-por-passo.
// A música interpola do "calmo" ao "quente" conforme os inimigos, com glide.
// ===========================================================================
#define MUSIC_ENEMY_MAX  15     // inimigos que levam ao BPM máximo (150)
#define MUSIC_CALM_UNTIL  4     // até este nº de inimigos, fica no BPM calmo (100)
#define MUSIC_STEP_CALM   9     // frames NTSC equivalentes/passo (100 BPM)
#define MUSIC_STEP_HOT    6     // frames NTSC equivalentes/passo (150 BPM)
// O relógio de 300 Hz mantém o mesmo andamento em sistemas de 50 e 60 Hz.
// ===========================================================================

void MUSIC_init(void);          // silencia o PSG e reinicia o sequenciador
void MUSIC_start(void);         // compat (no-op; a música já toca após MUSIC_init)
void MUSIC_update(void);        // avança a música (chamar 1x por quadro, ANTES do SFX)
void MUSIC_setEnemies(u8 count);// 0 = calmo ... enemyMax = perigo (BPM máx)

// curva de BPM da FASE atual (0 em qualquer campo = usa o padrão do CONFIG acima).
// Chamar no início da fase; permite ajustar o comportamento por fase.
//   calmUntil = inimigos até ficar calmo   enemyMax = inimigos p/ BPM máximo
//   stepCalm  = frames/passo calmo         stepHot  = frames/passo no perigo
void MUSIC_setRamp(u8 calmUntil, u8 enemyMax, u8 stepCalm, u8 stepHot);

u16  MUSIC_bpm(void);           // BPM atual (para HUD/debug)
u8   MUSIC_chord(void);         // acorde do compasso atual: 0..3 (HUD)
u16  MUSIC_stepInBar(void);     // passo dentro do compasso 2/4: 0..7 (HUD)

#endif // MUSIC_H
