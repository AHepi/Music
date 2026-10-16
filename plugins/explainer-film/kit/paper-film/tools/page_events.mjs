// What this does: runs a cinema page or chapter in "events mode" and writes down, 30 times a second, everything it
// does, without filming it: every word lookup (kit.at / kit.end, with every time that word is said on the page),
// every camera shot and slide, every flat graphic drawn over the picture (words, labels, cards, rings, arrows) with
// its box in pixels and how visible it is, the held-shot key (the "still key"), the live effects (things marked
// moving: smoke, flames, flicker) and the page joins. The result is one JSON file that
// calculators/plan_page_timing.py (pauses, reading times, cuts, margins, still lists, planned cuts) and
// tools/check_page_layout.mjs (pops, overlaps, held shots, effects) read. Nothing is drawn by the graphics card, so it
// is fast (a minute or two for a few pages) and light; building the pages still loads their sets.
//
// How it works: the stage page is opened with window.pageEvents switched on before anything loads. graphics.js and
// cinema-kit.js (plugin kit) note what they draw and look up only when it is on; normal filming never switches it on,
// so frames are drawn exactly as before. This tool then asks each showing page for its pose and its draw2D at every
// frame, the same way cinema-chapter.js does when filming, and keeps the notes.
//
// Use (from anywhere; SCENE is a file name in paper-film/scenes without .js):
//   node page_events.mjs SCENE OUT.json                       the whole scene, every frame
//   node page_events.mjs SCENE OUT.json --pages 3,4,5         only while pages 3, 4 and 5 show (chapter page numbers)
//   node page_events.mjs SCENE OUT.json --from 47 --to 124    only these chapter seconds
//   --step N           every Nth frame (default 1: all 30 a second)
//   --order-check N    also draw every Nth sampled frame again in reverse order and list any moment that comes out
//                      different (a page whose picture depends on what was drawn before it: lesson 29); 0 = off
//                      (default 15)
//   --query a=b&c=d    settings added to the stage's address (as PAPER_FILM_QUERY in render-paper-film.mjs)
//   --kit DIR          serve this kit folder (default: the kit this tool is in)
//   --serve /URL/PATH=DIR   also serve DIR at that address (repeatable), e.g. a film's assets or node_modules kept
//                      elsewhere: --serve /assets=../film/assets --serve /paper-film/node_modules=../film/paper-film/node_modules
//   --render-stills DIR T1 T2 ...   instead of sampling, draw full frames at these times WITH the notes switched on
//                      and save them as JPEGs (to prove the notes change nothing: compare with render-paper-film.mjs
//                      --stills, which draws with them off)
//   --help             this note
// The browser is found by find-browser.mjs (PAPER_FILM_BROWSER, Playwright's Chromium, the usual places).
// playwright-core comes from the kit's node_modules; PAPER_FILM_PLAYWRIGHT can name another copy (its index.mjs).
// Output (JSON): scene, fps, frame size, appear_delays (graphics.js APPEAR_DELAYS), pages (number, words, first and
// last word, join, camera plans), lookups, frames (per frame and page: shot, the page's own still value (the held-shot
// key is it plus the camera), camera place and lens, how many live things show and a fingerprint of which, join), items (one per drawn thing:
// its kind, words, times, the runs of frames it is drawn in, and a track of [frame, opacity, box, words' opacity, how
// far drawn, counter text] kept where it changes), effects (per page: each live thing and the runs of frames it shows),
// order_differences. Frame numbers count from frame_zero_seconds, 30 a second; times are chapter seconds.

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
// find-browser.mjs needs playwright-core, so it is loaded only when the pages run (--help works without node_modules)

const HELP = fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').filter((line) => line.startsWith('//')).map((line) => line.slice(3)).join('\n');
const FRAMES_PER_SECOND = 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2' };

