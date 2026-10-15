// What this does: the flat graphics drawn on top of a cinema page, like the titles and figures in a
// documentary: a place and year title with a thin rule ("BRITAIN · 1915"), big figures that count
// up, plain word hooks, labels with a line pointing at something in the picture, and charts whose
// line draws itself. They are drawn on a transparent 1080 x 1920 canvas each frame (a page's
// draw2D(context, t)), so they stay crisp; the finishing step lays them over the picture and adds
// the same grain, so they sit in the film rather than on it.
// At the end: the words of the redesigned chapter 2 for newcomers (log 34): plain heavy words in the top band that
// build on spoken words, rule cards, the guess ring, small name tags, a price arrow and a small pointer.
//
// Every function takes the moment t and its own times (at, until), and draws nothing outside them.
// Positions are in pixels: x from the left, y from the top. Phone apps cover roughly the bottom 380
// pixels and the right 140 pixels with their own buttons, so keep important words out of there.

import { clamp01 } from './cinema-kit.js';

export const INK = {
  paper: '#f2ede3', amber: '#e8a33d', red: '#d0503a', teal: '#7fb7b2', muted: 'rgba(242,237,227,0.62)', shadow: 'rgba(0,0,0,0.55)',
};
const easeOut = (x) => 1 - (1 - clamp01(x)) ** 3;
const easeInOut = (x) => { x = clamp01(x); return x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2; };

// how visible something is at t: fades in over `fadeIn` from `at`, out over `fadeOut` before `until`
export function presence(t, at, until = Infinity, fadeIn = 0.3, fadeOut = 0.35) {
  if (t < at || t > until) return 0;
  return Math.min(clamp01((t - at) / fadeIn), clamp01((until - t) / fadeOut));
}

function withShadow(ctx, blur = 22, colour = INK.shadow) {
  ctx.shadowColor = colour; ctx.shadowBlur = blur; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 3;
}
function noShadow(ctx) { ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0; }
function spaced(ctx, text, x, y, spacing, align = 'left') {
  const widths = [...text].map((c) => ctx.measureText(c).width);
  const total = widths.reduce((a, b) => a + b, 0) + spacing * (text.length - 1);
  let cursor = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  const saved = ctx.textAlign; ctx.textAlign = 'left';
  [...text].forEach((c, i) => { ctx.fillText(c, cursor, y); cursor += widths[i] + spacing; });
  ctx.textAlign = saved;
  return total;
}

// A place-and-year title: a thin amber rule draws across, then the words rise into place.
export function placeTitle(ctx, t, { at, until = at + 4, place, year, x = 84, y = 250, align = 'left', size = 46 }) {
  const a = presence(t, at, until, 0.01, 0.4);
  if (a <= 0) return false;
  const age = t - at;
  ctx.save();
  ctx.globalAlpha = a;
  const ruleLength = 150 * easeOut(age / 0.55);
  ctx.fillStyle = INK.amber;
  const ruleX = align === 'center' ? x - ruleLength / 2 : x;
  ctx.fillRect(ruleX, y, ruleLength, 4);
  const rise = 26 * (1 - easeOut((age - 0.15) / 0.6));
  ctx.globalAlpha = a * clamp01((age - 0.15) / 0.4);
  withShadow(ctx);
  ctx.fillStyle = INK.paper; ctx.font = `700 ${size}px Inter`; ctx.textBaseline = 'alphabetic';
  const placeWidth = spaced(ctx, place.toUpperCase(), x, y - 22 + rise, size * 0.16, align);
  if (year) {
    ctx.fillStyle = INK.amber; ctx.font = `800 ${size}px Inter`;
    const yearX = align === 'center' ? x + placeWidth / 2 + 24 : x + placeWidth + 24;
    if (align === 'center') { ctx.fillStyle = INK.amber; ctx.font = `600 ${size * 0.62}px Inter`; spaced(ctx, String(year), x, y + 58 - rise * 0.5, size * 0.2, 'center'); }
    else spaced(ctx, String(year), yearX, y - 22 + rise, size * 0.12);
  }
  ctx.restore();
  return true;
}

