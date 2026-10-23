# Cinza e Silêncio — tema de derrota aprovado

[Ouvir MP3](cinza-e-silencio.mp3) · [WAV](cinza-e-silencio.wav)

A composição aprovada toca uma vez na tela de derrota, após a animação da
queda. Substitui a música da fase por quatro segundos; depois fica em silêncio
até tentar novamente ou voltar ao título. Uma confirmação antecipada encerra
a frase. O tema de vitória continua nas conclusões bem-sucedidas e no final
da campanha. A perda do sinal mantém o áudio de mudança de rota.

São quatro segundos, três compassos de 2/4 a 90 BPM. A queda Ré–Lá–Fá responde
à subida da abertura e da vitória. Uma frase mais baixa, com uma breve pausa,
leva de Dó sustenido a Ré. A harmonia percorre Dm–Bb–Gm–A7–Dm(add9), com o
Mi como cor passageira na chegada, antes da sustentação final de Ré menor.
O tom é de perda e cansaço, com uma resolução que permite tentar novamente.

Três vozes tonais e um canal de ruído PSG, sem amostras. O baixo conserva uma
lembrança mais espaçada do baião; os ataques metálicos desaparecem antes da
frase final. A gravação usa Genesis Plus GX e o árbitro de áudio de produção.
O MP3/WAV de audição remove o silêncio/transiente do boot e aplica ganho
constante de +20 dB, sem compressão, equalização ou efeitos. As capturas brutas
PAL/NTSC permanecem em capture-*.wav; validation.json registra duração e picos.

compose.py exporta a mesma partitura aprovada para o motor em
src/system/audio/game_over_data.h e para a bancada isolada. O motor compartilha
o relógio de 600 Hz e os envelopes com o tema de vitória. As gravações acima
preservam a audição aprovada antes da integração.

## Reproduzir a prévia

Na raiz do projeto:

```sh
python3 game/art/audio-game-over-v1/compose.py
python3 game/art/audio-game-over-v1/compose.py --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game/art/audio-game-over-v1/bench -j4
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py --rom game/art/audio-game-over-v1/bench/out/release/rom.bin --seconds 6 --output game/art/audio-game-over-v1/capture-ntsc.wav
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py --rom game/art/audio-game-over-v1/bench/out/release/rom.bin --seconds 6 --pal --output game/art/audio-game-over-v1/capture-pal.wav
python3 game/art/audio-game-over-v1/prepare_preview.py
ffmpeg -hide_banner -loglevel error -y -i game/art/audio-game-over-v1/cinza-e-silencio.wav -codec:a libmp3lame -q:a 2 -metadata title="Cinza e Silêncio" -metadata artist="Plaguefall" game/art/audio-game-over-v1/cinza-e-silencio.mp3
```

START repete a composição na ROM de audição.

## Validar a integração

O teste nativo de áudio confere notas, quatro segundos em PAL/NTSC, silêncio
sem loop, retomada da trilha suspensa, interrupção e troca entre os dois temas.
O teste de ROM prepara cenários por RAM, mas executa os cartões, músicas,
confirmações e retornos pelo código de produção. Captura derrota no início
e no chefe, objetivo cumprido, sinal protegido, sinal perdido e vitória final.

```sh
arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py --audio-only --build-dir game/out/result-audio --output game/art/audio-game-over-v1/integration-validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py --audio-only --pal --build-dir game/out/result-audio --output game/art/audio-game-over-v1/integration-validation/pal
```

Os relatórios e WAVs ficam em integration-validation/. A compilação isolada
em game/out/result-audio permite validar uma ROM estável durante outros builds.

Os seis cenários passaram em NTSC e PAL: derrota na primeira fase e no chefe,
objetivo cumprido, sinal protegido, sinal perdido e vitória final. Os WAVs
verificam execução única e silêncio após a soltura. As confirmações de repetir,
seguir, voltar ao título e sair antes do final da música também foram conferidas.
Os testes nativos com ASan/UBSan passaram nos três perfis de trilha e na abertura.
