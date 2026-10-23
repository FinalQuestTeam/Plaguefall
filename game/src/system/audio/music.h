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
#define MUSIC_ENEMY_MAX  15     // inimigos que levam ao BPM máximo do perfil
#define MUSIC_CALM_UNTIL  4     // até este nº de inimigos, fica no BPM calmo
// Compile com MUSIC_MELANCHOLIC=1 (Entardecer) ou MUSIC_DARK=1 (Breu).
#if defined(MUSIC_DARK) && defined(MUSIC_MELANCHOLIC)
#error Select only one music variant
#endif
#ifdef MUSIC_DARK
#define MUSIC_STEP_CALM  12     // Breu: 75 BPM
#define MUSIC_STEP_HOT    8     // Breu: aproximadamente 113 BPM
#elif defined(MUSIC_MELANCHOLIC)
#define MUSIC_STEP_CALM  10     // Entardecer: 90 BPM
#define MUSIC_STEP_HOT    7     // Entardecer: aproximadamente 129 BPM
#else
#define MUSIC_STEP_CALM   9     // frames NTSC equivalentes/passo (100 BPM)
#define MUSIC_STEP_HOT    6     // frames NTSC equivalentes/passo (150 BPM)
#endif
// O relógio de 300 Hz mantém o mesmo andamento em sistemas de 50 e 60 Hz.
// ===========================================================================

#define MUSIC_TRACK_BAIAO       0
#define MUSIC_TRACK_ENTARDECER  1
#define MUSIC_TRACK_BREU        2
#define MUSIC_TRACK_LADAINHA    3
#define MUSIC_TRACK_COUNT       4
#ifdef MUSIC_DARK
#define MUSIC_DEFAULT_TRACK MUSIC_TRACK_BREU
#elif defined(MUSIC_MELANCHOLIC)
#define MUSIC_DEFAULT_TRACK MUSIC_TRACK_ENTARDECER
#else
#define MUSIC_DEFAULT_TRACK MUSIC_TRACK_BAIAO
#endif

// Audição na galeria: a primeira chamada salva a reprodução e a curva atuais.
// Trocar faixa reinicia a prévia; encerrar restaura exatamente o estado salvo.
// IDs inválidos são ignorados. Não muda a trilha escolhida para o jogo.
void MUSIC_previewTrack(u8 track);
void MUSIC_endPreview(void);
u8 MUSIC_track(void);
void MUSIC_selectTrack(u8 track); // permanent campaign selection; independent of gallery preview
const char *MUSIC_trackName(u8 track);

void MUSIC_init(void);          // silencia o PSG e reinicia o sequenciador
void MUSIC_start(void);         // compat (no-op; a música já toca após MUSIC_init)
void MUSIC_update(void);        // acompanha VBlank real; chamar ANTES do SFX
void MUSIC_syncClock(void);     // retoma após outro dono do PSG (abertura/prévia)
// Result cards replace the loop with a single approved cue (victory: 2s;
// game over: 4s), then hold silence until the result card is closed.
void MUSIC_playVictory(void);
void MUSIC_playGameOver(void);
void MUSIC_stopResultCue(void);
void MUSIC_stopVictory(void);
bool MUSIC_victoryActive(void);
bool MUSIC_gameOverActive(void);
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