function readArguments(argv) {
  const options = { step: 1, orderCheck: 15, query: '', kit: path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..'), serve: [], pages: null,
    from: null, to: null, renderStills: null, stillTimes: [] };
  const plain = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => { if (i + 1 >= argv.length) throw new Error(`${a} needs a value`); return argv[++i]; };
    if (a === '--help' || a === '-h') options.help = true;
    else if (a === '--pages') options.pages = next().split(',').map(Number);
    else if (a === '--from') options.from = Number(next());
    else if (a === '--to') options.to = Number(next());
    else if (a === '--step') options.step = Math.max(1, Math.round(Number(next())));
    else if (a === '--order-check') options.orderCheck = Math.max(0, Math.round(Number(next())));
    else if (a === '--query') options.query = next();
    else if (a === '--kit') options.kit = path.resolve(next());
    else if (a === '--serve') {
      const [address, folder] = next().split('=');
      options.serve.push({ address: address.replace(/\/+$/, ''), folder: path.resolve(folder) });
    } else if (a === '--render-stills') {
      options.renderStills = next();
      while (i + 1 < argv.length && !argv[i + 1].startsWith('--')) options.stillTimes.push(...argv[++i].split(',').filter(Boolean).map(Number));
    } else plain.push(a);
  }
  [options.scene, options.out] = plain;
  for (const n of [options.from, options.to, ...options.stillTimes]) if (n !== null && !Number.isFinite(n)) throw new Error(`not a number in seconds: ${n}`);
  if (options.pages && options.pages.some((n) => !Number.isInteger(n))) throw new Error('--pages takes page numbers, e.g. 3,4,5');
  return options;
}