// A plain word hook (white, heavy), popping in with a small scale settle.
export function hook(ctx, t, { at, until = at + 3, text, x = 540, y = 420, size = 96, colour = INK.paper, align = 'center', lines }) {
  const a = presence(t, at, until, 0.12, 0.3);
  if (a <= 0) return false;
  const age = t - at;
  const scale = 1 + 0.18 * Math.exp(-age * 9) * Math.cos(age * 22);
  ctx.save();
  ctx.globalAlpha = a;
  ctx.translate(x, y); ctx.scale(scale, scale);
  withShadow(ctx, 26);
  ctx.fillStyle = colour; ctx.font = `800 ${size}px Inter`; ctx.textAlign = align; ctx.textBaseline = 'middle';
  const rows = lines ?? [text];
  rows.forEach((row, i) => ctx.fillText(row, 0, (i - (rows.length - 1) / 2) * size * 1.02));
  ctx.restore();
  return true;
}

// A figure that counts from `from` to `to` over `duration`, with a small caption under it.
export function counter(ctx, t, { at, until = at + 4, duration = 1.2, from = 0, to, format = (v) => v.toFixed(0), x = 540, y = 520, size = 150, colour = INK.paper, caption, captionColour = INK.muted, align = 'center' }) {
  const a = presence(t, at, until, 0.15, 0.35);
  if (a <= 0) return false;
  const k = easeInOut((t - at) / duration);
  const value = from + (to - from) * k;
  ctx.save();
  ctx.globalAlpha = a;
  withShadow(ctx, 26);
  ctx.fillStyle = colour; ctx.font = `800 ${size}px Inter`; ctx.textAlign = align; ctx.textBaseline = 'alphabetic';
  ctx.fillText(format(value), x, y);
  if (caption) {
    ctx.fillStyle = captionColour; ctx.font = `600 ${Math.round(size * 0.24)}px Inter`;
    spaced(ctx, caption.toUpperCase(), x, y + size * 0.42, size * 0.03, align);
  }
  ctx.restore();
  return true;
}

// A label with a thin line pointing at a spot in the picture (`point` in pixels, e.g. from
// kit.toScreen). The line draws out from the spot, then the words appear at its end.
// plate: true draws a dark rounded plate behind the words, so they read over pale walls or sky.
export function callout(ctx, t, { at, until = at + 3, point, text, dx = 160, dy = -120, size = 40, colour = INK.paper, accent = INK.amber, margin = 70, plate = false }) {
  const a = presence(t, at, until, 0.01, 0.3);
  if (a <= 0 || !point || point.behind) return false;
  const age = t - at;
  const k = easeOut(age / 0.45);
  ctx.save();
  ctx.font = `800 ${size}px Inter`;
  const labelWidth = ctx.measureText(text).width + 52;
  // keep the words inside the frame: flip to the other side if they would run off it
  let side = Math.sign(dx || 1);
  const endX = point.x + dx;
  if (side > 0 && endX + 40 + labelWidth > 1080 - margin) side = -1;
  if (side < 0 && endX - 40 - labelWidth < margin) side = 1;
  const reach = Math.abs(dx) * side;
  const endY = Math.min(1500, Math.max(150, point.y + dy));
  const end = { x: point.x + reach * k, y: point.y + (endY - point.y) * k };
  ctx.globalAlpha = a;
  withShadow(ctx, 12);
  ctx.strokeStyle = accent; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(point.x, point.y); ctx.lineTo(end.x, end.y); ctx.lineTo(end.x + side * 40 * k, end.y); ctx.stroke();
  ctx.fillStyle = accent; ctx.beginPath(); ctx.arc(point.x, point.y, 7, 0, Math.PI * 2); ctx.fill();
  ctx.globalAlpha = a * clamp01((age - 0.3) / 0.25);
  if (plate) {
    const textWidth = labelWidth - 52, padX = size * 0.45, padY = size * 0.32;
    const left = side > 0 ? end.x + side * 52 - padX : end.x + side * 52 - textWidth - padX;
    noShadow(ctx);
    ctx.fillStyle = 'rgba(12,16,18,0.72)';
    ctx.beginPath(); ctx.roundRect(left, end.y - size / 2 - padY, textWidth + 2 * padX, size + 2 * padY, size * 0.3); ctx.fill();
    withShadow(ctx, 12);
  }
  ctx.fillStyle = colour; ctx.textBaseline = 'middle';
  ctx.textAlign = side > 0 ? 'left' : 'right';
  ctx.fillText(text, end.x + side * 52, end.y);
  ctx.restore();
  return true;
}

