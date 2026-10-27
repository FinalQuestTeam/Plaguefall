// Ponto de entrada: só sobe o fluxo do jogo. Toda a lógica (máquina de estados,
// telas, fases) vive em módulos próprios — o fluxo em core/flow.c.

#include <genesis.h>
#include "core/flow.h"

int main(bool hardReset)
{
    // SGDK soft reset retains static pointers into panels/streaming caches.
    // Start with clean RAM too: session continuation is provided by the code.
    if(!hardReset)SYS_hardReset();
    FLOW_run();     // inicializa os subsistemas e roda o jogo (nunca retorna)
    return 0;
}
