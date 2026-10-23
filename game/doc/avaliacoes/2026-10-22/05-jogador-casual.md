# Avaliação de Plaguefall pela perspectiva de jogador casual

O título, a voz de Damião e o universo do sertão industrial dão motivos para experimentar. O desafio da primeira sessão é transformar essa curiosidade em domínio dos controles e vontade de tentar novamente.

Esta é uma análise heurística da perspectiva casual, baseada em capturas reais e leitura do fluxo. Não representa uma pessoa jogando. Diversão, frustração, duração percebida e vontade de voltar precisam ser observadas em playtest humano.

## Impressões e achados

1. **Ponto forte — O gancho temático tem personalidade.** O rádio apresenta padre, igreja e pessoas fugindo, com uma fala curta que caracteriza Damião: “hoje ninguém vai pro céu antes da hora”. O jogador recebe um motivo concreto para enfrentar a arena. Preservar essa voz nas pequenas recompensas entre fases. Evidência: [roteiro inicial](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/levels/story.c:42). Capturas inspecionadas: `titulo-apos-derrota.png` e `radio-damiao.png` das suites desta avaliação.

2. **P1 — As regras iniciais podem exigir explicação demais.** O direcional move e mira; a arma conserva a última direção; C seleciona e B usa; alguns pickups têm efeito automático e outros viram inventário. Esses fatos estão distribuídos nas seis páginas da ajuda. Um iniciante pode tentar fugir mantendo a mira no alvo e não entender a mudança de direção, ou guardar recursos sem perceber. Ensinar tiro, direção e um item em passos curtos na primeira arena. Critério sugerido: a pessoa explica essas três ações após dois minutos, sem orientação externa. Evidência: [ajuda](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/help_copy.h:4).

3. **P1 — Repetir é claro, mas pode apagar a sensação de crescimento.** A derrota oferece tentar novamente na mesma fase, com vida cheia e equipamento básico; a tela informa a perda de itens e melhorias. A clareza ajuda, mas uma nova tentativa mais fraca pode desanimar após uma morte tardia. Comparar duas tentativas consecutivas com iniciantes, observando se compreendem a perda e ainda querem insistir. Evidências: [texto da derrota](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/result.c:160), [regra efetiva](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/core/flow.c:512).

4. **P1 — A campanha exige continuidade sem explicar seu compromisso de tempo.** A ajuda anuncia 16 etapas; o menu não oferece “Continuar”; sair avisa que o progresso será perdido. Uma pessoa com pouco tempo pode adiar o retorno depois de interromper uma sessão. Avaliar checkpoint ou retomada e comunicar progresso global. Não há base para estimar a duração total em minutos nesta avaliação. Evidências: [16 etapas](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/help_copy.h:93), [menu](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/title.c:25), [saída](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/pause.c:66).

5. **P2 — O jogo comunica progresso melhor nos intervalos que durante a ação.** A tela de conclusão celebra o objetivo e informa destino; a pausa mostra objetivo e item. Isso dá contexto às arenas, mas ainda deve ser verificado se o jogador lembra a missão sem interromper o combate. Aproximar as informações essenciais da ação, sobretudo em chefe e rotas condicionais. Evidências: [conclusão](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/result.c:180), [pausa](/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/src/system/video/screens/pause.c:32).

## Escolha recomendada

Fazer uma primeira sessão observada com 3–5 pessoas sem familiaridade com o projeto. Registrar descoberta de controles, primeiro uso de item, primeira morte, compreensão da recuperação e vontade de voltar em outro dia. Esses dados devem decidir entre aprofundar onboarding, suavizar perdas e implementar retomada. A necessidade de um save é uma hipótese de uso casual, não uma obrigação já demonstrada.