// A line chart drawn over time. box: [x, y, width, height] in pixels; points: [[xValue, yValue]];
// xRange, yRange: [min, max]. The axis fades in, then the line draws from left to right over
// `drawFor` seconds with a glowing head. marks: [{ index, text, at }] labels on points.
export function lineChart(ctx, t, { at, until = Infinity, drawFor = 2, box, points, xRange, yRange, colour = INK.amber, width = 7,
  xLabels = [], yLabels = [], title, marks = [], baseline, panel = true, series = [] }) {
  const a = presence(t, at, until, 0.3, 0.4);
  if (a <= 0) return false;
  const [bx, by, bw, bh] = box;
  const px = (v) => bx + (v - xRange[0]) / (xRange[1] - xRange[0]) * bw;
  const py = (v) => by + bh - (v - yRange[0]) / (yRange[1] - yRange[0]) * bh;
  ctx.save();
  ctx.globalAlpha = a;
  if (panel) {
    const pad = 46;
    ctx.fillStyle = 'rgba(12,16,18,0.55)';
    ctx.beginPath(); ctx.roundRect(bx - pad - 30, by - pad - (title ? 70 : 0), bw + pad * 2 + 40, bh + pad * 2 + (title ? 70 : 0) + 40, 26); ctx.fill();
  }
  if (title) { ctx.fillStyle = INK.paper; ctx.font = '700 38px Inter'; ctx.textBaseline = 'alphabetic'; spaced(ctx, title.toUpperCase(), bx, by - 40, 4); }
  ctx.strokeStyle = 'rgba(242,237,227,0.35)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(bx, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.stroke();
  ctx.fillStyle = INK.muted; ctx.font = '600 30px Inter';
  for (const [v, label] of xLabels) { ctx.textAlign = 'center'; ctx.textBaseline = 'top'; ctx.fillText(label, px(v), by + bh + 14); }
  for (const [v, label] of yLabels) {
    ctx.strokeStyle = 'rgba(242,237,227,0.14)'; ctx.beginPath(); ctx.moveTo(bx, py(v)); ctx.lineTo(bx + bw, py(v)); ctx.stroke();
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle'; ctx.fillText(label, bx - 14, py(v));
  }
  if (baseline !== undefined) {
    ctx.setLineDash([10, 10]); ctx.strokeStyle = 'rgba(242,237,227,0.5)'; ctx.beginPath(); ctx.moveTo(bx, py(baseline)); ctx.lineTo(bx + bw, py(baseline)); ctx.stroke(); ctx.setLineDash([]);
  }
  const drawLine = (pts, lineColour, lineWidth, startAt, duration, head = true) => {
    const k = clamp01((t - startAt) / duration);
    if (k <= 0) return;
    const total = pts.length - 1;
    const upto = k * total;
    ctx.strokeStyle = lineColour; ctx.lineWidth = lineWidth; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    withShadow(ctx, 18, lineColour);
    ctx.beginPath(); ctx.moveTo(px(pts[0][0]), py(pts[0][1]));
    let headX = px(pts[0][0]), headY = py(pts[0][1]);
    for (let i = 1; i <= Math.ceil(upto) && i <= total; i++) {
      const f = Math.min(1, upto - (i - 1));
      headX = px(pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f); headY = py(pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f);
      ctx.lineTo(headX, headY);
    }
    ctx.stroke();
    if (head && k < 1) { ctx.fillStyle = '#fff6e0'; ctx.beginPath(); ctx.arc(headX, headY, lineWidth * 1.3, 0, Math.PI * 2); ctx.fill(); }
    noShadow(ctx);
  };
  drawLine(points, colour, width, at + 0.3, drawFor);
  for (const s of series) drawLine(s.points, s.colour, s.width ?? width, at + 0.3 + (s.delay ?? 0), s.drawFor ?? drawFor);
  for (const mark of marks) {
    const m = presence(t, mark.at, until, 0.2, 0.3);
    if (m <= 0) continue;
    const [xv, yv] = (mark.series ? series[mark.series - 1].points : points)[mark.index];
    ctx.globalAlpha = a * m;
    ctx.fillStyle = mark.colour ?? colour; ctx.beginPath(); ctx.arc(px(xv), py(yv), 11, 0, Math.PI * 2); ctx.fill();
    withShadow(ctx, 16);
    ctx.fillStyle = INK.paper; ctx.font = `800 ${mark.size ?? 46}px Inter`; ctx.textAlign = mark.align ?? 'center'; ctx.textBaseline = 'alphabetic';
    ctx.fillText(mark.text, px(xv) + (mark.dx ?? 0), py(yv) + (mark.dy ?? -26));
    noShadow(ctx);
  }
  ctx.restore();
  return true;
}