function serve(kitFolder, extra) {
  const server = http.createServer((request, response) => {
    const address = decodeURIComponent(new URL(request.url, 'http://x').pathname);
    if (address === '/favicon.ico') { response.writeHead(204); response.end(); return; }
    let file = null;
    const mapped = extra.find((m) => address === m.address || address.startsWith(`${m.address}/`));
    if (mapped) {
      file = path.join(mapped.folder, address.slice(mapped.address.length));
      if (!file.startsWith(mapped.folder)) file = null;
    } else {
      file = path.join(kitFolder, address);
      if (!file.startsWith(kitFolder)) file = null;
    }
    if (!file || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] ?? 'application/octet-stream' });
    fs.createReadStream(file).pipe(response);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function loadPlaywright(options) {
  const tries = [process.env.PAPER_FILM_PLAYWRIGHT, 'playwright-core',
    ...options.serve.filter((m) => m.address.endsWith('node_modules')).map((m) => path.join(m.folder, 'playwright-core', 'index.mjs')),
    path.join(options.kit, 'paper-film', 'node_modules', 'playwright-core', 'index.mjs')].filter(Boolean);
  for (const name of tries) {
    try { return await import(name.endsWith('.mjs') ? pathToFileURL(name).href : name); } catch { /* try the next */ }
  }
  throw new Error('playwright-core was not found: run npm install in paper-film, or set PAPER_FILM_PLAYWRIGHT to its index.mjs');
}

// Switched on before any of the stage's own code runs: graphics.js and cinema-kit.js look for this.
function switchOnNotes() {
  window.pageEvents = {
    on: true, current: { page: null, frame: null, t: null }, notes: [], lookups: [],
    note(fields) { this.notes.push({ ...fields, page: this.current.page, frame: this.current.frame }); },
    lookup(fields) { this.lookups.push(fields); },
  };
}

// Runs inside the stage page: samples every frame and keeps what the notes say, folded into tracks.
async function sampleInPage({ fromTime, toTime, fps, step, pagesWanted, orderCheck }) {
  const built = window.built;
  const events = window.pageEvents;
  const stage = await import('/paper-film/stage/cinema-stage.js');
  const graphics = await import('/paper-film/scenes/graphics.js');
  const MOVING = 1 << stage.MOVING_LAYER;
  const canvas = document.createElement('canvas');
  canvas.width = stage.FRAME_WIDTH; canvas.height = stage.FRAME_HEIGHT;
  const context = canvas.getContext('2d', { willReadFrequently: false });
  const round = (x, digits) => (x === null || x === undefined || !Number.isFinite(x) ? x : Number(x.toFixed(digits)));
  const roundBox = (box) => (box ? box.map((v) => round(v, 1)) : null);
  const effectRoots = new Map();   // page index -> [{ id, object }]
  const findEffects = (i) => {
    if (effectRoots.has(i)) return effectRoots.get(i);
    const roots = [];
    built.kits[i].scene.traverse((o) => {
      if (!(o.layers.mask & MOVING)) return;
      if (o.parent && (o.parent.layers.mask & MOVING)) return;   // only the top of each moving thing
      roots.push({ id: `${o.name || o.type}#${roots.length}`, object: o, uuid: o.uuid });
    });
    effectRoots.set(i, roots);
    return roots;
  };
  const shown = (o) => { for (let x = o; x; x = x.parent) if (!x.visible) return false; return true; };
  const pagesAt = (t) => (built.pagesAt ? built.pagesAt(t) : [0]);

  // one frame: every showing page's pose and draw2D, as cinema-chapter.js draws it
  async function frameAt(frame) {
    const t = fromTime + frame / fps;
    if (built.prepare) await built.prepare(t);
    const showing = pagesAt(t);
    const row = { f: frame, t: round(t, 4), pages: [], join: null };
    if (showing.length === 2) {
      const j = built.joins[showing[0]];
      row.join = { page: built.kits[showing[0]].number, kind: j.kind, progress: round((t - j.start) / j.length, 4) };
    }
    const notesBefore = events.notes.length;
    for (const i of showing) {
      const kit = built.kits[i];
      const page = built.pages[i];
      kit.t = t;
      kit.shotShowing = null;
      events.current = { page: kit.number, frame, t };
      const state = page.pose(t) ?? {};
      if (state.camera) kit.aim(state.camera, t);
      const c = kit.camera, r5 = (x) => x.toFixed(5);
      // the held-shot key exactly as cinema-chapter.js showPage makes it (the camera's place is part of it)
      const stillKey = state.still ? [i, state.still === true ? '' : state.still, ...c.position.toArray().map(r5), ...c.quaternion.toArray().map(r5), r5(c.fov)].join('|') : null;
      const effects = findEffects(i).filter((e) => shown(e.object)).map((e) => e.id);
      context.reset?.();
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.save();
      const drew = page.draw2D ? page.draw2D(context, t, kit) : false;
      context.restore();
      row.pages.push({
        page: kit.number, shot: kit.shotShowing ?? null,
        page_still: state.still === undefined || state.still === null || state.still === false ? null : String(state.still),
        still_key: stillKey,
        camera: [...c.position.toArray().map((v) => round(v, 4)), ...c.quaternion.toArray().map((v) => round(v, 6)), round(c.fov, 4)],
        effects, drew: drew !== false && drew !== undefined,
      });
    }
    events.current = { page: null, frame: null, t: null };
    const notes = events.notes.splice(notesBefore);
    return { row, notes };
  }

  // the moments to sample (frame numbers counted from fromTime)
  const frames = [];
  const total = Math.floor((toTime - fromTime) * fps + 1e-6);
  for (let frame = 0; frame <= total; frame += step) {
    if (pagesWanted) {
      const showing = pagesAt(fromTime + frame / fps).map((i) => built.kits[i].number);
      if (!showing.some((n) => pagesWanted.includes(n))) continue;
    }
    frames.push(frame);
  }

  const rows = [];
  const items = new Map();
  // one drawn thing across frames: its page, kind, start and words (a counter: its place and caption, as its figure
  // changes from frame to frame, and some pages pass a new value every frame)
  const identity = (n) => [n.page, n.fn, n.kind, round(n.at ?? -1, 3), n.fn === 'counter' ? `${round(n.x, 1)},${round(n.y, 1)}|${n.caption ?? ''}` : n.text, n.within ?? ''].join('|');
  const summary = new Map();   // frame -> a fingerprint of everything drawn, for the order check
  const fingerprint = (row, notes) => JSON.stringify([row.pages.map((p) => [p.page, p.page_still, p.still_key, p.effects]),
    notes.map((n) => [identity(n), round(n.opacity, 3), roundBox(n.box)])]);
  for (const frame of frames) {
    const { row, notes } = await frameAt(frame);
    rows.push(row);
    if (orderCheck && rows.length % orderCheck === 1) summary.set(frame, fingerprint(row, notes));
    for (const n of notes) {
      const id = identity(n);
      let item = items.get(id);
      // the track keeps a point wherever something changes: [frame, opacity, box, words' opacity, how far drawn, counter text]
      const point = [frame, round(n.opacity, 4), roundBox(n.box), round(n.wordsOpacity ?? n.wordOpacity ?? null, 4), round(n.drawn ?? n.filled ?? null, 4), n.fn === 'counter' ? n.text : null];
      if (!item) {
        const { opacity, wordsOpacity, wordOpacity, drawn, filled, box, frame: noteFrame, value, ...fixed } = n;
        item = { id, ...fixed, runs: [[frame, frame]], track: [point] };
        items.set(id, item);
        continue;
      }
      // runs: the stretches of frames it is drawn in (not drawn in between: 0)
      const run = item.runs[item.runs.length - 1];
      const newRun = frame - run[1] > step;
      if (newRun) item.runs.push([frame, frame]); else run[1] = frame;
      const last = item.track[item.track.length - 1];
      if (newRun || JSON.stringify(last.slice(1)) !== JSON.stringify(point.slice(1))) item.track.push(point);
      if (Array.isArray(n.line)) item.line = roundBox(n.line);     // a label's line, as far as it has drawn
      if (n.point) item.point = { x: round(n.point.x, 1), y: round(n.point.y, 1) };
    }
  }

  // the order check: some of the same moments again, last first
  const orderDifferences = [];
  if (orderCheck) {
    for (const frame of [...summary.keys()].reverse()) {
      const { row, notes } = await frameAt(frame);
      const again = fingerprint(row, notes);
      if (again !== summary.get(frame)) {
        const before = JSON.parse(summary.get(frame)), after = JSON.parse(again);
        orderDifferences.push({ frame, t: row.t, in_order: before, out_of_order: after });
      }
    }
  }

  // live effects: the frames each one shows, as runs
  const effects = [];
  const runsOf = new Map();
  for (const row of rows) {
    for (const p of row.pages) {
      for (const id of p.effects) {
        const key = `${p.page}|${id}`;
        if (!runsOf.has(key)) runsOf.set(key, { page: p.page, id, runs: [] });
        const runs = runsOf.get(key).runs;
        if (runs.length && row.f - runs[runs.length - 1][1] <= step) runs[runs.length - 1][1] = row.f;
        else runs.push([row.f, row.f]);
      }
    }
  }
  effects.push(...runsOf.values());
  const effectCounts = [...effectRoots.entries()].map(([i, roots]) => ({ page: built.kits[i].number, live_things: roots.map((e) => e.id) }));
  // a live thing found in more than one page's world (one page's smoke or dust handed to another) can show after its page
  const pagesOf = new Map();
  for (const [i, roots] of effectRoots.entries()) for (const e of roots) pagesOf.set(e.uuid, [...(pagesOf.get(e.uuid) ?? []), { page: built.kits[i].number, id: e.id }]);
  const sharedLiveThings = [...pagesOf.values()].filter((list) => list.length > 1);

  const pages = built.kits.map((kit, i) => ({
    index: i, number: kit.number, first_word_at: kit.firstWordAt, last_word_end_at: kit.lastWordEnd,
    words: kit.words.map((w) => ({ text: w.text, start: w.start, end: w.end })),
    join: built.joins?.[i] ? { kind: built.joins[i].kind, after: built.joins[i].after, length: built.joins[i].length, start: built.joins[i].start, end: built.joins[i].end } : null,
    built: Boolean(built.pages[i]),
    camera_plans: kit.cameraPlans ?? [],
  }));
  // each frame keeps how many live things showed and a short fingerprint of which (the full list per thing is in effects)
  const shortHash = (text) => { let h = 2166136261; for (let k = 0; k < text.length; k++) { h ^= text.charCodeAt(k); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); };
  for (const row of rows) {
    for (const p of row.pages) {
      if (!p.drew) delete p.drew;
      p.effects_shown = p.effects.length;
      p.effects_key = p.effects.length ? shortHash(p.effects.join(',')) : null;
      delete p.effects;
      delete p.still_key;   // the page's own still value and the camera say the same (the key is both, as cinema-chapter.js makes it)
    }
  }
  return {
    frame_size: [stage.FRAME_WIDTH, stage.FRAME_HEIGHT], appear_delays: graphics.APPEAR_DELAYS, text_left: graphics.TEXT_LEFT, text_right: graphics.TEXT_RIGHT,
    // where each lookup was asked from, without this run's server address (so two runs write the same file)
    pages, lookups: events.lookups.map((l) => ({ ...l, asked_from: (l.asked_from ?? '').replace(location.origin, '') })), frames: rows, items: [...items.values()], effects, live_things: effectCounts, shared_live_things: sharedLiveThings,
    order_differences: orderDifferences,
    sampled_frames: frames.length,
  };
}

async function main() {
  let options;
  try { options = readArguments(process.argv.slice(2)); } catch (problem) { console.error(problem.message); process.exit(2); }
  if (options.help) { console.log(`Usage: node page_events.mjs SCENE OUT.json [options]\n\n${HELP}`); return; }
  if (!options.scene || (!options.out && !options.renderStills)) {
    console.error('Usage: node page_events.mjs SCENE OUT.json [--pages 3,4,5] [--from S --to S] [--step N] [--order-check N] [--kit DIR] [--serve /URL=DIR] (--help for more)');
    process.exit(2);
  }
  const sceneFile = path.join(options.kit, 'paper-film', 'scenes', `${options.scene}.js`);
  if (!fs.existsSync(sceneFile)) { console.error(`no scene ${sceneFile}`); process.exit(2); }
  if (!fs.readFileSync(sceneFile, 'utf8').includes('buildCinemaChapter')) {
    console.error(`${options.scene} is not a cinema chapter (it never calls buildCinemaChapter); page events work on cinema pages only`);
    process.exit(2);
  }
  const { chromium } = await loadPlaywright(options);
  const server = await serve(options.kit, options.serve);
  const { findBrowser } = await import('./find-browser.mjs');
  const browser = await chromium.launch({ executablePath: findBrowser(), args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const started = Date.now();
  try {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    page.on('console', (message) => { if (message.type() === 'error' || message.type() === 'warning') console.log('[stage]', message.text()); });
    page.on('pageerror', (error) => console.log('[stage error]', error.message));
    await page.addInitScript(switchOnNotes);
    const address = `http://127.0.0.1:${server.address().port}/paper-film/stage/cinema-stage.html?scene=${options.scene}${options.query ? `&${options.query}` : ''}`;
    await page.goto(address);
    await page.waitForFunction('window.stageReady === true || window.stageFailed', null, { timeout: 600000 });
    const failed = await page.evaluate(() => window.stageFailed);
    if (failed) throw new Error(`the scene did not load: ${failed}`);
    const info = await page.evaluate(() => window.sceneInfo);
    if (options.renderStills) {
      fs.mkdirSync(options.renderStills, { recursive: true });
      for (const time of options.stillTimes) {
        await page.evaluate((t) => window.prepareFrame?.(t), time);
        const dataUrl = await page.evaluate((t) => window.renderFrame(t), time);
        const file = path.join(options.renderStills, `still-${time.toFixed(2)}.jpg`);
        fs.writeFileSync(file, Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64'));
        console.log(`${file} (drawn with page events switched on)`);
      }
      const noted = await page.evaluate(() => window.pageEvents.notes.length);
      console.log(`notes taken while drawing: ${noted}`);
      return;
    }
    const fromTime = options.from ?? info.start;
    const toTime = Math.min(options.to ?? info.end, info.end);
    const result = await page.evaluate(sampleInPage, { fromTime, toTime, fps: FRAMES_PER_SECOND, step: options.step, pagesWanted: options.pages, orderCheck: options.orderCheck });
    const output = {
      what: 'page events: everything a cinema page did at each frame, from paper-film/tools/page_events.mjs (read by calculators/plan_page_timing.py and tools/check_page_layout.mjs)',
      scene: options.scene, query: options.query || null, fps: FRAMES_PER_SECOND, step: options.step, from_seconds: fromTime, to_seconds: toTime,
      frame_zero_seconds: fromTime, scene_start: info.start, scene_end: info.end, page_edges: info.pageEdges ?? [], pages_asked: options.pages,
      made: new Date().toISOString(), seconds_taken: Math.round((Date.now() - started) / 1000), ...result,
    };
    fs.mkdirSync(path.dirname(path.resolve(options.out)), { recursive: true });
    fs.writeFileSync(options.out, JSON.stringify(output));
    const words = result.items.filter((item) => ['words', 'label', 'tag', 'hook', 'counter', 'title', 'credit'].includes(item.kind)).length;
    console.log(`wrote ${options.out}: ${result.sampled_frames} frames (${(fromTime).toFixed(2)} to ${toTime.toFixed(2)} s), ${result.items.length} drawn things `
      + `(${words} with words), ${result.lookups.length} word lookups, ${result.effects.length} live things, `
      + `${result.order_differences.length} moments that differ when drawn out of order; ${Math.round((Date.now() - started) / 1000)} s`);
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((error) => { console.error(error); process.exit(1); });
