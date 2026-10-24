"""Reproducible resources and native audio/player checks; binaries live in a temp dir."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    run("python3", "game/tools/build_text_font.py", "--check")
    run("python3", "game/tools/build_floor_tiles.py", "--check")
    run("python3", "game/tools/test_text.py")
    run("python3", "game/art/actor-deaths-v1/export.py", "--check")
    run("python3", "game/art/intro-monologo-v2/export_intro.py", "--check")
    run("python3", "game/art/routemap-regional-v1/export_map.py", "--check")
    run("python3", "game/art/routemap-footer-ux-v1/export_footer.py", "--check")
    run("python3", "game/art/interface-ux-v2/exportar.py", "--check")
    run("python3", "game/art/mission-portraits-v3/export.py", "--check")
    run("python3", "game/tools/build_mission_portraits.py", "--check")
    run("python3", "game/art/resultados-ux-v1/exportar.py", "--check")
    run("python3", "game/art/radio-dialogos-ux-v1/exportar.py", "--check")
    run("python3", "game/art/countdown-radio-v4/export.py", "--check")
    run("python3", "game/art/hud-resistencia-v1/integracao/exportar.py", "--check")
    run("python3", "game/tools/build_hud_labels.py", "--check")
    run("python3", "game/art/training-v2/export_scene.py", "--check")
    run("python3", "game/tools/build_operations.py", "--check")
    run("python3", "game/art/objective-sprites-v1/export.py", "--check")
    run("python3", "game/tools/pack_campaign_ground_art.py", "--check")
    run("python3", "game/art/campaign-whole-scenes-v1/validate_early.py")
    run("python3", "game/tools/test_campaign_rules.py")
    run("python3", "game/tools/test_campaign_route_ops.py")
    run("python3", "game/tools/build_campaign_routes.py", "--check")
    run("python3", "game/tools/verify_campaign_route_scenes.py")
    from campaign_corridors import active
    if active('3'):
        run("python3", "game/tools/campaign_corridors.py", "--check")
    if active('9'):
        run("python3", "game/tools/build_campaign_factory.py", "--check")
    run("python3", "game/tools/test_player_aim.py")
    run("python3", "game/tools/test_player_shots.py")
    run("python3", "game/art/bolsa-recuperacao-v1/export.py", "--check")
    run("python3", "game/tools/test_death_rules.py")
    run("python3", "game/tools/test_enemy_facing.py")
    run("python3", "game/tools/pack_actor_animation.py", "--check")
    run("python3", "game/art/cangaco-insects-sized-v3/validate_sprites.py", "--assets-only")
    run("python3", "game/tools/build_terrain_modules.py", "--check")
    run("python3", "game/tools/test_terrain_modules.py")
    run("python3", "game/tools/build_route_stages.py", "--check")
    for variant in ("original", "melancolico", "sombrio", "igreja"):
        run("python3", "game/tools/compose_music.py", "--variant", variant, "--check")
    run("python3", "game/tools/compose_music.py", "--catalog", "--check")
    run("python3", "game/tools/compose_opening.py", "--check")
    run("python3", "game/art/audio-vitoria-v1/compose.py", "--check")
    run("python3", "game/art/audio-game-over-v1/compose.py", "--check")
    compiler = shlex.split(os.environ.get("CC", "cc"))
    flags = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
             "-Igame/tests/audio", "-Igame/src/system/audio"]
    production = ["game/src/system/audio/music.c", "game/src/system/audio/audio.c"]
    with tempfile.TemporaryDirectory(prefix="plaguefall-check-") as folder:
        for name, defines in (("original", []), ("melancolico", ["-DMUSIC_MELANCHOLIC=1"]),
                              ("sombrio", ["-DMUSIC_DARK=1"])):
            binary = str(Path(folder) / name)
            run(*compiler, *flags, *defines, "game/tests/audio/music_test.c", *production, "-o", binary)
            run(binary)
        binary = str(Path(folder) / "opening")
        run(*compiler, *flags, "game/tests/audio/opening_test.c",
            "game/src/system/audio/opening.c", *production, "-o", binary)
        run(binary)
    print("All generated resources and native audio/player checks passed.")


if __name__ == "__main__":
    main()
