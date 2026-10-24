// What this does: the runner of the stage test. It serves the folder kit/ (a copy of the film kit's stage files + my .glb files and pictures) to a hidden Chromium
// (Playwright, software graphics, exactly the way the film kit's own render-paper-film.mjs does it), opens street-wet-test.html and runs the jobs named in the JSON file given
// as the first argument: [{ "call": "describe", "args": {...}, "out": "name.json" }, { "call": "still", "args": {...}, "out": "name.png" } ...]. Outputs go to the folder given second.
// Use: node run_stage_test.mjs jobs.json OUT_FOLDER
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const KIT_NODE = '/home/user/Music/austerity-explainer/film-kit/paper-film/node_modules';
const { chromium } = await import(pathToFileURL(path.join(KIT_NODE, 'playwright-core/index.mjs')).href);
const HERE = path.dirname(new URL(import.meta.url).pathname);
const KIT = path.join(HERE, 'kit');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.woff2': 'font/woff2' };
const [jobsFile, outFolder] = process.argv.slice(2);
fs.mkdirSync(outFolder, { recursive: true });

function findBrowser() {
  for (const root of ['/opt/pw-browsers']) {
    for (const folder of fs.readdirSync(root).filter((n) => n.startsWith('chromium_headless_shell')).sort().reverse()) {
      for (const sub of ['chrome-linux/headless_shell', 'chrome-headless-shell-linux64/chrome-headless-shell']) {
        const candidate = path.join(root, folder, sub);
        if (fs.existsSync(candidate)) return candidate;
      }
    }
  }
  throw new Error('no Chromium found');
}
const server = http.createServer((request, response) => {
  const relative = decodeURIComponent(new URL(request.url, 'http://x').pathname);
  const file = path.join(KIT, relative);
  if (!file.startsWith(KIT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end(); return; }
  response.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: findBrowser(), args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('console', (message) => { if (['error', 'warning'].includes(message.type())) console.log('[stage]', message.text().slice(0, 300)); });
page.on('pageerror', (error) => console.log('[stage error]', error.message));
const started = Date.now();
await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/street-wet-test.html`);
await page.waitForFunction('window.stageReady === true || window.stageFailed', null, { timeout: 300000 });
const failed = await page.evaluate(() => window.stageFailed);
if (failed) { console.log('STAGE FAILED', failed); process.exit(1); }
console.log('stage ready after', ((Date.now() - started) / 1000).toFixed(1), 's');
const timings = {};
for (const job of JSON.parse(fs.readFileSync(jobsFile, 'utf8'))) {
  const t0 = Date.now();
  try {
    const result = await page.evaluate(([call, args]) => window.test[call](args), [job.call, job.args]);
    if (typeof result === 'string' && result.startsWith('data:image/png')) fs.writeFileSync(path.join(outFolder, job.out), Buffer.from(result.split(',')[1], 'base64'));
    else fs.writeFileSync(path.join(outFolder, job.out), JSON.stringify(result, null, 1));
  } catch (error) { console.log('JOB FAILED', job.out, String(error).slice(0, 400)); }
  timings[job.out] = (Date.now() - t0) / 1000;
  console.log('done', job.out, timings[job.out], 's');
}
fs.writeFileSync(path.join(outFolder, 'stage_timings.json'), JSON.stringify(timings, null, 1));
await browser.close();
server.close();
