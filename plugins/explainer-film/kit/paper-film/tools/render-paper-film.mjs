// What this does: films a paper scene. It serves the kit folder to a hidden browser, opens the
// paper stage with one scene, asks for every frame in turn (30 a second) and hands the frames to
// ffmpeg, which writes a silent video. It can instead write a few single frames as pictures, for
// checking a moment without filming the whole scene, or just report the scene's length and where
// its pages end.
//
// Use (from anywhere; SCENE is a file name in paper-film/scenes without .js):
//   node render-paper-film.mjs SCENE OUTPUT.mp4                    whole scene, silent video
//   node render-paper-film.mjs SCENE OUTPUT.mp4 --frames 600 1200  only frames 600 to 1199 (a chunk;
//                                                                  chunks are joined afterwards)
//   node render-paper-film.mjs SCENE OUTPUT_FOLDER --stills 57.5 66.0 ...   pictures of those moments
//   node render-paper-film.mjs SCENE --info                        prints the scene's start, end,
//                                                                  frame count and page edges (JSON)
//   node render-paper-film.mjs SCENE --camera OUTPUT.json [STEP]   writes where the camera is every
//                                                                  STEP frames (default 3) without
//                                                                  drawing, for tools/camera_audit.py
// Times are seconds on the chapter timeline; frame 0 is the scene's start.
//
// The hidden browser is Chromium, found by find-browser.mjs: the PAPER_FILM_BROWSER setting (a path
// to the browser program), Playwright's own downloaded Chromium, then the usual install places.
// --stills takes times separated by spaces or commas (57.5 66 or 57.5,66); anything that is not a
// number stops the run before the browser opens (plugin kit; the film kit's copy reads "57.5,66" as one
// time that is not a number, NaN, and still goes on to draw it).
// Filming speed on a 2-processor machine with software graphics: about 0.6 to 0.9 seconds a frame
// for the paper stage. A cinema chapter (a scene that calls buildCinemaChapter) opens the cinema
// stage instead (cinema-stage.html); PAPER_FILM_STAGE can force one or the other. PAPER_FILM_QUERY adds
// settings to the stage's address (model-preview.js reads its model and camera from there).
// PAPER_FILM_CHAPTER and PAPER_FILM_PAGES choose the chapter and pages cinema-test-pages draws
// (PAPER_FILM_CHAPTER=my-chapter PAPER_FILM_PAGES=3,4); without PAPER_FILM_CHAPTER it draws chapter 2.

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright-core';
import { findBrowser } from './find-browser.mjs';

const KIT_FOLDER = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const FRAMES_PER_SECOND = 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2' };

