// What this does: reads the stretches the motion check flagged (as "from-to" frame ranges) and says,
// for each, which page it is on, what is being drawn there (by mark name), and how long it lasts,
// so a flagged stretch can be judged: a rest the narration needs, a fine mark too small for the
// check to see, or a real gap.
//   node tools/explain-motion-report.mjs 616-646 1020-1051 ...
import { build } from "esbuild";
import { overlay } from "./overlay.mjs";

const js = (await build({ stdin: { contents: `export { austerityChapterOne as film, activeStepsAt } from "./src/canvas-core/austerityChapterOne";`, resolveDir: process.cwd(), loader: "ts" }, bundle: true, format: "esm", write: false, platform: "neutral", plugins: [overlay], logLevel: "error" })).outputFiles[0].text;
const { film, activeStepsAt } = await import("data:text/javascript;base64," + Buffer.from(js).toString("base64"));
const holds = film.meta.holds ?? [];
const inHold = (f) => holds.some(([a, b]) => f >= a && f < b);
for (const range of process.argv.slice(2)) {
  const [from, to] = range.split("-").map(Number);
  const marks = new Set(); let held = 0;
  for (let f = from; f < to; f++) { activeStepsAt(f).forEach((m) => marks.add(m)); if (inHold(f)) held++; }
  console.log(`${from}-${to} (${(from / 30).toFixed(2)}-${(to / 30).toFixed(2)} s, ${((to - from) / 30).toFixed(1)} s): ${held} of ${to - from} frames in declared rests; marks being made: ${[...marks].join(", ") || "none"}`);
}
