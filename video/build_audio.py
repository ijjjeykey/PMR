"""Assemble voiceover + synthesized music bed; write timeline.json for the renderer.

Usage: python3 build_audio.py <voice_dir> <out_dir>
"""
import json, sys, wave
from pathlib import Path
import numpy as np

here = Path(__file__).parent
vo_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
FPS, TOTAL, LEAD = 30, 30.0, 0.35
GAPS = {"hook": 0.4, "who": 0.32, "paid": 0.32, "fee": 0.3, "direct": 0.38}  # breath after each line
import os
scenes = json.loads((Path(os.environ.get("REEL", here)) / "script.json").read_text())
TOTAL = float(os.environ.get("TOTAL", TOTAL))
GAPS = json.loads(os.environ["GAPS"]) if "GAPS" in os.environ else GAPS


def read(p):
    with wave.open(str(p)) as w:
        return w.getframerate(), np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767


def trim(x, sr, thr=0.012, pad=0.04):
    idx = np.where(np.abs(x) > thr)[0]
    a, b = max(0, idx[0] - int(pad * sr)), min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def onepole_lp(x, sr, fc):
    a = np.exp(-2 * np.pi * fc / sr); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s; y[i] = s
    return y


def warm(x, sr):
    """Gentle low-mid warmth, soft de-harsh, light compression and a small room: less 'dry TTS'."""
    low = onepole_lp(x, sr, 250)
    x = x + 0.35 * low                       # low shelf ~ +2.5 dB
    x = 0.85 * x + 0.15 * onepole_lp(x, sr, 6000)  # tame top end a bit
    env = np.convolve(np.abs(x), np.ones(int(0.01 * sr)) / int(0.01 * sr), "same")
    gain = np.where(env > 0.25, (0.25 + (env - 0.25) / 3) / np.maximum(env, 1e-6), 1.0)
    x = x * gain
    rng = np.random.default_rng(3); L = int(0.18 * sr)
    ir = rng.standard_normal(L) * np.exp(-np.arange(L) / (0.045 * sr)); ir /= np.abs(ir).sum()
    room = np.convolve(x, ir)[:len(x)]
    return x + 0.6 * room / max(1e-6, np.abs(room).max()) * np.abs(x).max() * 0.12


sr = read(vo_dir / f"{scenes[0]['id']}.wav")[0]
voice = np.zeros(int(TOTAL * sr), np.float32)
t, timeline = LEAD, []
for s in scenes:
    _, x = read(vo_dir / f"{s['id']}.wav")
    x = warm(trim(x, sr), sr)
    i = int(t * sr); voice[i:i + len(x)] += x
    timeline.append({**s, "start": round(t, 3), "end": round(t + len(x) / sr, 3)})
    t += len(x) / sr + GAPS.get(s["id"], 0)
voice_end = timeline[-1]["end"]
assert voice_end < TOTAL - 0.8, f"voiceover too long: {voice_end:.2f}s"

# Music bed: modern soft pluck progression (Am-F-C-G) over a pad, with delay and a light pulse.
n = len(voice); tt = np.arange(n) / sr
def note(m): return 440 * 2 ** ((m - 69) / 12)
music = np.zeros(n, np.float32)
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
bar = 2.0
for k in range(int(TOTAL / bar) + 1):
    ch = chords[k % 4]; t0 = k * bar
    for m in ch:
        f = note(m - 12)
        env = np.clip((tt - t0) / 0.5, 0, 1) * np.clip((t0 + bar + 0.5 - tt) / 0.5, 0, 1)
        music += 0.03 * env * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2.004 * f * tt))
    for j, m in enumerate([ch[0] + 12, ch[2], ch[1] + 12, ch[2] + 12]):
        ts = t0 + j * bar / 4; i = int(ts * sr); L = int(0.9 * sr)
        seg = tt[:L]; f = note(m)
        pl = np.exp(-seg * 5) * (np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(4 * np.pi * f * seg) * np.exp(-seg * 9))
        music[i:i + L] += 0.04 * pl[:max(0, min(L, n - i))]
d = int(0.375 * sr); echo = np.zeros_like(music); echo[d:] = music[:-d] * 0.3; music += echo
for b in np.arange(0, TOTAL, bar / 2):
    i = int(b * sr); L = int(0.25 * sr); seg = tt[:L]
    music[i:i + L] += (0.07 * np.exp(-seg * 18) * np.sin(2 * np.pi * (50 + 60 * np.exp(-seg * 30)) * seg))[:max(0, n - i)]
venv = np.convolve(np.abs(voice), np.ones(int(0.25 * sr)) / int(0.25 * sr), "same")
duck = 1 - 0.6 * np.clip(venv / 0.05, 0, 1)
fade = np.clip(tt / 0.8, 0, 1) * np.clip((TOTAL - tt) / 1.5, 0, 1)
mix = voice + music * duck * fade * 0.85
mix = mix / max(1e-6, np.abs(mix).max()) * 0.92
out_dir.mkdir(parents=True, exist_ok=True)
with wave.open(str(out_dir / "mix.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

# Per-frame mouth openness from the voice envelope (lip-sync).
hop = sr // FPS
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(int(TOTAL * FPS))])
mouth = np.clip(rms / np.percentile(rms[rms > 0.01], 90), 0, 1)
mouth = np.convolve(mouth, [0.25, 0.5, 0.25], "same")
(out_dir / "timeline.json").write_text(json.dumps(
    {"fps": FPS, "duration": TOTAL, "scenes": timeline, "mouth": [round(float(v), 3) for v in mouth]},
    ensure_ascii=False))
print("voice ends at", round(voice_end, 2), "s")
