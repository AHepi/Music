// What this does (debug only): draws one moment of a scene lit by the lamp alone, so shadows show
// black. Use: node lamp-only-still.mjs SCENE TIME OUTPUT.jpg
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const server = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(new URL(q.url, 'http://x').pathname)); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] ?? 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise((res) => server.listen(0, '127.0.0.1', res));
const [scene, time, out] = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/paper-stage.html?scene=${scene}`);
await page.waitForFunction('window.stageReady === true', null, { timeout: 180000 });
const url = await page.evaluate((t) => { window.stage.setLightLevels({ ambientShare: 0.0, lampShare: 1.0 }); return window.renderFrame(t); }, Number(time));
fs.writeFileSync(out, Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
await browser.close(); server.close();
