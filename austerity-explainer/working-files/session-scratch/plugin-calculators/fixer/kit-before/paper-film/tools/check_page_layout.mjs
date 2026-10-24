// What this does: checks what single stills miss, from a page events file (tools/page_events.mjs), without drawing
// anything. It is the slim page pose sampler of log 35 (the skeptic's cut):
//   1. pops: a flat graphic or a live thing (smoke, flame, glow) that comes or goes in two frames or fewer, shows for
//      two frames or fewer, or jumps across the frame in one frame (a label flipping sides), at a moment that is not a
//      planned cut (log 27's one-frame faults; lesson 86);
//   2. effects that outlive their moment or their page: a moment that comes out different when drawn out of order
//      (lesson 29: dust from page 8 showed on pages 9 and 10 when single moments were drawn for checking), and a live
//      thing shared by two pages' worlds;
//   3. held-shot keys while the camera moves (the set is then drawn twice a frame) and the held picture changing during a
//      move (plan 34: a state changes only while the camera holds);
//   4. holds with no held-shot key (the whole set is drawn every frame, about five times slower);
//   5. overlaps at events: two drawn things (words, labels, tags, cards, rings) in the same place at the moment one of
//      them comes in, a cut, or a move starts or ends.
// The paper look's own checks (standing pieces at their own distance, rows too wide, knocked-down pieces, a crane seen
// from too high) and 3D clearance are not here: the cinema look does not use them, and the events hold no 3D boxes.
//
// Use: node check_page_layout.mjs EVENTS.json[.gz] [--pages 3,4,5] [--json] [--out FILE] [--report FILE] [--settings FILE]
//   --pages     only these chapter pages (default: the pages the events were made for)
//   --json      print the result as JSON instead of the plain report
//   --out FILE  also write the JSON result;  --report FILE  also write the plain report
//   --settings  film-settings.json to read (default: the kit's, or the FILM_SETTINGS setting)
// Exit 1 when anything fails, 0 otherwise. The report names every film-settings.json value it used.

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const HELP = fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').filter((line) => line.startsWith('//')).map((line) => line.slice(3)).join('\n');
const KIT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');

function readArguments(argv) {
  const options = { json: false, pages: null, out: null, report: null, settings: process.env.FILM_SETTINGS ?? path.join(KIT, 'film-settings.json') };
  const plain = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => { if (i + 1 >= argv.length) throw new Error(`${a} needs a value`); return argv[++i]; };
    if (a === '--help' || a === '-h') options.help = true;
    else if (a === '--json') options.json = true;
    else if (a === '--pages') options.pages = next().split(',').map(Number);
    else if (a === '--out') options.out = next();
    else if (a === '--report') options.report = next();
    else if (a === '--settings') options.settings = next();
    else plain.push(a);
  }
  [options.events] = plain;
  return options;
}

// film-settings.json, noting every value read (as settings.py does), so the report can name them
function settingsReader(file) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const used = new Map();
  return {
    file,
    value(key) {
      let node = data;
      for (const part of key.split('.')) {
        if (!node || typeof node !== 'object' || !(part in node)) throw new Error(`film-settings.json has no "${key}" ("${part}" is missing)`);
        node = node[part];
      }
      used.set(key, node);
      return node.value;
    },
    usedLines: () => [...used.entries()].map(([key, e]) => `${key} = ${JSON.stringify(e.value)} ${e.unit ?? ''} (${e.kind})`),
    usedJson: () => Object.fromEntries([...used.entries()].map(([key, e]) => [key, { value: e.value, unit: e.unit, kind: e.kind, source: e.source }])),
  };
}

const problem = (check, verdict, page, what, detail, fix = '', extra = {}) => ({ check, verdict, page, what, detail, fix, ...extra });

// how strongly a drawn thing shows in a frame (0 to 1): a label or title by its words, an arrow or pointer by how much
// of it has drawn, anything else by its own strength
function strengthOf(item, point) {
  if (['label', 'title'].includes(item.kind) && point[3] !== null && point[3] !== undefined) return point[3];
  if (['pointer', 'arrow'].includes(item.kind) && point[4] !== null && point[4] !== undefined) return point[1] * point[4];
  return point[1];
}

