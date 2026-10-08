# Reel: «Реферальный агент в Дубае — нужен ли он?»

30 с, 1080×1920 (Reels/Shorts/TikTok), по статье propertymanagement-review.com
о реферальных агентах holiday homes в Дубае. Готовый файл: `referral-agent-dubai.mp4`.

Текст и субтитры: `script.json`. Сцена (персонаж, фон, инфографика): `scene.html`.

## Пересборка
```bash
npm install
# голос: офлайн Piper (ru_RU-dmitri-medium) через sherpa-onnx
pip install sherpa-onnx
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-ru_RU-dmitri-medium.tar.bz2
tar xjf vits-piper-ru_RU-dmitri-medium.tar.bz2
python3 tts.py vits-piper-ru_RU-dmitri-medium build/vo 1.08
python3 build_audio.py build/vo build          # микс + music bed + timeline.json (липсинк)
NODE_PATH=$(npm root -g) node render.js build referral-agent-dubai.mp4
```
