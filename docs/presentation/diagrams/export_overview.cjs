// Re-export the durable SVG using an operator-provided Playwright installation.
// NODE_PATH may point to the existing browser-test environment; no new dependency.
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport: {width: 1920, height: 1080}, deviceScaleFactor: 1});
    await page.setContent(await fs.readFile(path.join(__dirname, 'system-overview.svg'), 'utf8'));
    await page.evaluate(() => { document.body.style.margin = '0'; });
    await page.locator('svg').screenshot({path: path.join(__dirname, 'system-overview.png')});
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
