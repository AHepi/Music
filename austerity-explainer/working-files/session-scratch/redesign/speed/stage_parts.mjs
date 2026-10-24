// times the parts of one frame of a scene: the 3D drawing alone, the whole frame, and the frame grab
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { chromium } from '/home/user/Music/austerity-explainer/film-kit/paper-film/node_modules/playwright-core/index.mjs';
const KIT = '/home/user/Music/austerity-explainer/film-kit';
const [scene, time, query] = process.argv.slice(2);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const server = http.createServer((q, r) => { const f = path.join(KIT, decodeURIComponent(new URL(q.url, 'http://x').pathname));
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] ?? 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const shell = fs.readdirSync('/opt/pw-browsers').filter((n) => n.startsWith('chromium_headless_shell')).sort().reverse()[0];
const browser = await chromium.launch({ executablePath: `/opt/pw-browsers/${shell}/chrome-linux/headless_shell`, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const tab = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await tab.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/cinema-stage.html?scene=${scene}&${query ?? ''}`);
await tab.waitForFunction('window.stageReady === true || window.stageFailed', null, { timeout: 300000 });
const out = await tab.evaluate(async (t) => {
  const stage = await import('/paper-film/stage/cinema-stage.js');
  const gl = stage.renderer.getContext();
  const finish = () => { const px = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); };
  window.renderFrame(t); window.renderFrame(t + 0.033);
  const time = (f, n = 2) => { const s = performance.now(); for (let k = 0; k < n; k++) f(k); finish(); return ((performance.now() - s) / n).toFixed(0); };
  const kit = window.built.kits[0];
  const pose = window.built.pages[0].pose(t);
  const whole = time((k) => window.renderFrame(t + 0.066 + k * 0.033));
  const sceneOnly = time(() => { stage.renderer.setRenderTarget(null); stage.renderer.render(kit.scene, kit.camera); });
  const grab = time(() => stage.grabFrame());
  const THREE = await import('three');
  const plain = new THREE.MeshBasicMaterial({ color: 0x888888 });
  kit.scene.overrideMaterial = plain;
  const flat = time(() => { stage.renderer.setRenderTarget(null); stage.renderer.render(kit.scene, kit.camera); });
  kit.scene.overrideMaterial = null;
  let meshes = 0; const shaders = new Set(); kit.scene.traverse((o) => { if (o.isMesh && o.visible) { meshes++; shaders.add(o.material.type); } });
  const shadowMaps = []; kit.scene.traverse((o) => { if (o.isLight && o.castShadow) shadowMaps.push(o.type + ' ' + o.shadow.mapSize.x); });
  return `flat grey material ${flat} ms; ${meshes} visible meshes, material kinds ${[...shaders].join(', ')}; shadow-casting lights: ${shadowMaps.join(', ') || 'none'}; ` + `whole frame ${whole} ms; the 3D drawing alone (no smoothing, to screen) ${sceneOnly} ms; the frame grab (JPEG) ${grab} ms`;
}, Number(time));
console.log(`${scene} ${query ?? ''}: ${out}`);
await browser.close(); server.close();
