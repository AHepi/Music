// What this does: finds out why a page films slowly. It opens one page of a chapter in the hidden
// browser, times how long one frame takes to draw, then takes away one kind of thing at a time
// (smoke and dust sprites, point lights, shadows, transparent things, big models by name) and
// times the frame again, so the slow part shows as the biggest drop. Nothing is saved; the page
// files are not changed.
//
// Use (from the kit folder): node paper-film/tools/profile_frame.mjs PAGE TIME [MODEL_NAME_PART ...]
//   e.g. node paper-film/tools/profile_frame.mjs 3 60 scene scene   (each name removes the next top-level
//   object whose name contains it; loaded models are called 'Scene', in the order the page added them)
// PROFILE_TESTS=lambert,no-normal-maps,... chooses the tests (default: sprites, points, point lights,
// shadows, transparent; the model-material tests: no-normal-maps, no-receive-shadow, lambert).
// It prints milliseconds a frame for each test, and how many draw calls and triangles the frame had.

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const KIT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const [page, time, ...names] = process.argv.slice(2);
if (!page || !time) { console.log('Use: node profile_frame.mjs PAGE TIME [MODEL_NAME_PART ...]'); process.exit(1); }

const server = http.createServer((request, response) => {
  const file = path.join(KIT, decodeURIComponent(new URL(request.url, 'http://x').pathname));
  if (!file.startsWith(KIT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end(); return; }
  response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const shell = fs.readdirSync('/opt/pw-browsers').filter((n) => n.startsWith('chromium_headless_shell')).sort().reverse()[0];
const browser = await chromium.launch({ executablePath: `/opt/pw-browsers/${shell}/chrome-linux/headless_shell`, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const tab = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
tab.on('pageerror', (e) => console.log('[page error]', e.message));
await tab.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/cinema-stage.html?scene=cinema-test-pages&pages=${page}`);
await tab.waitForFunction('window.stageReady === true || window.stageFailed', null, { timeout: 300000 });

const measure = (label) => tab.evaluate(async ({ t, label }) => {
  const { renderer } = await import('/paper-film/stage/cinema-stage.js');
  window.renderFrame(t); window.renderFrame(t + 0.033);          // warm up (shaders compile)
  const started = performance.now();
  for (let k = 0; k < 3; k++) window.renderFrame(t + 0.066 + k * 0.033);
  const ms = (performance.now() - started) / 3;
  return `${label.padEnd(34)} ${ms.toFixed(0).padStart(6)} ms a frame   (${renderer.info.render.calls} draw calls, ${renderer.info.render.triangles} triangles in the last pass)`;
}, { t: Number(time), label });

await tab.evaluate(async () => { window.__THREE = await import('three'); });
const remove = (test) => tab.evaluate((test) => {
  const scene = window.built.kits[0].scene;
  const doomed = [];
  scene.traverse((o) => {
    if (test.kind === 'sprites' && o.isSprite) doomed.push(o);
    if (test.kind === 'points' && o.isPoints) doomed.push(o);
    if (test.kind === 'pointlights' && o.isPointLight) doomed.push(o);
    if (test.kind === 'transparent' && o.isMesh && o.material && o.material.transparent) doomed.push(o);
    if (test.kind === 'name' && !doomed.length && o.parent === scene && (o.name || '').toLowerCase().includes(test.name)) doomed.push(o);   // the first match only
  });
  for (const o of doomed) o.parent.remove(o);
  // material tests: the models' realistic (Standard) materials swapped for cheaper ones
  if (test.kind === 'no-normal-maps') scene.traverse((o) => { if (o.isMesh && o.material.normalMap) { o.material.normalMap = null; o.material.needsUpdate = true; } });
  if (test.kind === 'no-receive-shadow') scene.traverse((o) => { if (o.isMesh && o.material.isMeshStandardMaterial) o.receiveShadow = false; });
  if (test.kind === 'lambert') scene.traverse((o) => {
    if (!o.isMesh || !o.material.isMeshStandardMaterial) return;
    const m = o.material;
    const lambert = new window.__THREE.MeshLambertMaterial({
      map: m.map, color: m.color, emissive: m.emissive, emissiveMap: m.emissiveMap, emissiveIntensity: m.emissiveIntensity,
      aoMap: m.aoMap, aoMapIntensity: m.aoMapIntensity, normalMap: m.normalMap, transparent: m.transparent, opacity: m.opacity, side: m.side,
    });
    lambert.name = m.name; o.material = lambert;
  });
  if (test.kind === 'shadows') scene.traverse((o) => { if (o.isLight && o.castShadow) o.castShadow = false; });
  return doomed.length;
}, test);

// what the scene holds at the top level
console.log(await tab.evaluate(() => {
  const scene = window.built.kits[0].scene, counts = {};
  scene.traverse((o) => { const k = o.isSprite ? 'sprite' : o.isPoints ? 'points' : o.isLight ? o.type : o.isMesh ? 'mesh' : null; if (k) counts[k] = (counts[k] ?? 0) + 1; });
  return 'scene holds: ' + JSON.stringify(counts) + '; top-level names: ' + scene.children.map((o) => o.name).filter(Boolean).slice(0, 20).join(', ');
}));
console.log(await measure('everything'));
const ALL_TESTS = [['without smoke/dust sprites', { kind: 'sprites' }], ['without motes (points)', { kind: 'points' }],
  ['without point lights', { kind: 'pointlights' }], ['without shadows', { kind: 'shadows' }], ['without transparent meshes', { kind: 'transparent' }],
  ['models: no normal maps', { kind: 'no-normal-maps' }], ['models: catch no shadows', { kind: 'no-receive-shadow' }], ['models: matte (Lambert) materials', { kind: 'lambert' }]];
const chosen = (process.env.PROFILE_TESTS ?? 'sprites,points,pointlights,shadows,transparent').split(',');
for (const [label, test] of ALL_TESTS.filter(([, t]) => chosen.includes(t.kind))) {
  const n = await remove(test);
  console.log(await measure(`${label} (${n} removed)`));
}
for (const name of names) {
  const n = await remove({ kind: 'name', name: name.toLowerCase() });
  console.log(await measure(`without "${name}" (${n} removed)`));
}
await browser.close(); server.close();
