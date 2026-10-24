import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const root = path.resolve('.');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
}).listen(8767);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => console.log('PAGEERROR', e.message));
page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 300)); });
await page.goto(`http://localhost:8767/proj-demo.html${process.argv[2] || ''}`);
await page.waitForFunction(() => window.__ready === true, null, { timeout: 300000 });
fs.mkdirSync('proj-out', { recursive: true });
const shots = { A_same_as_plate: [0, 0, 0, 0, 0, 0], B_step_right_0_6: [0.6, 0, 0, 0.6, 0, 0], C_step_right_1_5_push_2: [1.5, 0, -2, 1.5, 0, -2], D_move_up_0_8: [0, 0.8, 0, 0, 0.8, 0] };
for (const [name, v] of Object.entries(shots)) {
  const r = await page.evaluate((v) => window.__shot(...v), v);
  console.log('SHOT', name, Math.round(r.ms), 'ms');
  fs.writeFileSync(`proj-out/${process.argv[3] || ''}${name}.jpg`, Buffer.from(r.url.split(',')[1], 'base64'));
}
await browser.close(); server.close();
