# Reel: AC, plumbing & electrical maintenance in Dubai (45 s)

Based on the propertymanagement-review.com article "AC, Plumbing and Electrical Maintenance in Dubai".
Output: `ac-maintenance-dubai.mp4` (1080×1920). Script: `script.json`. Scene: `scene.html`.

Editing style (from the reference reel): a new scene every 3–5 s with a colour change
(ink / brand blue / red / white), blur-cut transitions, a new pose + emotion per scene
(hands-on-cheeks shock, stop palm, pointing, holding the filter, wink + finger up, thinking,
arms crossed, open hands, thumbs up), word-by-word blur-in text, cue-timed pop-ups and SFX.

## Rebuild (from `video/`)
```bash
REEL=ac-maintenance python3 tts.py kokoro-en-v0_19 build2/vo 10 1.08
REEL=ac-maintenance TOTAL=45 GAPS='{"leak":0.3,"stop":0.35,"causes":0.3,"filter":0.3,"thermo":0.3,"hidden":0.3,"tank":0.3,"trip":0.3,"amc":0.35}' \
  python3 build_audio.py build2/vo build2
export SCENE=ac-maintenance/scene.html NODE_PATH=$(npm root -g)
node render.js build2 x --sfx && python3 sfx.py build2
AUDIO=mix_sfx.wav node render.js build2 ac-maintenance/ac-maintenance-dubai.mp4
```