// A row of bars rising (values in the same unit), each with its label underneath and its value on top.
export function bars(ctx, t, { at, until = Infinity, box, values, labels = [], valueText = (v) => String(v), maxValue, colours = [INK.paper], rise = 0.8, stagger = 0.35, panel = true, title }) {
  const a = presence(t, at, until, 0.3, 0.4);
  if (a <= 0) return false;
  const [bx, by, bw, bh] = box;
  const max = maxValue ?? Math.max(...values);
  const slot = bw / values.length, barWidth = slot * 0.56;
  ctx.save(); ctx.globalAlpha = a;
  if (panel) { ctx.fillStyle = 'rgba(12,16,18,0.55)'; ctx.beginPath(); ctx.roundRect(bx - 40, by - (title ? 110 : 40), bw + 80, bh + (title ? 110 : 40) + 100, 26); ctx.fill(); }
  if (title) { ctx.fillStyle = INK.paper; ctx.font = '700 38px Inter'; ctx.textBaseline = 'alphabetic'; spaced(ctx, title.toUpperCase(), bx, by - 46, 4); }
  values.forEach((v, i) => {
    const k = easeOut((t - at - 0.2 - i * stagger) / rise);
    if (k <= 0) return;
    const h = bh * v / max * k, x = bx + i * slot + (slot - barWidth) / 2;
    ctx.fillStyle = colours[i % colours.length];
    withShadow(ctx, 14);
    ctx.fillRect(x, by + bh - h, barWidth, h);
    noShadow(ctx);
    ctx.fillStyle = INK.paper; ctx.font = '800 48px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.globalAlpha = a * clamp01(k * 2 - 1);
    ctx.fillText(valueText(v), x + barWidth / 2, by + bh - h - 16);
    ctx.globalAlpha = a;
    if (labels[i]) { ctx.fillStyle = INK.muted; ctx.font = '600 32px Inter'; ctx.textBaseline = 'top'; ctx.fillText(labels[i], x + barWidth / 2, by + bh + 16); }
  });
  ctx.restore();
  return true;
}

// A small attribution line (who said it), lower left, like a documentary source credit.
// plate: true puts the line on a soft dark plate in paper white (for busy or bright backgrounds)
export function credit(ctx, t, { at, until = at + 4, text, x = 84, y = 1440, size = 30, plate = false }) {
  const a = presence(t, at, until, 0.3, 0.4);
  if (a <= 0) return false;
  ctx.save(); ctx.globalAlpha = a * 0.9;
  ctx.font = `600 ${size}px Inter`; ctx.textBaseline = 'alphabetic';
  if (plate) {
    const width = ctx.measureText(text.toUpperCase()).width + 3 * text.length;
    ctx.fillStyle = 'rgba(12,14,18,0.74)';
    ctx.beginPath(); ctx.roundRect(x - 18, y - size * 0.95, width + 36, size * 1.5, 10); ctx.fill();
  }
  withShadow(ctx, 14);
  ctx.fillStyle = plate ? INK.paper : INK.muted;
  spaced(ctx, text.toUpperCase(), x, y, 3);
  ctx.restore();
  return true;
}

