// Render each slides/*.html to png/slide-NN.png at 1920x1080.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const dir = __dirname;
  const out = path.join(dir, 'png');
  fs.mkdirSync(out, {recursive: true});
  const files = fs.readdirSync(path.join(dir, 'slides')).filter(f => f.endsWith('.html')).sort();
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
  for (const f of files) {
    await page.goto('file://' + path.join(dir, 'slides', f), {waitUntil: 'load'});
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.screenshot({path: path.join(out, `slide-${f.slice(0, 2)}.png`)});
  }
  console.log(files.length + ' rendered');
  await browser.close();
})();
