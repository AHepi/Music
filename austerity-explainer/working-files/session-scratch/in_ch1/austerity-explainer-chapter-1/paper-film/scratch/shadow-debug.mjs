// Debug: draw one moment with the lamp only (no fill light), and report the shadow settings.
import { chromium } from 'playwright-core';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = '/home/claude/austerity-explainer';
const server = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(new URL(q.url, 'http://x').pathname)); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise((res) => server.listen(0, '127.0.0.1', res));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('console', (m) => console.log('[page]', m.text()));
await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/paper-stage.html?scene=chapter-1-page-3`);
await page.waitForFunction('window.stageReady === true', null, { timeout: 120000 });
const info = await page.evaluate(() => {
  const s = window.stage;
  s.setLightLevels({ ambientShare: 0.0, lampShare: 1.0 });
  const r = s.renderer;
  const lamp = s.scene.children.find((c) => c.isDirectionalLight);
  return { enabled: r.shadowMap.enabled, type: r.shadowMap.type, lampPos: lamp.position.toArray(), castShadow: lamp.castShadow,
    casters: (() => { let n = 0; s.scene.traverse((o) => { if (o.isMesh && o.castShadow) n++; }); return n; })(),
    maxTex: r.capabilities.maxTextureSize, floatFragTex: r.extensions.has('EXT_color_buffer_float'), halfFloatLinear: r.extensions.has('OES_texture_half_float_linear') };
});
console.log(info);
const url = await page.evaluate(() => window.renderFrame(57.8));
fs.writeFileSync(process.argv[2], Buffer.from(url.split(',')[1], 'base64'));
const mapInfo = await page.evaluate(() => { const lamp = window.stage.scene.children.find((c) => c.isDirectionalLight); return { map: !!lamp.shadow.map, size: lamp.shadow.map && [lamp.shadow.map.width, lamp.shadow.map.height] }; });
console.log(mapInfo);
await browser.close(); server.close();
