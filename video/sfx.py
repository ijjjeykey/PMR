"""Mix synthesized sound effects (whoosh/pop/tick/alert) from sfx.json onto mix.wav -> mix_sfx.wav."""
import json, sys, wave
from pathlib import Path
import numpy as np

b = Path(sys.argv[1])
with wave.open(str(b / "mix.wav")) as w:
    sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
rng = np.random.default_rng(5)

def whoosh():
    n = int(0.32 * sr); t = np.arange(n) / sr; noise = rng.standard_normal(n)
    out = np.zeros(n); s = 0.0
    for i in range(n):  # sweeping one-pole low-pass
        a = np.exp(-2 * np.pi * (400 + 5000 * (i / n)) / sr); s = (1 - a) * noise[i] + a * s; out[i] = s
    return 0.5 * out * np.sin(np.pi * t / t[-1]) ** 2
def pop():
    n = int(0.09 * sr); t = np.arange(n) / sr
    return 0.35 * np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 45)
def tick():
    n = int(0.05 * sr); t = np.arange(n) / sr
    return 0.3 * (np.sin(2 * np.pi * 2200 * t) + 0.5 * np.sin(2 * np.pi * 3300 * t)) * np.exp(-t * 90)
def alert():
    n = int(0.22 * sr); t = np.arange(n) / sr
    f = np.where(t < 0.11, 880, 660)
    return 0.22 * np.sign(np.sin(2 * np.pi * f * t)) * np.exp(-((t % 0.11) * 18)) * 0.6
FX = {"whoosh": whoosh(), "pop": pop(), "tick": tick(), "alert": alert()}
fx = np.zeros_like(x)
for kind, at in json.loads((b / "sfx.json").read_text()):
    s = FX[kind]; i = int(at * sr); j = min(len(fx), i + len(s))
    if 0 <= i < len(fx): fx[i:j] += s[:j - i]
y = x + 0.55 * fx
y = y / max(1, np.abs(y).max() / 0.95)
with wave.open(str(b / "mix_sfx.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())
print("sfx events:", len(json.loads((b / 'sfx.json').read_text())))