// every sampled frame an item is drawn in, with its track values there
function pointsByFrame(item, step) {
  const out = new Map();
  let index = 0;
  for (const [start, end] of item.runs) {
    for (let frame = start; frame <= end; frame += step) {
      while (index + 1 < item.track.length && item.track[index + 1][0] <= frame) index++;
      out.set(frame, item.track[index]);
    }
  }
  return out;
}

const boxesMeet = (a, b, by) => Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > by && Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > by;
const sameCamera = (a, b, tolerance) => a.length === b.length && a.every((v, k) => Math.abs(v - b[k]) <= tolerance);

export function checkPageLayout(events, settings, pagesWanted = null) {
  const fps = events.fps, step = events.step ?? 1, zero = events.frame_zero_seconds;
  const time = (frame) => zero + frame / fps;
  const popFrames = settings.value('page_timing.layout.pop_frames_max');
  const popChange = settings.value('page_timing.layout.pop_strength_change');
  const holdFrames = settings.value('page_timing.layout.hold_without_still_key_frames');
  const tolerance = settings.value('page_timing.layout.camera_still_tolerance');
  const jumpPixels = settings.value('page_timing.layout.jump_pixels_min');
  const overlapLeast = settings.value('page_timing.overlap_opacity_min');
  const overlapBy = settings.value('page_timing.overlap_pixels_min');
  const sampled = [...new Set(events.frames.flatMap((row) => row.pages.map((p) => p.page)))].sort((a, b) => a - b);
  const pages = pagesWanted ?? events.pages_asked ?? sampled;
  const out = [];

  // the frames of each page, in order, and the planned cuts: shot changes, held-picture steps, a page's first and last
  // frames (the joins)
  const rowsOf = new Map();
  for (const row of events.frames) for (const p of row.pages) {
    if (!rowsOf.has(p.page)) rowsOf.set(p.page, []);
    rowsOf.get(p.page).push({ f: row.f, t: row.t, ...p });
  }
  const planned = new Map();   // page -> Set of frames where a change is planned
  const plan = (page, frame, why) => { if (!planned.has(page)) planned.set(page, new Map()); planned.get(page).set(frame, why); };
  for (const [page, rows] of rowsOf) {
    plan(page, rows[0].f, 'the page comes in'); plan(page, rows[rows.length - 1].f + step, 'the page has gone');
    for (let k = 1; k < rows.length; k++) {
      const a = rows[k - 1], b = rows[k];
      if (b.f - a.f > step) { plan(page, b.f, 'the page comes in again'); plan(page, a.f + step, 'the page goes'); }
      if (b.shot !== a.shot) plan(page, b.f, `cut to ${b.shot}`);
      else if (b.page_still !== a.page_still && b.page_still !== null && a.page_still !== null) plan(page, b.f, 'the held picture steps');
    }
    const info = events.pages.find((p) => p.number === page);
    if (info?.join) { plan(page, Math.ceil((info.join.start - zero) * fps - 1e-6), `${info.join.kind} starts`); plan(page, Math.ceil((info.join.end - zero) * fps - 1e-6), `${info.join.kind} ends`); }
  }
  const nearPlanned = (page, frame) => {
    const marks = planned.get(page);
    if (!marks) return null;
    for (let d = -step; d <= step; d += step) if (marks.has(frame + d)) return marks.get(frame + d);
    return null;
  };

  // 1. pops: flat graphics
  const items = events.items.filter((item) => pages.includes(item.page) && item.kind !== 'shade');
  const tracks = new Map(items.map((item) => [item.id, pointsByFrame(item, step)]));
  let popsFound = 0;
  for (const item of items) {
    const series = tracks.get(item.id);
    const name = item.text || item.kind;
    const framesDrawn = [...series.keys()];
    const seen = framesDrawn.filter((f) => strengthOf(item, series.get(f)) > 0.05).length;
    if (seen > 0 && seen <= popFrames) {
      const first = framesDrawn.find((f) => strengthOf(item, series.get(f)) > 0.05);
      out.push(problem('pops', 'fail', item.page, name, `shows for only ${seen} frame${seen > 1 ? 's' : ''} (${time(first).toFixed(2)} s)`,
        'give it a real time on screen, or take it out', { frame: first, seconds: time(first) }));
      popsFound++;
      continue;
    }
    // comes or goes too fast, away from a planned cut
    const strength = (f) => (series.has(f) ? strengthOf(item, series.get(f)) : 0);
    const first = framesDrawn[0], last = framesDrawn[framesDrawn.length - 1];
    for (const [from, to, word] of [[first - step, first + popFrames * step, 'comes in'], [last + step, last - popFrames * step, 'goes']]) {
      const edge = word === 'comes in' ? first : last + step;
      if (nearPlanned(item.page, edge)) continue;
      const before = strength(word === 'comes in' ? from : to), after = strength(word === 'comes in' ? to : from);
      const fullBy = word === 'comes in' ? framesDrawn.slice(0, popFrames).some((f) => strength(f) >= popChange) : framesDrawn.slice(-popFrames).some((f) => strength(f) >= popChange);
      if (fullBy && Math.abs(after - before) >= popChange) {
        out.push(problem('pops', 'fail', item.page, name, `${word} in ${popFrames} frames or fewer at ${time(edge).toFixed(2)} s, not at a planned cut`,
          word === 'comes in' ? 'fade it in over at least 3 frames, or bring it in on a cut' : 'fade it out, or end it exactly on a cut (fadeOut 0 there)', { frame: edge, seconds: time(edge) }));
        popsFound++;
      }
    }
  }
  // jumps: a drawn thing that moves across the frame in one frame (a label flipping to its other side, log 27's
  // scissors) while it shows, away from a planned cut
  for (const item of items) {
    const series = tracks.get(item.id);
    let previous = null;
    for (const [frame, point] of series) {
      if (previous && frame - previous.frame === step && point[2] && previous.point[2]
          && strengthOf(item, point) >= 0.5 && strengthOf(item, previous.point) >= 0.5 && !nearPlanned(item.page, frame)) {
        // (judged on what shows: old chapter 2's BARELY MOVE flips sides while its words are still waiting to come in,
        // and the film shows nothing there)
        const dx = (point[2][0] + point[2][2] - previous.point[2][0] - previous.point[2][2]) / 2;
        const dy = (point[2][1] + point[2][3] - previous.point[2][1] - previous.point[2][3]) / 2;
        if (Math.hypot(dx, dy) >= jumpPixels) {
          out.push(problem('pops', 'fail', item.page, item.text || item.kind, `jumps ${Math.hypot(dx, dy).toFixed(0)} px in one frame at ${time(frame).toFixed(2)} s`,
            item.kind === 'label' ? 'give the label a fixed side (side: \'left\' or \'right\') so it cannot flip while it shows' : 'move it smoothly, or only on a cut',
            { frame, seconds: time(frame) }));
          popsFound++;
          break;
        }
      }
      previous = { frame, point };
    }
  }
  // pops: live things (each one's runs of frames shown)
  for (const effect of events.effects ?? []) {
    if (!pages.includes(effect.page)) continue;
    for (const [start, end] of effect.runs) {
      const length = (end - start) / step + 1;
      const atEdges = nearPlanned(effect.page, start) && nearPlanned(effect.page, end + step);
      if (length <= popFrames && !atEdges) {
        out.push(problem('pops', 'fail', effect.page, `live thing ${effect.id}`, `shows for only ${length} frame${length > 1 ? 's' : ''} (${time(start).toFixed(2)} s)`,
          'switch it on and off on planned moments, or fade it', { frame: start, seconds: time(start) }));
        popsFound++;
      }
    }
  }
  if (!popsFound) out.push(problem('pops', 'pass', null, 'all', `nothing comes or goes in ${popFrames} frames or fewer outside a planned cut (${items.length} drawn things, ${(events.effects ?? []).filter((e) => pages.includes(e.page)).length} live things)`));

  // 2. effects that outlive their moment or their page
  const differences = (events.order_differences ?? []).filter((d) => {
    const inOrder = d.in_order?.[0] ?? [];
    return inOrder.some((p) => pages.includes(p[0])) || !inOrder.length;
  });
  // one problem per page and thing that differs, with the moments it differs at
  const differing = new Map();
  for (const d of differences) {
    const before = d.in_order, after = d.out_of_order;
    const add = (page, what) => { const key = `${page}|${what}`; if (!differing.has(key)) differing.set(key, { page, what, seconds: [] }); differing.get(key).seconds.push(d.t); };
    (before[0] ?? []).forEach((p, k) => {
      const q = (after[0] ?? [])[k];
      if (!q) return;
      for (const id of (q[3] ?? []).filter((x) => !(p[3] ?? []).includes(x))) add(p[0], `live thing ${id} shows when drawn out of order`);
      for (const id of (p[3] ?? []).filter((x) => !(q[3] ?? []).includes(x))) add(p[0], `live thing ${id} is missing when drawn out of order`);
      if (p[1] !== q[1] || p[2] !== q[2]) add(p[0], `the held picture differs (${p[1]} in order, ${q[1]} out of order)`);
    });
    if (JSON.stringify(before[1]) !== JSON.stringify(after[1])) add((before[0] ?? [])[0]?.[0] ?? null, 'the flat graphics differ');
  }
  for (const d of differing.values()) {
    const seconds = d.seconds.sort((a, b) => a - b);
    out.push(problem('effects after their moment', 'fail', d.page, d.what,
      `at ${seconds.length} of the moments drawn again out of order (${seconds[0].toFixed(2)} to ${seconds[seconds.length - 1].toFixed(2)} s): what shows depends on what was drawn before`,
      'set every effect from the moment alone (visible = a test on t, never left on from an earlier frame); lesson 29', { seconds }));
  }
  for (const shared of events.shared_live_things ?? []) {
    out.push(problem('effects after their page', 'fail', shared[0].page, shared.map((s) => `${s.id} (page ${s.page})`).join(' = '),
      'one live thing is in two pages\' worlds, so it can show after its page', 'give each page its own copy'));
  }
  if (!differences.length && !(events.shared_live_things ?? []).length) {
    const checked = Math.ceil((events.sampled_frames ?? events.frames.length) / 15);
    out.push(problem('effects after their moment', 'pass', null, 'all', (events.order_differences ? `about ${checked} moments drawn again out of order came out the same; ` : 'no order check in these events; ') + 'no live thing is shared between pages'));
  }

  // 3 and 4. held-shot keys during moves, state changes during moves, holds without a key
  for (const page of pages) {
    const rows = rowsOf.get(page) ?? [];
    let keyDuringMove = [], stepDuringMove = [], holdNoKey = [], run = null;
    const flushHold = () => { if (run && run.frames >= holdFrames) holdNoKey.push(run); run = null; };
    for (let k = 1; k < rows.length; k++) {
      const a = rows[k - 1], b = rows[k];
      if (b.f - a.f > step) { flushHold(); continue; }
      const moving = !sameCamera(a.camera, b.camera, tolerance) && a.shot === b.shot;
      if (moving && b.page_still !== null) keyDuringMove.push(b);
      if (moving && a.page_still !== null && b.page_still !== null && a.page_still !== b.page_still) stepDuringMove.push(b);
      if (!moving && b.page_still === null) {
        run = run ?? { from: b.f, frames: 0, shot: b.shot };
        run.frames++;
        run.to = b.f;
      } else flushHold();
    }
    flushHold();
    const stretches = (list) => {
      const groups = [];
      for (const r of list) {
        const last = groups[groups.length - 1];
        if (last && r.f - last.to <= step) { last.to = r.f; last.frames++; } else groups.push({ from: r.f, to: r.f, frames: 1, shot: r.shot });
      }
      return groups;
    };
    for (const g of stretches(keyDuringMove)) {
      out.push(problem('held key during a move', 'fail', page, g.shot, `the page returns a held-shot key while the camera moves (${time(g.from).toFixed(2)} to ${time(g.to).toFixed(2)} s, ${g.frames} frames): the set is drawn twice a frame`,
        'return still: false while the camera moves (as page 3 does during its slide)', { from: time(g.from), to: time(g.to) }));
    }
    for (const g of stretches(stepDuringMove)) {
      out.push(problem('state change during a move', 'fail', page, g.shot, `the held picture changes while the camera moves (${time(g.from).toFixed(2)} s)`,
        'change states only while the camera holds (plan 34)', { from: time(g.from) }));
    }
    for (const g of holdNoKey) {
      out.push(problem('hold without a key', 'look', page, g.shot, `the camera holds for ${(g.frames / fps).toFixed(2)} s (${time(g.from).toFixed(2)} to ${time(g.to).toFixed(2)} s) with no held-shot key: the whole set is drawn every frame, about five times slower`,
        'return still: true (or a key that changes when the set changes) from pose(t) while the camera holds', { from: time(g.from), to: time(g.to), seconds: g.frames / fps }));
    }
    if (!keyDuringMove.length && !stepDuringMove.length && !holdNoKey.length && rows.length) {
      out.push(problem('held shots', 'pass', page, `page ${page}`, 'held-shot keys only while the camera holds, and every hold has one'));
    }
  }

  // 5. overlaps at events: the moments something comes in, a cut, a move's start and end
  const eventFrames = new Map();
  const mark = (page, frame, why) => { const key = `${page}|${frame}`; if (!eventFrames.has(key)) eventFrames.set(key, { page, frame, why: [] }); eventFrames.get(key).why.push(why); };
  for (const item of items) {
    const series = tracks.get(item.id);
    const frames = [...series.keys()];
    if (!frames.length) continue;
    mark(item.page, frames[0], `${item.text || item.kind} comes in`);
    const full = frames.find((f) => strengthOf(item, series.get(f)) >= 0.99);
    if (full !== undefined) mark(item.page, full, `${item.text || item.kind} at full strength`);
  }
  for (const [page, marks] of planned) for (const [frame, why] of marks) if (pages.includes(page)) mark(page, frame, why);
  for (const info of events.pages) {
    if (!pages.includes(info.number)) continue;
    for (const p of info.camera_plans ?? []) for (const m of p.moves) {
      mark(info.number, Math.ceil((m.from - zero) * fps - 1e-6), `${p.name} ${m.kind} starts`);
      mark(info.number, Math.ceil((m.to - zero) * fps - 1e-6), `${p.name} ${m.kind} ends`);
    }
  }
  const drawable = items.filter((item) => ['words', 'label', 'tag', 'hook', 'counter', 'title', 'credit', 'card', 'ring', 'dots', 'chart'].includes(item.kind));
  const pairs = new Map();
  for (const { page, frame, why } of eventFrames.values()) {
    const showing = drawable.filter((item) => item.page === page && tracks.get(item.id).has(frame)).map((item) => ({ item, point: tracks.get(item.id).get(frame) }))
      .filter(({ item, point }) => point[2] && strengthOf(item, point) > overlapLeast);
    for (let a = 0; a < showing.length; a++) {
      for (let b = a + 1; b < showing.length; b++) {
        const x = showing[a], y = showing[b];
        if (x.item.group && x.item.group === y.item.group) continue;
        if (x.item.within && x.item.within === y.item.within) continue;
        if ((x.item.kind === 'card' && y.item.within === x.item.id) || (y.item.kind === 'card' && x.item.within === y.item.id)) continue;
        if (!boxesMeet(x.point[2], y.point[2], overlapBy)) continue;
        const key = [x.item.id, y.item.id].sort().join(' & ');
        if (!pairs.has(key)) pairs.set(key, { page, names: [x.item.text || x.item.kind, y.item.text || y.item.kind], frames: [], why: new Set() });
        pairs.get(key).frames.push(frame);
        why.forEach((w) => pairs.get(key).why.add(w));
      }
    }
  }
  for (const pair of pairs.values()) {
    const frames = pair.frames.sort((a, b) => a - b);
    out.push(problem('overlaps at events', 'fail', pair.page, `${pair.names[0]} and ${pair.names[1]}`,
      `in the same place at ${frames.map((f) => time(f).toFixed(2)).join(', ')} s (${[...pair.why].slice(0, 3).join('; ')})`,
      'move one, or end the old one a frame before the new one comes (its fade counts inside its until)', { seconds: frames.map(time) }));
  }
  if (!pairs.size) out.push(problem('overlaps at events', 'pass', null, 'all', `no two drawn things in the same place at ${eventFrames.size} event moments`));

  const order = { fail: 0, look: 1, pass: 2 };
  out.sort((a, b) => order[a.verdict] - order[b.verdict] || a.check.localeCompare(b.check) || (a.page ?? 0) - (b.page ?? 0));
  return { pages, verdicts: { fail: out.filter((p) => p.verdict === 'fail').length, look: out.filter((p) => p.verdict === 'look').length, pass: out.filter((p) => p.verdict === 'pass').length }, problems: out };
}

