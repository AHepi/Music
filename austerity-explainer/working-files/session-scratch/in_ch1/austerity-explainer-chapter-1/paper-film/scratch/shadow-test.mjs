import { chromium } from 'playwright-core'; import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = '/home/claude/austerity-explainer';
const server = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(new URL(q.url, 'http://x').pathname)); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : 'text/html' }); fs.createReadStream(f).pipe(r); });
await new Promise((res) => server.listen(0, '127.0.0.1', res));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const mode of ['plain', 'wallcasts']) {
  const page = await browser.newPage(); page.on('console', (m) => console.log('[page]', m.text()));
  await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/scratch/shadow-test.html?mode=${mode}`);
  await page.waitForFunction('window.out', null, { timeout: 60000 });
  const url = await page.evaluate(() => window.out);
  fs.writeFileSync(`/tmp/claude-0/-home-claude/b6432673-c449-59ed-866a-2e8e839d8cf1/scratchpad/stills-pcf/shadow-test-${mode}.png`, Buffer.from(url.split(',')[1], 'base64'));
}
await browser.close(); server.close();
