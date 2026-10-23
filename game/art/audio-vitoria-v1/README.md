# Mais um Amanhecer — tema de vitória

Composição original para o encerramento das fases de Plaguefall. Dois compassos
de 2/4 a 120 BPM, com duração musical de dois segundos e execução única.

[Ouvir MP3](mais-um-amanhecer.mp3) · [WAV](mais-um-amanhecer.wav)

A melodia Ré–Fá–Lá–Ré agudo / Dó–Lá–Ré agudo retoma a subida da abertura
O Sonho Atendido. A harmonia Dm–G–A7–D passa do menor à resolução maior,
com baixo de baião e ataques metálicos curtos. O último tempo deixa a melodia
e o baixo sustentarem a chegada enquanto o acompanhamento explicita o Fá sustenido.

São três vozes tonais e um canal de ruído PSG. A ROM de audição usa o árbitro
de áudio de produção; a gravação vem do Genesis Plus GX. A prévia remove o
transiente de inicialização e o silêncio do boot, e aplica ganho constante
de +20 dB, sem efeitos, equalização ou compressão. Os arquivos capture-ntsc.wav
e capture-pal.wav preservam as capturas brutas. A prévia tem aproximadamente
2,2 segundos incluindo a margem de silêncio para reprodução.

O tema aprovado toca nas telas de objetivo cumprido e de vitória final da
campanha. Substitui a música de fundo por uma execução única; depois fica em
silêncio até fechar o resultado. A confirmação antecipada encerra a frase.
As derrotas usam o tema aprovado [Cinza e Silêncio](../audio-game-over-v1/README.md).
A perda do sinal mantém seu áudio anterior. A galeria mantém as quatro faixas
existentes.

compose.py exporta a mesma partitura para victory_data.h e para a bancada.
A bancada usa MUSIC_playVictory() e MUSIC_update() do motor de produção.
As capturas e o MP3 acima preservam a prévia originalmente aprovada; os ensaios
da integração ficam em integration-validation/.

## Reproduzir

Execute na raiz do repositório:

```sh
python3 game/art/audio-vitoria-v1/compose.py
python3 game/art/audio-vitoria-v1/compose.py --check
PATH="/opt/homebrew/opt/openjdk/bin:$PATH" make -C game/art/audio-vitoria-v1/bench -j4
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py --rom game/art/audio-vitoria-v1/bench/out/release/rom.bin --seconds 4 --output game/art/audio-vitoria-v1/capture-ntsc.wav
arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py --rom game/art/audio-vitoria-v1/bench/out/release/rom.bin --seconds 4 --pal --output game/art/audio-vitoria-v1/capture-pal.wav
python3 game/art/audio-vitoria-v1/prepare_preview.py
ffmpeg -hide_banner -loglevel error -y -i game/art/audio-vitoria-v1/mais-um-amanhecer.wav -codec:a libmp3lame -q:a 2 -metadata title="Mais um Amanhecer" -metadata artist="Plaguefall" game/art/audio-vitoria-v1/mais-um-amanhecer.mp3
```

A bancada toca uma vez no boot; START repete. validation.json registra duração
audível em PAL/NTSC, ausência de clipping e o hash da ROM usada nas capturas.

## Validação da integração

Os testes nativos de music_test.c usam ASan/UBSan nos perfis padrão, melancólico
e sombrio. Conferem as notas aprovadas, duração PAL/NTSC, silêncio sem loop,
retomada exata da música suspensa, cancelamento e reinício, quadros perdidos,
chamadas duplicadas e virada do contador de VBlank. A abertura também foi
verificada com o motor atualizado.

O teste focado na ROM percorre objetivo cumprido, proteção bem-sucedida,
perda do sinal e vitória final, além de confirmar a saída antecipada. Captura
o áudio das telas reais e verifica silêncio após o final da música. Os
relatórios NTSC/PAL em integration-validation/ registram o hash da ROM.
Este modo não testa as regras de perda de equipamento após derrota.

```sh
arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py --audio-only --output game/art/audio-vitoria-v1/integration-validation/ntsc
arch -x86_64 /usr/bin/python3 game/tools/test_results_emulator.py --audio-only --pal --output game/art/audio-vitoria-v1/integration-validation/pal
```

As capturas bench-ntsc.wav e bench-pal.wav usam a bancada com o motor de
produção atualizado; bench-validation.json registra aproximadamente 2,00 e
2,02 segundos audíveis, respectivamente, com a mesma partitura aprovada.
