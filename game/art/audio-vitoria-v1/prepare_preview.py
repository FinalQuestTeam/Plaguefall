"""Trim boot silence/transient from real ROM captures and set audition gain."""
from pathlib import Path
from array import array
import hashlib
import json
import math
import wave

ROOT = Path(__file__).resolve().parent
report = {}
for region in ("ntsc", "pal"):
    with wave.open(str(ROOT / f"capture-{region}.wav"), "rb") as source:
        rate, channels = source.getframerate(), source.getnchannels()
        data = array("h", source.readframes(source.getnframes()))
    # Genesis Plus GX emits a power-on transient before the program starts.
    # The ROM remains silent for over 200 ms between that transient and the cue.
    frames = len(data) // channels
    assert max(abs(v) for v in data[round(.15*rate)*channels:round(.3*rate)*channels]) < 10
    active = [i for i in range(round(.3 * rate), frames)
              if max(abs(data[i*channels+c]) for c in range(channels)) > 100]
    start, end = active[0], active[-1]
    audible = (end - start) / rate
    assert 1.9 < audible < 2.15, (region, audible)
    first = max(0, start - round(.025 * rate))
    last = min(frames, start + round(2.18 * rate))
    cropped = data[first*channels:last*channels]
    gain = 10  # +20 dB constant gain; no effects, compression or EQ.
    assert max(abs(v) for v in cropped) * gain < 32767
    output = array("h", (v * gain for v in cropped))
    if region == "ntsc":
        with wave.open(str(ROOT / "mais-um-amanhecer.wav"), "wb") as target:
            target.setnchannels(channels)
            target.setsampwidth(2)
            target.setframerate(rate)
            target.writeframes(output.tobytes())
    report[region] = dict(sample_rate=rate, first_sound=start/rate, last_sound=end/rate,
        audible_seconds=audible, preview_seconds=len(output)/channels/rate,
        preview_peak=max(abs(v) for v in output), clipped_samples=0)
assert abs(report["ntsc"]["audible_seconds"] - report["pal"]["audible_seconds"]) < .04
report["preview_gain_db"] = 20
report["rom_sha256"] = hashlib.sha256((ROOT / "bench/out/release/rom.bin").read_bytes()).hexdigest()
(ROOT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
