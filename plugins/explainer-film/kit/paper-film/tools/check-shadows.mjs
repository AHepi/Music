// What this does: draws one moment of a scene lit by the lamp alone (no soft fill light), so every
// shadow shows black. Use it to prove pieces really cast shadows: a scene can look fine while
// casting none at all (flat sheets lit from the front cast nothing unless set to cast from both
// faces, which the stage does).
//
// Use (from anywhere): node check-shadows.mjs SCENE TIME_IN_SECONDS OUTPUT.jpg

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const KIT_FOLDER = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };

function findBrowser() {
  const candidates = [process.env.PAPER_FILM_BROWSER];
  try { candidates.push(chromium.executablePath()); } catch { /* none of Playwright's own */ }
  for (const root of ['/opt/pw-browsers', path.join(process.env.HOME ?? '', '.cache/ms-playwright')]) {
    if (!fs.existsSync(root)) continue;
    for (const folder of fs.readdirSync(root).filter((name) => name.startsWith('chromium')).sort().reverse()) {
      candidates.push(path.join(root, folder, 'chrome-linux64/chrome'), path.join(root, folder, 'chrome-linux/chrome'));
    }
  }
  candidates.push('/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome');
  const found = candidates.find((candidate) => candidate && fs.existsSync(candidate));
  if (!found) throw new Error('No Chromium found. Set PAPER_FILM_BROWSER to the path of a Chromium or Chrome program.');
  return found;
}

const [scene, time, output] = process.argv.slice(2);
const server = http.createServer((request, response) => {
  const file = path.join(KIT_FOLDER, decodeURIComponent(new URL(request.url, 'http://x').pathname));
  if (!file.startsWith(KIT_FOLDER) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end(); return; }
  response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: findBrowser(), args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/paper-stage.html?scene=${scene}`);
  await page.waitForFunction('window.stageReady === true || window.stageFailed', null, { timeout: 300000 });
  const failed = await page.evaluate(() => window.stageFailed);
  if (failed) throw new Error(failed);
  const dataUrl = await page.evaluate((t) => { window.stage.setLightLevels({ ambientShare: 0.0, lampShare: 1.0 }); return window.renderFrame(t); }, Number(time));
  fs.writeFileSync(output, Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64'));
  console.log(`wrote ${output}`);
} finally {
  await browser.close();
  server.close();
}
