// Hybrid deck, step 1: for each slide page, record every text block (box, font, runs) and
// render a background PNG with the same page but all text made transparent.
// Usage: node hybrid.cjs   (writes hybrid/bg-NN.png and hybrid/text.json)
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const HERE = __dirname, SLIDES = path.join(HERE, 'slides'), OUT = path.join(HERE, 'hybrid');
fs.mkdirSync(OUT, {recursive: true});

function extract() {
  const INLINE = new Set(['B', 'STRONG', 'I', 'EM', 'SPAN', 'BR', 'A', 'SMALL', 'SUB', 'SUP']);
  const blocks = [];
  const isTextBlock = el => {
    if (!el.textContent.trim()) return false;
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    for (const child of el.children) {
      if (!INLINE.has(child.tagName)) return false;
      const d = getComputedStyle(child).display;
      if (d !== 'inline' && child.tagName !== 'BR') return false;
    }
    return true;
  };
  const walk = el => {
    if (['SCRIPT', 'STYLE', 'IMG', 'SVG'].includes(el.tagName)) return;
    if (isTextBlock(el)) {
      const parent = el.parentElement;
      if (parent && parent !== document.body && isTextBlock(parent)) return; // the parent will take it
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      const pad = k => parseFloat(style[k]) || 0;
      const box = {
        x: rect.left + pad('paddingLeft') + pad('borderLeftWidth'),
        y: rect.top + pad('paddingTop') + pad('borderTopWidth'),
        w: rect.width - pad('paddingLeft') - pad('paddingRight') - pad('borderLeftWidth') - pad('borderRightWidth'),
        h: rect.height - pad('paddingTop') - pad('paddingBottom') - pad('borderTopWidth') - pad('borderBottomWidth'),
      };
      const runs = [];
      const upper = style.textTransform === 'uppercase';
      const visit = node => {
        if (node.nodeType === 3) {
          let text = node.textContent.replace(/\s+/g, ' ');
          if (!text) return;
          const s = getComputedStyle(node.parentElement);
          if (upper || s.textTransform === 'uppercase') text = text.toUpperCase();
          runs.push({text, weight: parseInt(s.fontWeight, 10), color: s.color, size: parseFloat(s.fontSize),
                     spacing: s.letterSpacing === 'normal' ? 0 : parseFloat(s.letterSpacing)});
        } else if (node.tagName === 'BR') runs.push({br: true});
        else for (const child of node.childNodes) visit(child);
      };
      for (const child of el.childNodes) visit(child);
      if (runs.length) {
        // Trim leading/trailing spaces of the block.
        const first = runs.find(r => !r.br), last = [...runs].reverse().find(r => !r.br);
        if (first) first.text = first.text.replace(/^\s+/, '');
        if (last) last.text = last.text.replace(/\s+$/, '');
        let lineHeight = parseFloat(style.lineHeight);
        if (Number.isNaN(lineHeight)) lineHeight = parseFloat(style.fontSize) * 1.2;
        blocks.push({...box, align: style.textAlign, lineHeight, size: parseFloat(style.fontSize), runs,
                     tag: el.tagName, cls: el.className});
      }
      return;
    }
    // Text sitting directly beside non-inline children (e.g. the brand name next to the logo).
    const style = getComputedStyle(el);
    for (const node of el.childNodes) {
      if (node.nodeType !== 3 || !node.textContent.trim()) continue;
      const range = document.createRange(); range.selectNodeContents(node);
      const r = range.getBoundingClientRect();
      let text = node.textContent.replace(/\s+/g, ' ').trim();
      if (style.textTransform === 'uppercase') text = text.toUpperCase();
      let lineHeight = parseFloat(style.lineHeight); if (Number.isNaN(lineHeight)) lineHeight = parseFloat(style.fontSize) * 1.2;
      blocks.push({x: r.left, y: r.top, w: r.width, h: r.height, align: 'left', lineHeight, size: parseFloat(style.fontSize),
                   runs: [{text, weight: parseInt(style.fontWeight, 10), color: style.color, size: parseFloat(style.fontSize),
                           spacing: style.letterSpacing === 'normal' ? 0 : parseFloat(style.letterSpacing)}], tag: el.tagName, cls: el.className});
    }
    for (const child of el.children) walk(child);
  };
  walk(document.body);
  return blocks;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
  const files = fs.readdirSync(SLIDES).filter(f => f.endsWith('.html')).sort();
  const all = [];
  for (const [i, file] of files.entries()) {
    await page.goto('file://' + path.join(SLIDES, file));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    const blocks = await page.evaluate(extract);
    await page.addStyleTag({content: '*{color:transparent !important;text-shadow:none !important;-webkit-text-fill-color:transparent !important}'});
    await page.waitForTimeout(150);
    const n = String(i + 1).padStart(2, '0');
    await page.screenshot({path: path.join(OUT, `bg-${n}.png`)});
    all.push({slide: i + 1, file, blocks});
    console.log(file, blocks.length, 'text blocks');
  }
  fs.writeFileSync(path.join(OUT, 'text.json'), JSON.stringify(all, null, 1));
  await browser.close();
})();
