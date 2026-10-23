// ROTEIRO DO JOGO — este é o ÚNICO arquivo a editar para mudar as falas na ROM.
// Universo, abertura extensa e campanha: doc/historia/README.md.
//
// COMO ESCREVER UMA CENA:
//
//   CENA(abertura)
//       ESQUERDA(P_DAMIAO,    "ONDE ESTOU? ESTE SETOR ESTA INFESTADO.")
//       DIREITA(P_COMANDO, "DAMIAO, ELES TOMARAM A BASE! LIMPE A AREA.")
//   FIM
//
//   - ESQUERDA(retrato, "fala")  → retrato no canto superior esquerdo fala
//   - DIREITA(retrato, "fala")   → retrato no canto inferior direito fala
//   - A ordem das linhas é a ordem da conversa: intercale como quiser.
//   - O retrato é escolhido POR FALA: o mesmo personagem pode trocar de
//     expressão no meio da cena, ou um terceiro pode entrar no mesmo canto.
//   - Escreva a fala corrida, em MAIÚSCULA COM ACENTOS ("VOCÊ", "ENTÃO");
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
    // O monologo completo agora toca no boot (screens/intro.c), antes do menu.
    // Na fase, mantem apenas o chamado que apresenta a missao.
    DIREITA(P_COMANDO,  "DAMIÃO, AQUI É O PADRE. SEGURE O PÁTIO. TEM GENTE FUGINDO PELO FUNDO.")
    ESQUERDA(P_DAMIAO,     "TÔ INDO. HOJE NINGUÉM VAI PRO CÉU ANTES DA HORA.")
FIM

CENA(rota_limpa)            // 2A: venceu a fase 1 sem gastar bomba
    DIREITA(P_COMANDO,  "TODOS PASSARAM PELO FUNDO. A IGREJA FICOU INTEIRA. SIGA PELA RUA DE SERVIÇO.")
    ESQUERDA(P_DAMIAO,     "BOM. GUARDO O ESTOURO PRA QUEM MANDOU ESSAS BARATAS.")
FIM

CENA(rota_da_lama)          // 2B: gastou bomba na fase 1
    DIREITA(P_COMANDO,  "A BOMBA LEVOU PARTE DA IGREJA. OS ESCOMBROS FECHARAM A RUA. VÁ PELO BAIXIO.")
    ESQUERDA(P_DAMIAO,     "FOGUETE POUSA DE PÉ. EU VOU AFUNDANDO NA LAMA. PROGRESSO É ISSO AÍ.")
FIM

CENA(sangria)
    DIREITA(P_COMANDO, "ESTE GALPÃO É O NOVO ABRIGO. SEGURE OS BICHOS ENQUANTO PENSAMOS NO CAMINHO.")
    ESQUERDA(P_DAMIAO, "AS REDES AINDA ESTÃO ARMADAS. NINGUÉM SAI CORRENDO OUTRA VEZ.")
    DIREITA(P_COMANDO, "CUIDADO COM OS VAZAMENTOS. O CALOR TOMOU BOA PARTE DO PISO.")
FIM

CENA(canal)
    DIREITA(P_COMANDO, "VAMOS PELOS TÚNEIS DE MANUTENÇÃO. VÁ NA FRENTE E ABRA CAMINHO PARA O GRUPO.")
    ESQUERDA(P_DAMIAO, "CONSERTEI ESSAS VÁLVULAS POR ANOS. AINDA SEI ONDE O CHÃO AGUENTA.")
FIM

CENA(capela)
    DIREITA(P_COMANDO, "HÁ UM SINALIZADOR DENTRO DA SANTA. PROTEJA A BASE POR TRINTA SEGUNDOS.")
    DIREITA(P_COMANDO, "SE O SINAL CHEGAR, AS NAVES DE RESGATE VÊM BUSCAR OS REFUGIADOS.")
    ESQUERDA(P_DAMIAO, "MINHA MÃE MANDOU LEVAR UMA REZA. HOJE EU FAÇO A ESCOLTA.")
FIM

CENA(ponto_salvo)
    DIREITA(P_COMANDO, "DEU CERTO. AS NAVES LEVARAM O POVO. FALTA LIMPAR O PERÍMETRO.")
    DIREITA(P_DINORAH, "DEPOIS VAMOS AOS NINHOS PERTO DA BASE DE LANÇAMENTO. PRECISAMOS VER A EXTENSÃO.")
    ESQUERDA(P_DAMIAO, "AGORA QUE ELES ESTÃO LONGE, A GENTE PODE IR ATÉ A RAIZ DESSE INFERNO.")
FIM

CENA(retirada)
    DIREITA(P_DINORAH, "O SINAL CAIU, DAMIÃO. EU TE PEDI UMA COISA: PROTEGER QUEM NÃO PODIA LUTAR.")
    ESQUERDA(P_DAMIAO, "EU ESTAVA AQUI. TENTEI SEGURAR TODOS OS LADOS.")
    DIREITA(P_COMANDO, "DINORAH, AINDA PODEMOS TIRAR O GRUPO POR TERRA. NÃO É HORA DE NOS SEPARAR.")
    DIREITA(P_DINORAH, "EU VOU COM ELES. DEPOIS A GENTE CONVERSA, SE AINDA HOUVER O QUE DIZER.")
FIM

CENA(rede)
    DIREITA(P_COMANDO, "OS RASTROS SEGUEM OS CABOS ATÉ A BASE. VÁ PELO BAIXIO DAS ANTENAS.")
    ESQUERDA(P_DAMIAO, "A CADA FIO QUE EU SEGURO, APARECE OUTRO NINHO. VOU ACHAR DE ONDE ISSO VEM.")
