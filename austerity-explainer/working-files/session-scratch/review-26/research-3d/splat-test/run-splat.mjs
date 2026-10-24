// Renders a Gaussian splat with Spark in the same hidden browser and software graphics the film uses.
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const root = path.resolve('.');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm', '.spz': 'application/octet-stream', '.ply': 'application/octet-stream', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
}).listen(8765);
const [file, tag = 'test', extra = ''] = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('PAGE', m.type(), m.text().slice(0, 200)); });
page.on('pageerror', e => console.log('PAGEERROR', e.message));
await page.goto(`http://localhost:8765/splat.html?file=${encodeURIComponent(file)}${extra}`);
await page.waitForFunction(() => window.__ready === true, null, { timeout: 600000 });
console.log('INFO', JSON.stringify(await page.evaluate(() => window.__info)));
const views = [[0, 0, 0, 0, 0, -1], [0.3, 0, 0, 0.3, 0, -1], [0, 0, -0.6, 0, 0, -1.6]];
for (let i = 0; i < views.length; i++) {
  const res = await page.evaluate((v) => window.__renderAt(...v), views[i]);
  console.log('VIEW', i, 'render+grab ms', res.times.map(t => Math.round(t)).join(' '), 'grab only', Math.round(res.grab));
  fs.writeFileSync(`out-${tag}-${i}.jpg`, Buffer.from(res.url.split(',')[1], 'base64'));
}
await browser.close(); server.close();
