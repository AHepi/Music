// What this does: draws one still picture of a paper scene as a PNG (no video). It opens the paper
// stage in a hidden browser with the named scene, draws the moment asked for, and saves the picture
// exactly as drawn (scenes may draw at twice the size for smooth edges; shrink it afterwards).
//
// If the scene can draw a distance picture, it is saved too (OUTPUT-distance.png and .json), for the
// finishing tool's background blur.
//
// Use: node paper-film/tools/draw-one-page-still.mjs SCENE OUTPUT.png [SECONDS]

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const PROJECT_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const BROWSER = '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };

function serveProject() {
  const server = http.createServer((request, response) => {
    const relative = decodeURIComponent(new URL(request.url, 'http://x').pathname);
    const file = path.join(PROJECT_ROOT, relative);
    if (!file.startsWith(PROJECT_ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    fs.createReadStream(file).pipe(response);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

const [sceneName, output, seconds = '0'] = process.argv.slice(2);
const server = await serveProject();
const browser = await chromium.launch({ executablePath: BROWSER, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', (message) => { if (message.type() === 'error' || message.type() === 'warning') console.log('[stage]', message.text()); });
  page.on('pageerror', (error) => console.log('[stage error]', error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/paper-stage.html?scene=${sceneName}`);
  await page.waitForFunction('window.stageReady === true', null, { timeout: 180000 });
  const started = Date.now();
  const dataUrl = await page.evaluate((t) => { window.renderFrame(t); return window.stage.renderer.domElement.toDataURL('image/png'); }, Number(seconds));
  fs.writeFileSync(output, Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64'));
  console.log(`${output} (${Date.now() - started} ms)`);
  // scenes that can also draw a distance picture (for background blur) get it saved beside the still
  const distance = await page.evaluate(() => (window.drawDistancePicture ? window.drawDistancePicture() : null));
  if (distance) {
    const distanceFile = output.replace(/\.png$/, '-distance.png');
    fs.writeFileSync(distanceFile, Buffer.from(distance.picture.slice(distance.picture.indexOf(',') + 1), 'base64'));
    fs.writeFileSync(output.replace(/\.png$/, '-distance.json'), JSON.stringify({ near: distance.near, far: distance.far }));
    console.log(`${distanceFile}`);
  }
} finally {
  await browser.close();
  server.close();
}
