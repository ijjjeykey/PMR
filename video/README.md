# Reel: "Referral agent: do you need one?" (EN)

30 s, 1080×1920 (Reels/Shorts/TikTok), based on the propertymanagement-review.com article
on Dubai holiday-home referral agents. Output: `referral-agent-dubai.mp4`.
Brand: blue `#1B44F2`, white, ink `#030E1A`, Anton + Montserrat (as on @dubai_property_owners).

Script: `script.json`. Scene (character, background, cards, captions): `scene.html`.

## Rebuild
```bash
npm install
pip install sherpa-onnx
# voice: offline Kokoro v0.19, speaker 10 = bm_lewis (deep British male)
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-en-v0_19.tar.bz2
tar xjf kokoro-en-v0_19.tar.bz2
python3 tts.py kokoro-en-v0_19 build/vo 10 1.08
python3 build_audio.py build/vo build          # trim, voice warmth/room, music bed, timeline.json (lip-sync)
NODE_PATH=$(npm root -g) node render.js build referral-agent-dubai.mp4
```