function serveKit() {
  const server = http.createServer((request, response) => {
    const relative = decodeURIComponent(new URL(request.url, 'http://x').pathname);
    if (relative === '/favicon.ico') { response.writeHead(204); response.end(); return; }
    const file = path.join(KIT_FOLDER, relative);
    if (!file.startsWith(KIT_FOLDER) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] ?? 'application/octet-stream' });
    fs.createReadStream(file).pipe(response);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function openStage(sceneName) {
  const server = await serveKit();
  // software graphics (SwiftShader), so it works on machines without a graphics card
  const browser = await chromium.launch({ executablePath: findBrowser(), args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', (message) => { if (message.type() === 'error' || message.type() === 'warning') console.log('[stage]', message.text()); });
  page.on('pageerror', (error) => console.log('[stage error]', error.message));
  // a cinema chapter (scenes/<name>.js marked as one) uses the cinema stage; others the paper stage
  const stageName = process.env.PAPER_FILM_STAGE ?? (fs.readFileSync(path.join(KIT_FOLDER, 'paper-film/scenes', `${sceneName}.js`), 'utf8').includes('buildCinemaChapter') ? 'cinema-stage' : 'paper-stage');
  await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/${stageName}.html?scene=${sceneName}${process.env.PAPER_FILM_CHAPTER ? `&chapter=${process.env.PAPER_FILM_CHAPTER}` : ''}${process.env.PAPER_FILM_PAGES ? `&pages=${process.env.PAPER_FILM_PAGES}` : ''}${process.env.PAPER_FILM_QUERY ? `&${process.env.PAPER_FILM_QUERY}` : ''}`);
  await page.waitForFunction('window.stageReady === true || window.stageFailed', null, { timeout: 300000 });
  const failed = await page.evaluate(() => window.stageFailed);
  if (failed) throw new Error(`the scene did not load: ${failed}`);
  const info = await page.evaluate(() => window.sceneInfo);
  return { server, browser, page, info };
}

const frameBytes = (dataUrl) => Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');

async function main() {
  const [sceneName, output, ...rest] = process.argv.slice(2);
  if (!sceneName) { console.log('Use: node render-paper-film.mjs SCENE OUTPUT.mp4 | SCENE FOLDER --stills t1 t2 | SCENE --info'); process.exit(1); }
  // still times: spaces or commas between them; refuse anything that isn't a number before opening the browser
  const stillTimes = rest[0] === '--stills' ? rest.slice(1).flatMap((text) => text.split(',')).filter((text) => text.trim() !== '').map((text) => ({ text, time: Number(text) })) : [];
  const badTimes = stillTimes.filter(({ time }) => !Number.isFinite(time)).map(({ text }) => `"${text}"`);
  if (rest[0] === '--stills' && (badTimes.length || !stillTimes.length)) {
    console.error(badTimes.length ? `--stills: not a time in seconds: ${badTimes.join(', ')}` : '--stills: give at least one time in seconds');
    process.exit(2);
  }
  const { server, browser, page, info } = await openStage(sceneName);
  try {
    const frameCount = Math.round((info.end - info.start) * FRAMES_PER_SECOND);
    if (output === '--info') {
      const pageEdges = (info.pageEdges ?? []).map((seconds) => Math.round((seconds - info.start) * FRAMES_PER_SECOND));
      console.log(JSON.stringify({ scene: sceneName, start: info.start, end: info.end, frames: frameCount, page_edge_frames: pageEdges }));
      return;
    }
    if (output === '--camera') {
      const file = rest[0] ?? `${sceneName}-camera.json`, step = Number(rest[1] ?? 3);
      const samples = [];
      for (let frame = 0; frame < frameCount; frame += step) {
        await page.evaluate((t) => window.prepareFrame?.(t), info.start + frame / FRAMES_PER_SECOND);
        samples.push(await page.evaluate((t) => window.built.cameraAt?.(t), info.start + frame / FRAMES_PER_SECOND));
      }
      const plans = await page.evaluate(() => window.built.cameraPlans?.() ?? []);
      fs.writeFileSync(file, JSON.stringify({ scene: sceneName, fps: FRAMES_PER_SECOND, step, page_edges: info.pageEdges ?? [], samples, plans }));
      console.log(`wrote ${file}: ${samples.length} camera samples`);
      return;
    }
    if (rest[0] === '--stills') {
      fs.mkdirSync(output, { recursive: true });
      for (const { time } of stillTimes) {
        const started = Date.now();
        await page.evaluate((t) => window.prepareFrame?.(t), time);
        const dataUrl = await page.evaluate((t) => window.renderFrame(t), time);
        const file = path.join(output, `still-${time.toFixed(2)}.jpg`);
        fs.writeFileSync(file, frameBytes(dataUrl));
        console.log(`${file} (${Date.now() - started} ms)`);
      }
      return;
    }
    const firstFrame = rest[0] === '--frames' ? Number(rest[1]) : 0;
    const lastFrame = rest[0] === '--frames' ? Math.min(frameCount, Number(rest[2])) : frameCount;
    console.log(`scene ${sceneName}: ${info.start.toFixed(3)} s to ${info.end.toFixed(3)} s, ${frameCount} frames; drawing ${firstFrame} to ${lastFrame - 1}`);
    const encoder = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FRAMES_PER_SECOND),
      '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    const started = Date.now();
    // a chunk starts a few frames early, without keeping them, so dust and smoke are already in place
    for (let frame = Math.max(0, firstFrame - 3); frame < firstFrame; frame++) {
      await page.evaluate((t) => window.prepareFrame?.(t), info.start + frame / FRAMES_PER_SECOND);
      await page.evaluate((t) => window.renderFrame(t), info.start + frame / FRAMES_PER_SECOND);
    }
    for (let frame = firstFrame; frame < lastFrame; frame++) {
      const time = info.start + frame / FRAMES_PER_SECOND;
      await page.evaluate((t) => window.prepareFrame?.(t), time);   // a lazy chapter builds a page the first time it shows
      const dataUrl = await page.evaluate((t) => window.renderFrame(t), time);
      if (!encoder.stdin.write(frameBytes(dataUrl))) await new Promise((resolve) => encoder.stdin.once('drain', resolve));
      const done = frame - firstFrame + 1;
      if (done % 60 === 0) console.log(`frame ${frame}/${frameCount}, ${((Date.now() - started) / done).toFixed(0)} ms a frame`);
    }
    encoder.stdin.end();
    await new Promise((resolve) => encoder.on('close', resolve));
    fs.writeFileSync(output.replace(/\.mp4$/, '.json'), JSON.stringify({ scene: sceneName, start: info.start, end: info.end, frames: frameCount, first_frame: firstFrame, last_frame: lastFrame - 1, fps: FRAMES_PER_SECOND }, null, 1));
    console.log(`wrote ${output} in ${((Date.now() - started) / 1000).toFixed(0)} s`);
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((error) => { console.error(error); process.exit(1); });
