// Render scene.html frame-by-frame with Playwright and encode with ffmpeg.
// Usage: node render.js <build_dir> <out.mp4> [--preview t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

(async () => {
  const [buildDir, out, flag, list] = process.argv.slice(2);
  const tl = JSON.parse(fs.readFileSync(path.join(buildDir, 'timeline.json'), 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.addInitScript(([t, c]) => { window.TIMELINE = t; window.COVER = c; }, [tl, flag === '--cover']);
  await page.goto('file://' + path.resolve(process.env.SCENE || path.join(__dirname, 'scene.html')));
  await page.evaluate(() => document.fonts.ready);
  const sfx = await page.evaluate(() => window.SFX || []);
  fs.writeFileSync(path.join(buildDir, 'sfx.json'), JSON.stringify(sfx));
  if (flag === '--sfx') return browser.close();
  if (flag === '--cover') {
    await page.evaluate(() => render(4.45));
    await page.evaluate(() => { const m = document.getElementById('man'); m.style.transform = 'translateY(180px)'; m.style.opacity = 1; });
    await page.screenshot({ path: out });
    return browser.close();
  }
  if (flag === '--preview') {
    for (const t of list.split(',').map(Number)) {
      await page.evaluate(t => render(t), t);
      await page.screenshot({ path: `${out}_${t}.png` });
    }
    return browser.close();
  }
  const n = Math.round(tl.duration * tl.fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(tl.fps), '-i', '-',
    '-i', path.join(buildDir, process.env.AUDIO || 'mix.wav'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < n; f++) {
    await page.evaluate(t => render(t), f / tl.fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`frame ${f}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('done', out);
})();
