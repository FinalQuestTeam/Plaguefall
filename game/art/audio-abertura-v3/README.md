# O Sonho Atendido — montagem aprovada

A partitura acompanha os **14 planos e 18 cartelas** do [storyboard aprovado](../../doc/historia/storyboard-abertura-v2.md). A reserva de **108 segundos** contém 4 segundos de logo Plaguefall, 101 segundos de monólogo e 3 segundos de sustentação para absorver as cargas de imagem.

[Ouvir a gravação real em MP3](o-sonho-atendido.mp3) · [Áudio capturado da ROM](../intro-monologo-v2/emulator-ntsc/opening.wav) · [Vídeo da ROM](../intro-monologo-v2/emulator-ntsc/abertura.mp4).

Os temas originais foram reorganizados para seguir a nova montagem: provocação, sonho, trabalho, carga e ovos, ausência dos tripulantes, invasores, prótese e comunidade, reza, rádio, retirada e resposta final. Carga/ovos e custo pessoal/comunidade compartilham frases musicais através da mudança de imagem. O pulso do rádio sustenta a retirada, e o encerramento resolve em Ré menor.

Não há reinício, pausa ou fade musical nas trocas de imagem ou de legenda. O relógio de 300Hz continua por interrupção vertical enquanto a imagem é carregada. A entrada do logo e a saída natural ou com START são os únicos fades de áudio. As quatro músicas de galeria/campanha permanecem preservadas.

Os testes nativos do motor com ASan/UBSan conferem 106 segundos contínuos em 50/60Hz, término sem loop, fade de START, remoção do callback e restauração da música de jogo. As [verificações no emulador](../intro-monologo-v2/README.md) conferem a continuidade desde o logo até o menu, sem pausas ou resets do relógio.

[Partitura editável](../../tools/compose_opening.py) · [Eventos gerados](../../src/system/audio/opening_data.h) · [Versão anterior preservada](../audio-abertura-v2/README.md).
