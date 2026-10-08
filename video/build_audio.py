"""Assemble voiceover + synthesized music bed; write timeline.json for the renderer."""
import json, sys, wave
from pathlib import Path
import numpy as np

here = Path(__file__).parent
vo_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
SR, FPS, TOTAL, LEAD, GAP = 22050, 30, 30.0, 0.3, 0.3
scenes = json.loads((here / "script.json").read_text())

def read(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == SR
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767

voice = np.zeros(int(TOTAL * SR), np.float32)
t, timeline = LEAD, []
for s in scenes:
    x = read(vo_dir / f"{s['id']}.wav")
    i = int(t * SR); voice[i:i + len(x)] += x
    timeline.append({**s, "start": round(t, 3), "end": round(t + len(x) / SR, 3)})
    t += len(x) / SR + GAP
assert t - GAP < TOTAL - 0.5, f"voiceover too long: {t:.2f}s"

# Music bed: soft plucked arpeggio in D Hijaz over a warm pad, with a simple delay.
n = len(voice); tt = np.arange(n) / SR
def note(m): return 440 * 2 ** ((m - 69) / 12)
music = np.zeros(n, np.float32)
chords = [[50, 54, 57], [48, 51, 55], [46, 50, 53], [50, 54, 57]]  # D, Cm, Bb, D
bar = 2.4
for k in range(int(TOTAL / bar) + 1):
    ch = chords[k % 4]; t0 = k * bar
    for m in ch:  # pad
        f = note(m)
        env = np.clip((tt - t0) / 0.6, 0, 1) * np.clip((t0 + bar + 0.6 - tt) / 0.6, 0, 1)
        music += 0.035 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.003 * f * tt))
    for j, m in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12]):
        ts = t0 + j * bar / 6; i = int(ts * SR); L = int(1.2 * SR)
        seg = tt[:L]; f = note(m)
        pl = np.exp(-seg * 4) * (np.sin(2 * np.pi * f * seg) + 0.4 * np.sin(4 * np.pi * f * seg) * np.exp(-seg * 8))
        music[i:i + L] += 0.05 * pl[:max(0, min(L, n - i))]
d = int(0.3 * SR); echo = np.zeros_like(music); echo[d:] = music[:-d] * 0.35; music += echo
# Kick-ish pulse for energy.
for b in np.arange(0, TOTAL, bar / 2):
    i = int(b * SR); L = int(0.25 * SR); seg = tt[:L]
    music[i:i + L] += (0.08 * np.exp(-seg * 18) * np.sin(2 * np.pi * (55 + 60 * np.exp(-seg * 30)) * seg))[:max(0, n - i)]
# Duck under the voice, fade in/out.
venv = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
duck = 1 - 0.55 * np.clip(venv / 0.05, 0, 1)
fade = np.clip(tt / 0.8, 0, 1) * np.clip((TOTAL - tt) / 1.5, 0, 1)
mix = voice * 1.0 + music * duck * fade * 0.9
mix = mix / max(1e-6, np.abs(mix).max()) * 0.92
out_dir.mkdir(parents=True, exist_ok=True)
with wave.open(str(out_dir / "mix.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

# Per-frame mouth openness from the voice envelope (lip-sync).
hop = SR // FPS
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(int(TOTAL * FPS))])
mouth = np.clip(rms / np.percentile(rms[rms > 0.01], 90), 0, 1) if (rms > 0.01).any() else rms
mouth = np.convolve(mouth, [0.25, 0.5, 0.25], "same")
(out_dir / "timeline.json").write_text(json.dumps(
    {"fps": FPS, "duration": TOTAL, "scenes": timeline, "mouth": [round(float(v), 3) for v in mouth]},
    ensure_ascii=False))
print("voice ends at", round(t - GAP, 2), "s")
