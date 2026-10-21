// ROTEIRO DO JOGO — este é o ÚNICO arquivo a editar para mudar as falas na ROM.
// Universo, abertura extensa e campanha: doc/historia/README.md.
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
    ESQUERDA(P_REX,     "VOCE JA OUVIU FALAR QUE O DIABO DA TUDO QUE A GENTE QUER?")
    ESQUERDA(P_REX,     "MAS SEMPRE DA MANEIRA MAIS FILHA DA PUTA POSSIVEL?")
    ESQUERDA(P_REX,     "EU SONHAVA COM ASTRONAUTAS, EXTRATERRESTRES E FOGUETES QUE DAVAM RE.")
    ESQUERDA(P_REX,     "AGORA TO ASSIM. BRACO DE SUCATA, CHAPEU COM RADIO E O BRASIL CHEIO DE BARATAS.")
    ESQUERDA(P_REX,     "OS FOGUETES VOLTARAM. TROUXERAM NINHOS. EU SO QUERIA UMA CARONA.")
    DIREITA(P_COMANDO,  "REX, AQUI E O PADRE. SEGURE O PATIO. TEM GENTE FUGINDO PELO FUNDO.")
    ESQUERDA(P_REX,     "TO INDO. HOJE NINGUEM VAI PRO CEU ANTES DA HORA.")
FIM

CENA(rota_limpa)            // 2A: venceu a fase 1 sem gastar bomba
    DIREITA(P_COMANDO,  "SEM EXPLOSAO, ELES AINDA NAO FECHARAM A RUA DE SERVICO. SIGA POR ELA.")
    ESQUERDA(P_REX,     "BOM. GUARDO O ESTOURO PRA QUEM MANDOU ESSAS BARATAS.")
FIM

CENA(rota_da_lama)          // 2B: gastou bomba na fase 1
    DIREITA(P_COMANDO,  "O CLARAO DA BOMBA ENTREGOU SUA POSICAO. VA PELO BAIXIO DO TERMINAL.")
    ESQUERDA(P_REX,     "FOGUETE POUSA DE PE. EU VOU AFUNDANDO NA LAMA. PROGRESSO E ISSO AI.")
FIM

CENA(sangria)
    DIREITA(P_COMANDO,  "CUIDADO COM OS VAZAMENTOS DOS MOTORES. O CHAO AINDA ESTA QUEIMANDO.")
    ESQUERDA(P_REX,     "EU VIA O POUSO PELA TV. NAO MOSTRAVAM O QUE SOBRAVA AQUI EMBAIXO.")
FIM

CENA(canal)
    DIREITA(P_COMANDO,  "OS BICHOS TOMARAM O CANAL DE MANUTENCAO. NA LAMA, ELES TE ALCANCAM.")
    ESQUERDA(P_REX,     "CONSERTEI ESSE LUGAR POR ANOS. AGORA VOU TER QUE PASSAR ATIRANDO.")
FIM

CENA(capela)
    DIREITA(P_COMANDO,  "O RADIO FICA NA BASE DA SANTA. PROTEJA O PONTO POR TRINTA SEGUNDOS.")
    DIREITA(P_COMANDO,  "PRECISAMOS DESSE TEMPO PARA TRANSMITIR AOS ABRIGOS.")
    ESQUERDA(P_REX,     "MINHA MAE MANDOU LEVAR UMA REZA. HOJE EU FACO A ESCOLTA.")
FIM

CENA(ponto_salvo)           // 6A: protegeu a santa/estacao na fase 5
    DIREITA(P_COMANDO,  "O PONTO RESISTIU. OUVI RESPOSTAS DOS ABRIGOS. SIGA PELOS FUNDOS DA CAPELA.")
    ESQUERDA(P_REX,     "TEM GENTE DO OUTRO LADO. JA E MOTIVO PRA CONTINUAR.")
FIM

CENA(retirada)              // 6B: a santa/estacao caiu na fase 5
    DIREITA(P_COMANDO,  "ATINGIRAM A SANTA. PERDEMOS O PONTO DE RADIO. O CERCO FECHOU. RECUE LUTANDO!")
    ESQUERDA(P_REX,     "NAO CONSEGUI SEGURAR. MAS AINDA TEM GENTE PRECISANDO DE NOS.")
FIM

CENA(rede)                  // convergencia: nao presume o resultado da fase 5
    DIREITA(P_DINORAH,  "REX, AQUI E DINORAH. AINDA HA VOZES NA REDE. SIGA PELO BAIXIO DAS ANTENAS.")
    ESQUERDA(P_REX,     "ENQUANTO TIVER ALGUEM RESPONDENDO, ESSE BANDO NAO ACABA.")
FIM

CENA(carga)
    DIREITA(P_COMANDO,  "OS NINHOS VIERAM NAS CARGAS DO ESPACO. CADA POUSO ALIMENTAVA O ENXAME.")
    ESQUERDA(P_REX,     "EU CONSERTAVA AQUELES FOGUETES. ME VENDIAM O CEU E DESCARREGAVAM ISSO.")
FIM

CENA(alfandega)
    DIREITA(P_COMANDO,  "AS SAUVAS ESTAO USANDO NOSSO EQUIPAMENTO. ELAS GUARDAM O ACESSO A MATRIZ.")
    ESQUERDA(P_REX,     "TEM METAL NAS BARATAS E BARATA NAS MAQUINAS. VOU ABRIR ESSE CAMINHO.")
FIM

