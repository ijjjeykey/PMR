"""Synthesize the voiceover per scene with an offline Piper voice (sherpa-onnx)."""
import json, sys, wave
from pathlib import Path
import numpy as np
import sherpa_onnx

model_dir = Path(sys.argv[1])  # e.g. vits-piper-ru_RU-dmitri-medium
out_dir = Path(sys.argv[2])
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
name = model_dir.name.replace("vits-piper-", "")
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
        model=str(model_dir / f"{name}.onnx"), tokens=str(model_dir / "tokens.txt"),
        data_dir=str(model_dir / "espeak-ng-data"), noise_scale=0.6, noise_scale_w=0.7),
    num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
out_dir.mkdir(parents=True, exist_ok=True)
scenes = json.loads((Path(__file__).parent / "script.json").read_text())
for s in scenes:
    a = tts.generate(s["text"], sid=0, speed=speed)
    x = np.clip(np.array(a.samples), -1, 1)
    with wave.open(str(out_dir / f"{s['id']}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(a.sample_rate)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print(s["id"], round(len(x) / a.sample_rate, 2))