function reportLines(result, events) {
  const lines = [`Page layout for ${events.scene}, pages ${result.pages.join(', ')}: ${result.verdicts.fail} to fix, ${result.verdicts.look} to look at, ${result.verdicts.pass} passed.`];
  let current = null;
  for (const p of result.problems) {
    if (p.check !== current) { current = p.check; lines.push('', current.toUpperCase()); }
    lines.push(`  ${p.verdict.toUpperCase().padEnd(5)} ${p.page !== null ? `page ${p.page}` : 'all'}: ${p.what}: ${p.detail}`);
    if (p.fix && p.verdict !== 'pass') lines.push(`        fix: ${p.fix}`);
  }
  return lines;
}

function main() {
  let options;
  try { options = readArguments(process.argv.slice(2)); } catch (problemText) { console.error(problemText.message); process.exit(2); }
  if (options.help) { console.log(`Usage: node check_page_layout.mjs EVENTS.json [options]\n\n${HELP}`); return 0; }
  if (!options.events) { console.error('Usage: node check_page_layout.mjs EVENTS.json [--pages 3,4,5] [--json] [--out FILE] [--report FILE] [--settings FILE] (--help for more)'); return 2; }
  const raw = fs.readFileSync(options.events);
  const events = JSON.parse((options.events.endsWith('.gz') ? zlib.gunzipSync(raw) : raw).toString('utf8'));
  const settings = settingsReader(options.settings);
  const result = checkPageLayout(events, settings, options.pages);
  const full = { calculator: 'check_page_layout', events: options.events, scene: events.scene, ...result, settings_file: settings.file, settings_used: settings.usedJson() };
  const text = [...reportLines(result, events), '', 'Settings used (film-settings.json):', ...settings.usedLines().map((l) => `  ${l}`)].join('\n');
  console.log(options.json ? JSON.stringify(full, null, 1) : text);
  if (options.out) { fs.mkdirSync(path.dirname(path.resolve(options.out)), { recursive: true }); fs.writeFileSync(options.out, JSON.stringify(full, null, 1)); }
  if (options.report) { fs.mkdirSync(path.dirname(path.resolve(options.report)), { recursive: true }); fs.writeFileSync(options.report, `${text}\n`); }
  return result.verdicts.fail ? 1 : 0;
}

const runAsTool = () => { try { return fs.realpathSync(process.argv[1]) === fs.realpathSync(new URL(import.meta.url).pathname); } catch { return false; } };
if (process.argv[1] && runAsTool()) process.exitCode = main();