CENA(acesso_tecnico)        // 10A: venceu a fase 9 sem sofrer dano
    DIREITA(P_COMANDO,  "VOCE SAIU INTEIRO. DA PARA SEGUIR PELO ACESSO DOS TECNICOS.")
    ESQUERDA(P_REX,     "FINALMENTE UMA PORTA QUE MEU ANTIGO EMPREGO ABRE.")
FIM

CENA(dreno)                 // 10B: sofreu dano na fase 9
    DIREITA(P_COMANDO,  "VOCE FOI ATINGIDO. SAIA DO CERCO PELO DRENO. CUIDADO COM O CALOR E A LAMA.")
    ESQUERDA(P_REX,     "AINDA TO DE PE. ME PASSE O CAMINHO.")
FIM

CENA(aviso)
    DIREITA(P_COMANDO,  "ACHEI OS ALERTAS DE CONTAMINACAO. O CONSORCIO SABIA. MANTEVE AS ENTREGAS.")
    ESQUERDA(P_REX,     "O DIABO PELO MENOS TEM FAMA. ESSES VENDIAM PROPAGANDA DE FUTURO.")
FIM

CENA(comporta)
    DIREITA(P_COMANDO,  "A COMPORTA DE CARGA ESTA FECHANDO. TENTE ALCANCAR A PASSAGEM DIRETA.")
    ESQUERDA(P_REX,     "COM ESSAS BARATAS APARECENDO DO NADA, VAI SER NO APERTO.")
FIM

CENA(linha_quente)          // 13A: venceu a fase 12 em menos de 60 segundos
    DIREITA(P_COMANDO,  "DEU TEMPO. A LINHA QUENTE AINDA ESTA ABERTA. E O CAMINHO DIRETO.")
    ESQUERDA(P_REX,     "PODE DEIXAR. HOJE EU NAO PERCO ESSA PASSAGEM.")
FIM

CENA(decantacao)            // 13B: venceu a fase 12 em 60 segundos ou mais
    DIREITA(P_COMANDO,  "A PASSAGEM FECHOU. RESTA O CANAL DE DECANTACAO. VAI TER LAMA ATE O FIM.")
    ESQUERDA(P_REX,     "ENTAO E PELO CANAL. AINDA DA PRA CHEGAR.")
FIM

CENA(patio_enxames)
    DIREITA(P_COMANDO,  "A MATRIZ PERCEBEU VOCE. ESTAO VINDO EM GRUPOS MAIORES.")
    ESQUERDA(P_REX,     "ELA TEM UM ENXAME DE BARATAS. EU TENHO VOCES NO RADIO. VAMOS ABRIR CAMINHO.")
FIM

CENA(boca_terminal)
    DIREITA(P_COMANDO,  "ULTIMO BLOQUEIO ANTES DO NINHO. A RESISTENCIA ESTA ESPERANDO SEU SINAL.")
    ESQUERDA(P_REX,     "PASSEI A VIDA QUERENDO SUBIR. AGORA SO QUERO PODER VOLTAR PRA CASA.")
FIM

CENA(rumo_ao_chefe)         // venceu a 15: o sinal da rainha
    DIREITA(P_COMANDO,  "LOCALIZEI A MATRIZ SOB O TERMINAL. E A LACRAIA. ELA COMANDA ESTE ENXAME.")
    ESQUERDA(P_REX,     "ENTAO VOU CORTAR O COMANDO DELES. FIQUE NO RADIO.")
FIM

CENA(confronto)             // chegando no chefe
    DIREITA(P_COMANDO,  "TEM UMA VOZ NA INTERFERENCIA. REX, E ELA.")
    DIREITA(P_LACRAIA,  "QUERIA VIAJAR, HUMANO? HA LUGAR PARA SUA CARNE NA PROXIMA CARGA.")
    ESQUERDA(P_REX,     "JA ENTENDI ESSA OFERTA. VOU FICAR COM O CHAO.")
FIM

CENA(final)                 // chefe derrotado
    ESQUERDA(P_REX,     "COMANDO, A LACRAIA CAIU. O SINAL DELA PAROU.")
    DIREITA(P_COMANDO,  "O BRASIL AINDA TEM MUITO CHAO OCUPADO. MAS HOJE VOCE PODE VOLTAR PRA CASA.")
    ESQUERDA(P_REX,     "EU AINDA QUERO VER O MUNDO LA DE CIMA. PRIMEIRO, VAMOS SALVAR O QUE FICOU AQUI.")
FIM

// ---------------------------------------------------------------------------
// ONDE CADA CENA TOCA (nó do grafo + momento)
// ---------------------------------------------------------------------------

const StoryEntry STORY[] =
{
    QUANDO(N_1,   ANTES,  abertura),
    QUANDO(N_2A,  ANTES,  rota_limpa),
    QUANDO(N_2B,  ANTES,  rota_da_lama),
    QUANDO(N_3,   ANTES,  sangria),
    QUANDO(N_4,   ANTES,  canal),
    QUANDO(N_5,   ANTES,  capela),
    QUANDO(N_6A,  ANTES,  ponto_salvo),
    QUANDO(N_6B,  ANTES,  retirada),
    QUANDO(N_7,   ANTES,  rede),
    QUANDO(N_8,   ANTES,  carga),
    QUANDO(N_9,   ANTES,  alfandega),
    QUANDO(N_10A, ANTES,  acesso_tecnico),
    QUANDO(N_10B, ANTES,  dreno),
    QUANDO(N_11,  ANTES,  aviso),
    QUANDO(N_12,  ANTES,  comporta),
    QUANDO(N_13A, ANTES,  linha_quente),
    QUANDO(N_13B, ANTES,  decantacao),
    QUANDO(N_14,  ANTES,  patio_enxames),
    QUANDO(N_15,  ANTES,  boca_terminal),
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