// A panel of 100 dots, ten by ten, for "about 3 in 100 out of work" (log 34): every dot lit (paper white), then,
// from `emptyAt`, the last `empty` dots go hollow one after another (a fraction empties the last one only in part:
// 0.4 leaves it 60% lit, for "fewer than one in a hundred"). `ghost` marks that many of the hollow dots, the
// earliest ones, with a dashed ring from `ghostAt` (for "up from about three": 3 of the nearly 6). Words: `heading`
// above, `caption` below (a figure Malina says); the dark panel widens to fit them.
export function dotPanel(ctx, t, { at, until = Infinity, x = 84, y = 300, spacing = 34, radius = 12, empty = 0, emptyAt = at + 0.6,
  emptyStep = 0.18, ghost = 0, ghostAt = emptyAt, heading, caption, captionAt = emptyAt, panel = true, colour = INK.paper, hollowColour = INK.amber }) {
  const a = presence(t, at, until, 0.3, 0.4);
  if (a <= 0) return false;
  const size = spacing * 10;
  ctx.save(); ctx.globalAlpha = a;
  if (panel) {
    ctx.font = '800 40px Inter';
    const captionWidth = caption ? ctx.measureText(caption.toUpperCase()).width + 2 * caption.length : 0;
    ctx.font = '700 34px Inter';
    const headingWidth = heading ? ctx.measureText(heading.toUpperCase()).width + 3 * heading.length : 0;
    const width = Math.max(size, captionWidth, headingWidth);
    ctx.fillStyle = 'rgba(12,16,18,0.55)';
    ctx.beginPath(); ctx.roundRect(x - 30, y - (heading ? 84 : 30), width + 60, size + (heading ? 84 : 30) + (caption ? 104 : 30), 22); ctx.fill();
  }
  if (heading) { ctx.fillStyle = INK.paper; ctx.font = '700 34px Inter'; ctx.textBaseline = 'alphabetic'; spaced(ctx, heading.toUpperCase(), x, y - 34, 3); }
  const whole = Math.ceil(empty);
  for (let i = 0; i < 100; i++) {
    const cx = x + (i % 10) * spacing + spacing / 2, cy = y + Math.floor(i / 10) * spacing + spacing / 2;
    const fromEnd = 99 - i;                       // 0 = the last dot
    let lit = 1;
    if (fromEnd < whole) {
      const k = easeOut((t - emptyAt - (whole - 1 - fromEnd) * emptyStep) / 0.3);
      const part = fromEnd === 0 && empty % 1 > 0 ? empty % 1 : 1;   // the last dot may empty only in part
      lit = 1 - k * part;
    }
    const isGhost = fromEnd < whole && fromEnd >= whole - ghost;   // the earliest hollow dots
    ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = colour; ctx.globalAlpha = a * lit; ctx.fill();
    if (lit < 1) { ctx.globalAlpha = a; ctx.lineWidth = 3; ctx.strokeStyle = hollowColour; ctx.stroke(); }
    if (isGhost) {
      const g = easeOut((t - ghostAt) / 0.5);
      if (g > 0) {
        ctx.beginPath(); ctx.arc(cx, cy, radius * 0.55, 0, Math.PI * 2);
        ctx.globalAlpha = a * 0.85 * g; ctx.lineWidth = 2.5; ctx.setLineDash([4, 3]); ctx.strokeStyle = INK.paper; ctx.stroke(); ctx.setLineDash([]);
      }
    }
  }
  ctx.globalAlpha = a;
  if (caption) {
    ctx.globalAlpha = a * clamp01((t - captionAt) / 0.3);
    ctx.fillStyle = INK.paper; ctx.font = '800 40px Inter'; ctx.textBaseline = 'top';
    withShadow(ctx, 14);
    spaced(ctx, caption.toUpperCase(), x, y + size + 22, 2);
  }
  ctx.restore();
  return true;
}

