// What this does: a stand-in for a page of chapter 2 for newcomers that isn't built yet (log 34): a dark card with
// the page's name and its narration shown word by word as Malina says it, on the chapter's timeline. It lets the
// whole chapter be timed and filmed end to end while the real pages (built-and-painted sets) are still being made.
// Every real page replaces it in ../inflation-chapter-2-newcomers.js.
import { clamp01 } from '../cinema-kit.js';
import { INK } from '../graphics.js';

export const join = { kind: 'dissolve', after: 0.3, length: 0.5 };

export async function build(kit) {
  const camera = kit.stillShot({ position: [0, 1.6, 6], target: [0, 1.6, 0], fov: 40 }, [], { name: 'stand-in' });
  kit.scene.background.set(0x14181c);
  const lines = [];
  let line = [];
  for (const word of kit.words) {
    line.push(word);
    if (line.length >= 5 || /[.?!]$/.test(word.text)) { lines.push(line); line = []; }
  }
  if (line.length) lines.push(line);
  return {
    pose: (t) => ({ camera: camera(t), still: true, look: { exposure: 1, aperture: 0, grain: 0 } }),
    draw2D(ctx, t) {
      ctx.fillStyle = INK.muted; ctx.font = '700 40px Inter'; ctx.textBaseline = 'alphabetic';
      ctx.fillText(`PAGE ${kit.number} (STAND-IN)`, 84, 200);
      const current = lines.findIndex((l) => t < l[l.length - 1].end + 0.4);
      const shown = lines.slice(Math.max(0, current - 3), current + 1);
      shown.forEach((l, row) => {
        let x = 84;
        ctx.font = '800 54px Inter';
        for (const w of l) {
          const said = clamp01((t - w.start) / 0.12);
          ctx.fillStyle = said > 0 ? INK.paper : 'rgba(242,237,227,0.25)';
          ctx.fillText(w.text, x, 820 + row * 86);
          x += ctx.measureText(w.text + ' ').width;
        }
      });
      return true;
    },
  };
}
