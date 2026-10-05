// Eksport PNG z plików SVG logo (do dokumentów Word/Canva, social media, favicon).
// Wymaga: npm i @resvg/resvg-js   Użycie: node brand/tools/export_png.mjs
import { Resvg } from '@resvg/resvg-js';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const svgDir = path.join(here, '..', 'logo', 'svg');
const pngDir = path.join(here, '..', 'logo', 'png');
const favDir = path.join(here, '..', 'favicon');
fs.mkdirSync(pngDir, { recursive: true });
fs.mkdirSync(favDir, { recursive: true });

const render = (svg, opts) => new Resvg(svg, opts).render().asPng();

// każdy wariant: wysokość 600 px (logotypy) lub 1024 px (sygnety)
for (const f of fs.readdirSync(svgDir).filter((f) => f.endsWith('.svg'))) {
  const svg = fs.readFileSync(path.join(svgDir, f), 'utf8');
  const square = f.startsWith('sygnet') || f.startsWith('ikona');
  const tall = f.startsWith('logo-pionowe');
  const png = render(svg, { fitTo: { mode: 'height', value: square ? 1024 : tall ? 1200 : 600 } });
  fs.writeFileSync(path.join(pngDir, f.replace('.svg', '.png')), png);
}

// favicony i ikony aplikacji
const icon = fs.readFileSync(path.join(svgDir, 'ikona.svg'), 'utf8');
fs.copyFileSync(path.join(svgDir, 'ikona.svg'), path.join(favDir, 'favicon.svg'));
for (const [name, size] of [['favicon-32.png', 32], ['favicon-48.png', 48], ['apple-touch-icon.png', 180], ['icon-192.png', 192], ['icon-512.png', 512]]) {
  fs.writeFileSync(path.join(favDir, name), render(icon, { fitTo: { mode: 'width', value: size } }));
}

// grafika do udostępniania (Open Graph 1200×630): logo pionowe na kremowym tle
const stacked = fs.readFileSync(path.join(svgDir, 'logo-pionowe.svg'), 'utf8');
const [, vw, vh] = stacked.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).map(Number);
const h = 470, w = (vw * h) / vh;
const inner = stacked.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
const og = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#fbf8f1"/>
<path d="M0 540 C300 490 520 520 700 548 C880 576 1040 520 1200 530 V630 H0Z" fill="#ebf1e4"/>
<svg x="${(1200 - w) / 2}" y="${(630 - h) / 2 - 10}" width="${w}" height="${h}" viewBox="0 0 ${vw} ${vh}">${inner}</svg></svg>`;
fs.writeFileSync(path.join(favDir, 'og-image.png'), render(og, { fitTo: { mode: 'original' } }));

console.log('PNG zapisane w', pngDir, 'i', favDir);
