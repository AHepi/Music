import { chromium } from 'playwright-core';
const exe = '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const browser = await chromium.launch({ executablePath: exe, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.setContent('<canvas id=c width=1080 height=1920></canvas>');
const info = await page.evaluate(() => {
  const gl = document.getElementById('c').getContext('webgl2');
  if (!gl) return 'no webgl2';
  const d = gl.getExtension('WEBGL_debug_renderer_info');
  return { renderer: d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), maxTex: gl.getParameter(gl.MAX_TEXTURE_SIZE) };
});
console.log(info);
await browser.close();
