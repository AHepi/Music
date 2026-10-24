// What this does: the flat graphics drawn on top of a cinema page, like the titles and figures in a
// documentary: a place and year title with a thin rule ("BRITAIN · 1915"), big figures that count
// up, plain word hooks, labels with a line pointing at something in the picture, and charts whose
// line draws itself. They are drawn on a transparent 1080 x 1920 canvas each frame (a page's
// draw2D(context, t)), so they stay crisp; the finishing step lays them over the picture and adds
// the same grain, so they sit in the film rather than on it.
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
export function credit(ctx, t, { at, until = at + 4, text, x = 84, y = 1440, size = 30 }) {
  const a = presence(t, at, until, 0.3, 0.4);
  if (a <= 0) return false;
  ctx.save(); ctx.globalAlpha = a * 0.9; withShadow(ctx, 14);
  ctx.fillStyle = INK.muted; ctx.font = `600 ${size}px Inter`; ctx.textBaseline = 'alphabetic';
  spaced(ctx, text.toUpperCase(), x, y, 3);
  ctx.restore();
  return true;
}
