// What this does: films a paper scene. It serves the project folder to a hidden browser, opens the
// paper stage with one scene, asks for every frame in turn (30 a second) and hands the frames to
// ffmpeg, which writes a silent video. It can instead write a few single frames as pictures, for
// checking a moment without filming the whole scene.
//
// Use:
//   node render-paper-film.mjs SCENE OUTPUT.mp4                    whole scene, silent video
//   node render-paper-film.mjs SCENE OUTPUT.mp4 --frames 600 1200  only frames 600 to 1199 (a chunk;
//                                                                  chunks are joined afterwards)
//   node render-paper-film.mjs SCENE OUTPUT_FOLDER --stills 57.5 66.0 ...   pictures of those moments
// (SCENE is a file name in paper-film/scenes without .js; times are seconds on the chapter timeline;
// frame 0 is the scene's start)

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright-core';

const PROJECT_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const BROWSER = '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const FRAMES_PER_SECOND = 30;
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

async function openStage(sceneName) {
  const server = await serveProject();
  const browser = await chromium.launch({ executablePath: BROWSER, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', (message) => { if (message.type() === 'error' || message.type() === 'warning') console.log('[stage]', message.text()); });
  page.on('pageerror', (error) => console.log('[stage error]', error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/paper-film/stage/paper-stage.html?scene=${sceneName}`);
  await page.waitForFunction('window.stageReady === true', null, { timeout: 180000 });
  const info = await page.evaluate(() => window.sceneInfo);
  return { server, browser, page, info };
}

const frameBytes = (dataUrl) => Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');

async function main() {
  const [sceneName, output, ...rest] = process.argv.slice(2);
  const { server, browser, page, info } = await openStage(sceneName);
  try {
    if (rest[0] === '--stills') {
      fs.mkdirSync(output, { recursive: true });
      for (const time of rest.slice(1).map(Number)) {
        const started = Date.now();
        const dataUrl = await page.evaluate((t) => window.renderFrame(t), time);
        const file = path.join(output, `still-${time.toFixed(2)}.jpg`);
        fs.writeFileSync(file, frameBytes(dataUrl));
        console.log(`${file} (${Date.now() - started} ms)`);
      }
      return;
    }
    const frameCount = Math.round((info.end - info.start) * FRAMES_PER_SECOND);
    const firstFrame = rest[0] === '--frames' ? Number(rest[1]) : 0;
    const lastFrame = rest[0] === '--frames' ? Math.min(frameCount, Number(rest[2])) : frameCount;
    console.log(`scene ${sceneName}: ${info.start.toFixed(3)} s to ${info.end.toFixed(3)} s, ${frameCount} frames; drawing ${firstFrame} to ${lastFrame - 1}`);
    const encoder = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FRAMES_PER_SECOND),
      '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    const started = Date.now();
    // a chunk starts a little early, without keeping those frames, so anything that depends on the
    // frames before it (nothing should, but dust and smoke settle) is in place
    for (let frame = Math.max(0, firstFrame - 3); frame < firstFrame; frame++) await page.evaluate((t) => window.renderFrame(t), info.start + frame / FRAMES_PER_SECOND);
    for (let frame = firstFrame; frame < lastFrame; frame++) {
      const time = info.start + frame / FRAMES_PER_SECOND;
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