// ------------------------------------------------------------------------ words for chapter 2 for newcomers (log 34)
// The redesigned chapter's words on screen (plan 34, part 2): plain heavy type in the top band (about 0.05 to 0.22 of
// the frame's height down), left-aligned from 0.06 across and never past 0.90 across (TEXT_LEFT, TEXT_RIGHT), clear
// of the phone's own buttons; a soft dark band behind words that cross the sky, smoke or a chimney; rule cards stacked
// over that band; the guess ring; small name tags over the two factories; a price arrow over a factory.
// The type (Inter) has no arrow sign, so a part of the words that starts with '→' gets a drawn arrow instead.
export const TEXT_LEFT = 65;     // 0.06 of the frame's width
export const TEXT_RIGHT = 972;   // 0.90 of the frame's width

// A soft dark band from the top of the frame down to `bottom` (pixels), strongest at the top; `amount` 0 to 1.
export function topShade(ctx, amount, { bottom = 470, strength = 0.62 } = {}) {
  if (amount <= 0) return;
  ctx.save();
  const g = ctx.createLinearGradient(0, 0, 0, bottom);
  g.addColorStop(0, `rgba(5,8,12,${strength * amount})`);
  g.addColorStop(0.7, `rgba(5,8,12,${0.55 * strength * amount})`);
  g.addColorStop(1, 'rgba(5,8,12,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 1080, bottom);
  ctx.restore();
}

// A drawn arrow sign the size of a letter of `size` pixels, its left end at x, centred on the middle of the letters
// at baseline y; returns its width.
function arrowSign(ctx, x, y, size, colour) {
  const width = size * 0.9, middle = y - size * 0.36, head = size * 0.3;
  ctx.save();
  ctx.strokeStyle = colour; ctx.fillStyle = colour; ctx.lineWidth = Math.max(3, size * 0.12); ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x + size * 0.05, middle); ctx.lineTo(x + width - head * 0.6, middle); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x + width, middle); ctx.lineTo(x + width - head * 1.1, middle - head); ctx.lineTo(x + width - head * 1.1, middle + head); ctx.closePath(); ctx.fill();
  ctx.restore();
  return width;
}

// How wide a part of words is at `size` (a leading '→' counts as the drawn arrow and a space).
function partWidth(ctx, text, size) {
  if (!text.startsWith('→')) return ctx.measureText(text).width;
  return size * 0.9 + ctx.measureText(text.slice(1)).width;
}

// Words that build part by part on spoken words: parts [{ text, at, colour? }], each popping in at its own moment
// (a part with no `at` comes with the first). The parts run left to right from x on baseline y; a part that would
// pass `right` starts a new line under the first. If one part alone is wider than the room, every part shrinks to fit.
// Everything fades out at `until`. Returns the drawn box { left, top, right, bottom } (null when nothing shows),
// for lines and arrows to start from.
export function buildWords(ctx, t, { parts, until = Infinity, x = TEXT_LEFT, y, size = 52, right = TEXT_RIGHT, colour = INK.paper,
  lineGap = 1.22, weight = 800, shadow = true, fadeOut = 0.3 }) {
  const first = parts.find((p) => p.at !== undefined)?.at ?? 0;
  if (t < first || t > until) return null;
  ctx.save();
  ctx.font = `${weight} ${size}px Inter`;
  const space = ctx.measureText(' ').width;
  const widest = Math.max(...parts.map((p) => partWidth(ctx, p.text, size)));
  const scale = Math.min(1, (right - x) / Math.max(1, widest));
  const fontSize = size * scale;
  ctx.font = `${weight} ${fontSize}px Inter`;
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  let cursor = x, line = 0, box = null;
  for (const part of parts) {
    const width = partWidth(ctx, part.text, fontSize);
    if (cursor > x && cursor + width > right) { cursor = x; line++; }
    const partAt = part.at ?? first;
    const a = presence(t, partAt, until, 0.14, fadeOut);
    const baseline = y + line * fontSize * lineGap;
    if (a > 0) {
      const age = t - partAt;
      const rise = 10 * (1 - easeOut(age / 0.25));
      ctx.globalAlpha = a;
      if (shadow) withShadow(ctx, 18); else noShadow(ctx);
      const ink = part.colour ?? colour;
      ctx.fillStyle = ink;
      let left = cursor;
      if (part.text.startsWith('→')) { left += arrowSign(ctx, cursor, baseline + rise, fontSize, ink) + space * 0.6; ctx.fillText(part.text.slice(1).trimStart(), left, baseline + rise); }
      else ctx.fillText(part.text, cursor, baseline + rise);
      box = box ?? { left: x, top: baseline - fontSize * 0.78, right: cursor + width, bottom: baseline + fontSize * 0.22 };
      box.right = Math.max(box.right, cursor + width);
      box.bottom = Math.max(box.bottom, baseline + fontSize * 0.22);
    }
    cursor += width + space;
  }
  ctx.restore();
  return box;
}

