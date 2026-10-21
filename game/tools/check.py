"""Reproducible score and native audio checks; all binaries live in a temp dir."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    for variant in ("original", "melancolico", "sombrio", "igreja"):
        run("python3", "game/tools/compose_music.py", "--variant", variant, "--check")
    run("python3", "game/tools/compose_music.py", "--catalog", "--check")
    run("python3", "game/tools/compose_opening.py", "--check")
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
    print("All generated scores and native audio checks passed.")


if __name__ == "__main__":
    main()
