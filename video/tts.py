"""Synthesize the voiceover per scene with an offline Kokoro voice (sherpa-onnx).

Usage: python3 tts.py <kokoro_model_dir> <out_dir> [speaker_id] [speed]
"""
import json, sys, wave
from pathlib import Path
import numpy as np
import sherpa_onnx

model_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
sid = int(sys.argv[3]) if len(sys.argv) > 3 else 10
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
        model=str(model_dir / "model.onnx"), voices=str(model_dir / "voices.bin"),
        tokens=str(model_dir / "tokens.txt"), data_dir=str(model_dir / "espeak-ng-data")),
    num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
out_dir.mkdir(parents=True, exist_ok=True)
for s in json.loads((Path(__file__).parent / "script.json").read_text()):
    a = tts.generate(s["text"], sid=sid, speed=speed)
    x = np.clip(np.array(a.samples), -1, 1)
    with wave.open(str(out_dir / f"{s['id']}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(a.sample_rate)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print(s["id"], a.sample_rate, round(len(x) / a.sample_rate, 2))