// A rule card (page 5 and page 16, the same on both): a soft dark plate filling `box` [x, y, width, height] in pixels,
// with words that build part by part (buildWords, from the plate's left inner edge), and an optional thin line from
// the plate to a spot in the picture: line { at, from: [x, y] on the plate's edge, to: { x, y } (kit.toScreen), via:
// [[x, y], ...] corners on the way, so the line can go round another card }. The plate appears with its first part.
export function ruleCard(ctx, t, { at, until = Infinity, box, parts, size = 50, line = null, plate = 'rgba(10,13,17,0.66)', accent = INK.amber }) {
  const a = presence(t, at, until, 0.25, 0.35);
  if (a <= 0) return false;
  const [bx, by, bw, bh] = box;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.fillStyle = plate;
  ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 18); ctx.fill();
  ctx.fillStyle = accent; ctx.fillRect(bx, by + 16, 6, bh - 32);   // a thin amber rule down its left edge
  ctx.restore();
  buildWords(ctx, t, { parts, until, x: bx + 30, y: by + size * 1.12, size, right: bx + bw - 24, lineGap: 1.18 });
  if (line && line.to && !line.to.behind) {
    const k = easeOut((t - line.at) / 0.5);
    if (k > 0 && t <= until) {
      const points = [line.from, ...(line.via ?? []), [line.to.x, line.to.y]];
      const lengths = points.slice(1).map((p, i) => Math.hypot(p[0] - points[i][0], p[1] - points[i][1]));
      let left = k * lengths.reduce((s, v) => s + v, 0);
      ctx.save();
      ctx.globalAlpha = a;
      withShadow(ctx, 8);
      ctx.strokeStyle = accent; ctx.lineWidth = 3; ctx.lineJoin = 'round';
      ctx.beginPath(); ctx.moveTo(...points[0]);
      let end = points[0];
      for (let i = 1; i < points.length && left > 0; i++) {
        const step = Math.min(1, left / Math.max(1e-6, lengths[i - 1]));
        end = [points[i - 1][0] + (points[i][0] - points[i - 1][0]) * step, points[i - 1][1] + (points[i][1] - points[i - 1][1]) * step];
        ctx.lineTo(...end);
        left -= lengths[i - 1];
      }
      ctx.stroke();
      ctx.fillStyle = accent;
      ctx.beginPath(); ctx.arc(...points[0], 6, 0, Math.PI * 2); ctx.fill();
      if (k >= 1) { ctx.beginPath(); ctx.arc(line.to.x, line.to.y, 8, 0, Math.PI * 2); ctx.fill(); }
      ctx.restore();
    }
  }
  return true;
}

// The guess ring: a thin circle at (x, y) whose amber arc fills clockwise from the top over `length` seconds from
// `at` (the time to have a guess), then stays full.
export function guessRing(ctx, t, { at, until = Infinity, length = 4, x, y, radius = 24, width = 7, colour = INK.amber }) {
  const a = presence(t, at, until, 0.2, 0.3);
  if (a <= 0) return false;
  const k = clamp01((t - at) / length);
  ctx.save();
  ctx.globalAlpha = a;
  withShadow(ctx, 10);
  ctx.lineWidth = width; ctx.lineCap = 'round';
  ctx.strokeStyle = 'rgba(242,237,227,0.32)';
  ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.stroke();
  if (k > 0) {
    ctx.strokeStyle = colour;
    ctx.beginPath(); ctx.arc(x, y, radius, -Math.PI / 2, -Math.PI / 2 + k * Math.PI * 2); ctx.stroke();
  }
  ctx.restore();
  return true;
}

