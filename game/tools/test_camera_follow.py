"""Run the real camera policy with ASan/UBSan at50/60Hz."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='plaguefall-camera-native-') as folder:
    binary = str(Path(folder) / 'camera')
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-Igame/tests/terrain','-Igame/src','game/tests/camera_follow_test.c',
                    'game/src/levels/camera_follow.c','-o',binary],cwd=ROOT,check=True)
    subprocess.run([binary],check=True)
