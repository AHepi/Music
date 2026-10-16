// What this does: finds the Chromium program the kit's tools draw with (render-paper-film.mjs,
// profile_frame.mjs), so every tool looks in the same places in the same order:
//   1. the PAPER_FILM_BROWSER setting (a path to a Chromium or Chrome program; explainer-film-setup
//      writes it into machine-settings.env when it finds one),
//   2. Playwright's separate "headless shell" build (newer full Chromium builds no longer run in the old
//      headless mode Playwright uses here), in /opt/pw-browsers or ~/.cache/ms-playwright,
//   3. Playwright's own Chromium, then a full Chromium in those folders,
//   4. the usual install places.
// Use (in a tool): import { findBrowser } from './find-browser.mjs'; chromium.launch({ executablePath: findBrowser(), ... })
// It throws a plain message if nothing is found.
// (Plugin kit only: the film kit keeps this function inside render-paper-film.mjs.)

import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

export function findBrowser() {
  const candidates = [process.env.PAPER_FILM_BROWSER];
  const roots = ['/opt/pw-browsers', path.join(process.env.HOME ?? '', '.cache/ms-playwright')];
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    for (const folder of fs.readdirSync(root).filter((name) => name.startsWith('chromium_headless_shell')).sort().reverse()) {
      candidates.push(path.join(root, folder, 'chrome-linux/headless_shell'), path.join(root, folder, 'chrome-headless-shell-linux64/chrome-headless-shell'));
    }
  }
  try { candidates.push(chromium.executablePath()); } catch { /* Playwright has no browser of its own here */ }
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    for (const folder of fs.readdirSync(root).filter((name) => name.startsWith('chromium')).sort().reverse()) {
      candidates.push(path.join(root, folder, 'chrome-linux64/chrome'), path.join(root, folder, 'chrome-linux/chrome'));
    }
  }
  candidates.push('/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'C:/Program Files/Google/Chrome/Application/chrome.exe');
  const found = candidates.find((candidate) => candidate && fs.existsSync(candidate));
  if (!found) throw new Error('No Chromium found. Set PAPER_FILM_BROWSER to the path of a Chromium or Chrome program (or run explainer-film-setup).');
  return found;
}
