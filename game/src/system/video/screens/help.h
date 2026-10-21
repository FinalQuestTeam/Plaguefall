#ifndef HELP_H
#define HELP_H

#include <genesis.h>

// Seis páginas: controles, coleta, inventário, inimigos, elite e missões/rotas.
// HELP_run: laço do título. HELP_open/update: consulta dentro do pause.
void HELP_run(void);
void HELP_open(void);
bool HELP_update(u16 pressed);

#endif // HELP_H