FIM

CENA(carga)
    DIREITA(P_COMANDO,  "OS NINHOS VIERAM NAS CARGAS DO ESPAÇO. CADA POUSO ALIMENTAVA O ENXAME.")
    ESQUERDA(P_DAMIAO,     "EU CONSERTAVA AQUELES FOGUETES. ME VENDIAM O CÉU E DESCARREGAVAM ISSO.")
FIM

CENA(alfandega)
    DIREITA(P_COMANDO,  "AS SAÚVAS ESTÃO USANDO NOSSO EQUIPAMENTO. ELAS GUARDAM O ACESSO A MATRIZ.")
    ESQUERDA(P_DAMIAO,     "TEM METAL NAS BARATAS E BARATA NAS MÁQUINAS. VOU ABRIR ESSE CAMINHO.")
FIM

CENA(acesso_tecnico)        // 10A: venceu a fase 9 sem sofrer dano
    DIREITA(P_COMANDO,  "VOCÊ SAIU INTEIRO. DÁ PARA SEGUIR PELO ACESSO DOS TÉCNICOS.")
    ESQUERDA(P_DAMIAO,     "FINALMENTE UMA PORTA QUE MEU ANTIGO EMPREGO ABRE.")
FIM

CENA(dreno)                 // 10B: sofreu dano na fase 9
    DIREITA(P_COMANDO,  "VOCÊ FOI ATINGIDO. SAIA DO CERCO PELO DRENO. CUIDADO COM O CALOR E A LAMA.")
    ESQUERDA(P_DAMIAO,     "AINDA TÔ DE PÉ. ME PASSE O CAMINHO.")
FIM

CENA(aviso)
    DIREITA(P_COMANDO,  "ACHEI OS ALERTAS DE CONTAMINAÇÃO. O CONSÓRCIO SABIA. MANTEVE AS ENTREGAS.")
    ESQUERDA(P_DAMIAO,     "O DIABO PELO MENOS TEM FAMA. ESSES VENDIAM PROPAGANDA DE FUTURO.")
FIM

CENA(comporta)
    DIREITA(P_COMANDO,  "A COMPORTA DE CARGA ESTÁ FECHANDO. TENTE ALCANÇAR A PASSAGEM DIRETA.")
    ESQUERDA(P_DAMIAO,     "COM ESSAS BARATAS APARECENDO DO NADA, VAI SER NO APERTO.")
FIM

CENA(linha_quente)          // 13A: venceu a fase 12 em menos de 60 segundos
    DIREITA(P_COMANDO,  "DEU TEMPO. A LINHA QUENTE AINDA ESTÁ ABERTA. É O CAMINHO DIRETO.")
    ESQUERDA(P_DAMIAO,     "PODE DEIXAR. HOJE EU NÃO PERCO ESSA PASSAGEM.")
FIM

CENA(decantacao)            // 13B: venceu a fase 12 em 60 segundos ou mais
    DIREITA(P_COMANDO,  "A PASSAGEM FECHOU. RESTA O CANAL DE DECANTAÇÃO. VAI TER LAMA ATÉ O FIM.")
    ESQUERDA(P_DAMIAO,     "ENTÃO É PELO CANAL. AINDA DÁ PRA CHEGAR.")
FIM

CENA(patio_enxames)
    DIREITA(P_COMANDO,  "A MATRIZ PERCEBEU VOCÊ. ESTÃO VINDO EM GRUPOS MAIORES.")
    ESQUERDA(P_DAMIAO,     "ELA TEM UM ENXAME DE BARATAS. EU TENHO VOCÊS NO RÁDIO. VAMOS ABRIR CAMINHO.")
FIM

CENA(boca_terminal)
    DIREITA(P_COMANDO,  "ÚLTIMO BLOQUEIO ANTES DO NINHO. A RESISTÊNCIA ESTÁ ESPERANDO SEU SINAL.")
    ESQUERDA(P_DAMIAO,     "PASSEI A VIDA QUERENDO SUBIR. AGORA SÓ QUERO PODER VOLTAR PRA CASA.")
FIM

CENA(rumo_ao_chefe)         // venceu a 15: o sinal da matriz
    DIREITA(P_COMANDO,  "LOCALIZEI A MATRIZ SOB O TERMINAL. É O ESCORPIÃO. ELE COMANDA ESTE ENXAME.")
    ESQUERDA(P_DAMIAO,     "ENTÃO VOU CORTAR O COMANDO DELES. FIQUE NO RÁDIO.")
FIM

CENA(confronto)             // chegando no chefe
    DIREITA(P_COMANDO,  "TEM UMA VOZ NA INTERFERÊNCIA. DAMIÃO, É ELE.")
    DIREITA(P_ESCORPIAO,  "QUERIA VIAJAR, HUMANO? HÁ LUGAR PARA SUA CARNE NA PRÓXIMA CARGA.")
    ESQUERDA(P_DAMIAO,     "JÁ ENTENDI ESSA OFERTA. VOU FICAR COM O CHÃO.")
FIM

CENA(final)                 // chefe derrotado
    ESQUERDA(P_DAMIAO,     "COMANDO, O ESCORPIÃO CAIU. O SINAL DELE PAROU.")
    DIREITA(P_COMANDO,  "O BRASIL AINDA TEM MUITO CHÃO OCUPADO. MAS HOJE VOCÊ PODE VOLTAR PRA CASA.")
    ESQUERDA(P_DAMIAO,     "EU AINDA QUERO VER O MUNDO LÁ DE CIMA. PRIMEIRO, VAMOS SALVAR O QUE FICOU AQUI.")
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
