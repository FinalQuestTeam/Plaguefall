# Limpeza de recursos substituídos

A limpeza removeu do runtime o gerador dos nove mechs, as matrizes antigas de insetos que já não eram usadas, seis ícones substituídos pelos atuais, a trilha XGM sem consumidores e quatro referências de imagem antigas. O único desenho antigo de inseto ainda necessário ao dummy/alvo do sandbox está isolado em `training_target_data.h`.

A galeria de Dinorah utiliza somente dez frames de repouso: cinco vistas × duas poses. Os vinte frames de movimento sem consumidor saíram da ROM. As animações completas permanecem no pacote de arte para a futura integração da personagem à arena.

Fonte opaca, paletas e variantes de brilho idênticas agora compartilham recursos. Os mapas, sprites exibidos, músicas e regras atuais foram mantidos. Os cenários legados das fases7–16 e os alvos de treino continuam ativos e não foram retirados.

| Medida | Antes | Depois |
|---|---:|---:|
| Conteúdo efetivo da ROM | 1.124.596 bytes | 1.101.736 bytes |
| Arquivo final | 1.179.648 bytes | 1.179.648 bytes |
| Fonte/paletas/brilho duplicados | 7.840 bytes extras | Compartilhados |
| Frames de movimento de Dinorah sem uso | 15.360 bytes | Fora da ROM |

A redução líquida é22.860 bytes. A diferença em relação à soma dos dados removidos vem do código e do alinhamento gerados pelo compilador para selecionar os frames compactos na galeria. O tamanho final continua em1152 KiB porque o SGDK completa blocos de128 KiB; o espaço vazio aumentou de55.052 para77.912 bytes.

[Inventário removido](removed.json) · [Comparação de tamanho](validation/size.json) · [Validação consolidada](../../doc/build-validation.json).

A validação da ROM nova cobre42 partidas na campanha e28 ensaios de carga em60 FPS NTSC/50 FPS PAL, com colisões, lava/lama, câmera, HUD, brilho, pausa e saídas do objetivo. [NTSC](../phases02-06-v1/validation/ntsc/report.json) · [PAL](../phases02-06-v1/validation/pal/report.json).

A abertura e a galeria foram exercitadas em ambas as regiões, incluindo comparação dos dez frames de Dinorah na VRAM com as imagens originais. Os testes de áudio e jogador com ASan/UBSan passaram. Relatórios antigos continuam identificados por seus hashes e pertencem às revisões anteriores.

Para verificar os recursos novamente:

```sh
python3 game/tools/pack_actor_animation.py --check
python3 game/tools/pack_courtyard.py --check
python3 game/tools/install_stage_art.py --check
python3 game/tools/package_rom.py --check
```