// A small name tag over a column of the picture (QUIET, FLAT OUT): small heavy words on a dark rounded plate centred
// on x, its bottom at y, with a short tick under it pointing down at the column.
export function nameTag(ctx, t, { at, until = Infinity, text, x, y, size = 34, accent = INK.amber }) {
  const a = presence(t, at, until, 0.25, 0.3);
  if (a <= 0) return false;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.font = `800 ${size}px Inter`;
  const letters = [...text];
  const spacing = size * 0.08;
  const width = letters.reduce((s, c) => s + ctx.measureText(c).width, 0) + spacing * (letters.length - 1);
  const padX = size * 0.5, height = size * 1.55;
  const left = Math.max(TEXT_LEFT, Math.min(TEXT_RIGHT - width - 2 * padX, x - width / 2 - padX));
  ctx.fillStyle = 'rgba(10,13,17,0.72)';
  ctx.beginPath(); ctx.roundRect(left, y - height, width + 2 * padX, height, height / 2); ctx.fill();
  ctx.strokeStyle = accent; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + size * 0.6); ctx.stroke();
  ctx.fillStyle = INK.paper; ctx.textBaseline = 'middle';
  spaced(ctx, text, left + padX, y - height / 2 + size * 0.04, spacing);
  ctx.restore();
  return true;
}

// A price arrow drawn over the picture: it draws itself from `from` ({ x, y } in pixels) for `length` pixels at
// `angle` degrees (0 = level, 30 = climbing) over `drawFor` seconds, with a head, and an optional small word at its
// tail (PRICES).
export function priceArrow(ctx, t, { at, until = Infinity, from, length = 300, angle = 0, drawFor = 0.9, colour = INK.amber, width = 10, word = null, size = 30 }) {
  const a = presence(t, at, until, 0.01, 0.3);
  if (a <= 0 || !from) return false;
  const k = easeInOut((t - at) / drawFor);
  const radians = -angle * Math.PI / 180;
  const end = { x: from.x + Math.cos(radians) * length * k, y: from.y + Math.sin(radians) * length * k };
  ctx.save();
  ctx.globalAlpha = a;
  withShadow(ctx, 14);
  ctx.strokeStyle = colour; ctx.fillStyle = colour; ctx.lineWidth = width; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(end.x, end.y); ctx.stroke();
  if (k > 0.05) {
    const head = width * 2.6;
    ctx.save();
    ctx.translate(end.x, end.y); ctx.rotate(radians);
    ctx.beginPath(); ctx.moveTo(head * 0.6, 0); ctx.lineTo(-head * 0.9, -head); ctx.lineTo(-head * 0.9, head); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  if (word) {
    ctx.globalAlpha = a * clamp01((t - at) / 0.3);
    ctx.fillStyle = INK.paper; ctx.font = `800 ${size}px Inter`; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
    ctx.fillText(word, from.x, from.y - width - 6);
  }
  ctx.restore();
  return true;
}

// A small arrow pointing at a spot in the picture (NEW MONEY SPENT going into a gate): a thin line from `from` to
// `to` (pixels) that draws itself, with a head at `to`.
export function pointer(ctx, t, { at, until = Infinity, from, to, colour = INK.amber, width = 4, drawFor = 0.45 }) {
  const a = presence(t, at, until, 0.01, 0.3);
  if (a <= 0 || !from || !to || to.behind) return false;
  const k = easeOut((t - at) / drawFor);
  const end = { x: from.x + (to.x - from.x) * k, y: from.y + (to.y - from.y) * k };
  const direction = Math.atan2(to.y - from.y, to.x - from.x);
  ctx.save();
  ctx.globalAlpha = a;
  withShadow(ctx, 10);
  ctx.strokeStyle = colour; ctx.fillStyle = colour; ctx.lineWidth = width; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(end.x, end.y); ctx.stroke();
  const head = width * 4;
  ctx.translate(end.x, end.y); ctx.rotate(direction);
  ctx.beginPath(); ctx.moveTo(head * 0.5, 0); ctx.lineTo(-head, -head * 0.7); ctx.lineTo(-head, head * 0.7); ctx.closePath(); ctx.fill();
  ctx.restore();
  return true;
}
