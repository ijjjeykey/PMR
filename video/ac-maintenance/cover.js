// Render the Instagram cover for the AC reel: node ac-maintenance/cover.js <build_dir> <out.png>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [buildDir, out] = process.argv.slice(2);
  const tl = JSON.parse(fs.readFileSync(path.join(buildDir, 'timeline.json'), 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.addInitScript(t => { window.TIMELINE = t; }, tl);
  await page.goto('file://' + path.join(__dirname, 'scene.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => {
    render(2.3); // leak scene: shocked pose under the dripping AC
    const $ = id => document.getElementById(id);
    $('bg').style.background = 'radial-gradient(ellipse at 50% 40%, #3a62ff, #1b44f2 55%, #1233c4)';
    $('sub').style.display = 'none'; $('handle').style.display = 'none';
    $('world').style.filter = 'none'; $('world').style.transform = 'none';
    const h = $('head1'); h.style.top = '250px'; h.style.color = '#fff';
    h.innerHTML = `<div style="display:inline-block;padding:10px 26px 6px;background:#fff;color:#030e1a;font-size:40px;letter-spacing:2px;transform:skewX(-10deg);box-shadow:8px 8px 0 #030e1a">DUBAI PROPERTY OWNERS</div>
      <div style="font-size:170px;line-height:.95;margin-top:22px;text-shadow:0 10px 0 rgba(3,14,26,.35)">AC LEAKING?</div>`;
    document.querySelectorAll('#head1 span').forEach(e => e.remove());
    $('p-leak').querySelector('svg').style.transform = 'translateY(70px)';
    $('warn').setAttribute('transform', 'translate(860 560) scale(1)');
    $('man').style.transform = 'translate(0px, 110px) scale(1.05)';
    const plate = document.createElement('div');
    plate.style.cssText = 'position:absolute;left:0;right:0;top:1440px;text-align:center;z-index:9';
    plate.innerHTML = `<div style="display:inline-block;padding:18px 40px 12px;background:#030e1a;color:#fff;font-family:A;font-size:80px;text-transform:uppercase;transform:skewX(-8deg);box-shadow:12px 12px 0 #fff">Don't just <span style="color:#7d97ff">wipe it</span></div>
      <div style="margin-top:34px;font-weight:800;font-size:44px;color:#fff;text-shadow:0 4px 16px rgba(3,14,26,.8)">AC · plumbing · electrics</div>`;
    document.getElementById('stage').appendChild(plate);
  });
  await page.screenshot({ path: out });
  await browser.close();
})();
