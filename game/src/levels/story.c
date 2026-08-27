// ROTEIRO DO JOGO — este é o ÚNICO arquivo a editar para escrever a história.
//
// COMO ESCREVER UMA CENA:
//
//   CENA(abertura)
//       ESQUERDA(P_REX,    "ONDE ESTOU? ESTE SETOR ESTA INFESTADO.")
//       DIREITA(P_COMANDO, "REX, ELES TOMARAM A BASE! LIMPE A AREA.")
//   FIM
//
//   - ESQUERDA(retrato, "fala")  → retrato no canto superior esquerdo fala
//   - DIREITA(retrato, "fala")   → retrato no canto inferior direito fala
//   - A ordem das linhas é a ordem da conversa: intercale como quiser.
//   - O retrato é escolhido POR FALA: o mesmo personagem pode trocar de
//     expressão no meio da cena, ou um terceiro pode entrar no mesmo canto.
//   - Escreva a fala corrida, em MAIUSCULA SEM ACENTO ("VOCE", "ENTAO");
//     a quebra de linha na caixa é automática. Limite: ~100 letras por fala
//     (4 linhas de 26) — passou disso, corta.
//   - Retratos disponíveis (P_*): levels/story.h; a arte 48x48 fica em
//     system/video/sprites/portraits_data.h (char-map editável em texto).
//
// ONDE A CENA TOCA: registre na tabela STORY no fim do arquivo —
//   QUANDO(N_5, ANTES, nome)  → ao chegar na fase 5, antes da preparação
//   QUANDO(N_5, DEPOIS, nome) → ao vencer a fase 5, antes do mapa de rotas
// Um nó pode ter cena de ANTES, de DEPOIS, as duas ou nenhuma. Cada cena
// toca UMA vez por run (morrer e tentar de novo não repete); START pula.

#include "levels/story.h"
#include "levels/graph.h"           // N_* (nós do grafo)

#define CENA(nome)          static const StoryLine cena_##nome[] = {
#define ESQUERDA(p, txt)    { LADO_ESQ, (p), (txt) },
#define DIREITA(p, txt)     { LADO_DIR, (p), (txt) },
#define FIM                 };
#define QUANDO(no, momento, nome) \
    { (no), (momento), cena_##nome, sizeof(cena_##nome) / sizeof(StoryLine) }

// ---------------------------------------------------------------------------
// AS CENAS
// ---------------------------------------------------------------------------

CENA(abertura)
    ESQUERDA(P_REX,     "AQUI E REX. CHEGUEI AO SETOR 7. OS INSETOS-MAQUINA ESTAO POR TODA PARTE.")
    DIREITA(P_COMANDO,  "REX, A COLONIA INTEIRA DEPENDE DE VOCE. LIMPE O SETOR, AREA POR AREA.")
    ESQUERDA(P_REX,     "ENTENDIDO, COMANDO. NENHUM INSETO VAI SOBRAR.")
FIM

CENA(rota_limpa)            // 2A: venceu a fase 1 sem gastar bomba
    DIREITA(P_COMANDO,  "SEGUROU AS BOMBAS! ASSIM QUE SE FAZ. A ROTA LIMPA ESTA ABERTA.")
    ESQUERDA(P_REX,     "GUARDO ELAS PARA QUANDO A COISA APERTAR.")
FIM

CENA(rota_da_lama)          // 2B: gastou bomba na fase 1
    DIREITA(P_COMANDO,  "UMA BOMBA LOGO NA CHEGADA... O ARSENAL E LIMITADO, REX.")
    ESQUERDA(P_REX,     "ANOTADO. A LAMA DESTE SETOR VAI ME LEMBRAR DISSO.")
FIM

CENA(retirada)              // 6B: o aliado caiu na fase 5
    DIREITA(P_COMANDO,  "PERDEMOS O ALIADO... ELES ESTAO EM CIMA DE VOCE! RECUE LUTANDO!")
    ESQUERDA(P_REX,     "EU NAO ESQUECO QUEM CAI. VOU ABRIR CAMINHO NA MARRA.")
FIM

CENA(rumo_ao_chefe)         // venceu a 15: o sinal da rainha
    DIREITA(P_COMANDO,  "SINAL ENORME A FRENTE... E ELA. A LACRAIA, A RAINHA DO ENXAME.")
    ESQUERDA(P_REX,     "ENTAO E AQUI QUE ISSO TERMINA.")
FIM

CENA(confronto)             // chegando no chefe
    DIREITA(P_LACRAIA,  "SSSKREEE... O MECH VERMELHO. MEUS FILHOS VAO DEVORAR SEU METAL.")
    ESQUERDA(P_REX,     "VEM BUSCAR.")
FIM

CENA(final)                 // chefe derrotado
    ESQUERDA(P_REX,     "COMANDO, A LACRAIA CAIU. O SETOR ESTA LIVRE.")
    DIREITA(P_COMANDO,  "VOCE CONSEGUIU, REX! VOLTE PARA CASA. VOCE MERECE.")
    ESQUERDA(P_REX,     "REX, DESLIGANDO.")
FIM

// ---------------------------------------------------------------------------
// ONDE CADA CENA TOCA (nó do grafo + momento)
// ---------------------------------------------------------------------------

const StoryEntry STORY[] =
{
    QUANDO(N_1,   ANTES,  abertura),
    QUANDO(N_2A,  ANTES,  rota_limpa),
    QUANDO(N_2B,  ANTES,  rota_da_lama),
    QUANDO(N_6B,  ANTES,  retirada),
    QUANDO(N_15,  DEPOIS, rumo_ao_chefe),
    QUANDO(N_16,  ANTES,  confronto),
    QUANDO(N_16,  DEPOIS, final),
};

const u16 STORY_COUNT = sizeof(STORY) / sizeof(STORY[0]);

const StoryEntry *STORY_find(u8 node, u8 when)
{
    for (u16 i = 0; i < STORY_COUNT; i++)
        if (STORY[i].node == node && STORY[i].when == when) return &STORY[i];
    return NULL;
}
