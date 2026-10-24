// Times each effect page at 1080 x 1920 in the film's hidden browser with software graphics.
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const root = path.resolve('.');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary', '.jpg': 'image/jpeg', '.png': 'image/png', '.wasm': 'application/wasm' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
}).listen(8766);
const list = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
fs.mkdirSync('fx-out', { recursive: true });
for (const fx of list) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('PAGEERROR', fx, e.message));
  await page.goto(`http://localhost:8766/fx-bench.html?fx=${fx}`);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); }
  catch (e) { console.log('FAILED', fx, e.message.slice(0, 120)); await page.close(); continue; }
  const res = await page.evaluate(() => window.__bench(4));
  const sorted = [...res.times].sort((a, b) => a - b); const med = (sorted[1] + sorted[2]) / 2;
  const info = await page.evaluate(() => window.__info);
  console.log(`FX ${fx.padEnd(10)} median ${Math.round(med - res.grab)} ms drawing (+${Math.round(res.grab)} ms grab)  all: ${res.times.map(Math.round).join(' ')}  tris ${info.triangles}`);
  fs.writeFileSync(`fx-out/${fx}.jpg`, Buffer.from(res.url.split(',')[1], 'base64'));
  await page.close();
}
await browser.close(); server.close();
