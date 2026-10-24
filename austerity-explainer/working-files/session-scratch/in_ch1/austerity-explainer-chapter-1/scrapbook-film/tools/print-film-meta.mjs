// What this does: loads a film's description (like the skill's captions tool does) and prints its
// declared rests, how much of the chapter they cover, and the first and last captions.
import { filmMeta } from "/home/claude/austerity-explainer/film/tools/captions.mjs";
const meta = await filmMeta(process.argv[2]);
const holds = meta.holds ?? [];
const held = holds.reduce((total, [a, b]) => total + (b - a), 0);
console.log(`frames: ${meta.durationFrames} (${(meta.durationFrames / meta.fps).toFixed(2)} s), kind ${meta.kind}, poster ${meta.poster}`);
console.log(`rests: ${holds.length}, covering ${held} frames (${(held / meta.fps).toFixed(1)} s, ${(100 * held / meta.durationFrames).toFixed(1)}% of the chapter)`);
const longest = [...holds].sort((x, y) => (y[1] - y[0]) - (x[1] - x[0])).slice(0, 8);
console.log("longest rests:", longest.map(([a, b, r]) => `${(a / 30).toFixed(1)}-${(b / 30).toFixed(1)}s (${((b - a) / 30).toFixed(1)}s)`).join(", "));
console.log(`captions: ${meta.captions.length}`);
for (const c of [...meta.captions.slice(0, 6), ...meta.captions.slice(-4)]) console.log(`  ${(c.from / 30).toFixed(2)}-${(c.to / 30).toFixed(2)}  ${c.text}`);
