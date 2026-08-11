// Exportação 4K das lâminas de um carrossel (.slide) para PNG.
// Uso:  node tools/export-4k.cjs <arquivo.html> [larguraAlvoPx=2160] [saida=exports/<nome>]
// Requisito: Playwright  ->  npm i -D playwright && npx playwright install chromium
const path = require('path');
const fs = require('fs');

let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.error('Playwright não encontrado. Instale:  npm i -D playwright && npx playwright install chromium');
  process.exit(1);
}

(async () => {
  const file = process.argv[2];
  if (!file) { console.error('Informe o HTML do carrossel. Ex: node tools/export-4k.cjs preparacao-estetica.html'); process.exit(1); }
  const targetW = parseInt(process.argv[3] || '2160', 10);      // ~4K portrait (2160×2700 p/ 4:5)
  const base = path.basename(file).replace(/\.html?$/i, '');
  const outDir = process.argv[4] || path.join('exports', base);
  fs.mkdirSync(outDir, { recursive: true });

  const CSS_WIDTH = 560;                                          // largura do .slide no layout
  const dpr = Math.min(4, Math.max(1, Math.round((targetW / CSS_WIDTH) * 100) / 100));

  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: dpr });
  await p.goto('file://' + path.resolve(file), { waitUntil: 'networkidle' });
  await p.waitForTimeout(500);

  const slides = await p.$$('.slide');
  for (let i = 0; i < slides.length; i++) {
    const out = path.join(outDir, `slide-${String(i + 1).padStart(2, '0')}.png`);
    await slides[i].screenshot({ path: out });
    console.log('->', out);
  }
  await b.close();
  console.log(`\n${slides.length} lâminas · ~${Math.round(CSS_WIDTH * dpr)}px de largura (4K) · ${outDir}`);
})();
