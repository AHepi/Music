// Reads a public page in hidden Chromium and saves its visible text. Usage: node read.mjs URL WAIT OUTFILE
import { chromium } from 'playwright-core';
import fs from 'fs';
const [url, wait = '8', outfile] = process.argv.slice(2);
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  headless: true,
  proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined,
  args: ['--headless=new', '--disable-blink-features=AutomationControlled'],
});
const ctx = await browser.newContext({
  userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
  viewport: { width: 1366, height: 900 }, locale: 'en-US', ignoreHTTPSErrors: false,
});
const page = await ctx.newPage();
try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }); } catch (e) { console.error('GOTO', e.message); }
await page.waitForTimeout(Number(wait) * 1000);
for (let i = 0; i < 8; i++) { await page.mouse.wheel(0, 2500); await page.waitForTimeout(400); }
const text = await page.evaluate(() => document.body ? document.body.innerText : '');
fs.writeFileSync(outfile, `TITLE: ${await page.title()}\nURL: ${page.url()}\n\n${text}`);
console.log('saved', outfile, text.length);
await browser.close();
