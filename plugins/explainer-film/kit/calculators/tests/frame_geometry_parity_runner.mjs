// What this does: the JavaScript half of test_frame_geometry_parity.py. It reads a file of cases (which function, which
// camera, which arguments), runs each through kit/paper-film/scenes/frame-geometry.js and prints the results as JSON, so
// the Python test can compare them with frame_geometry.py's. The module is loaded from its text as an ES module, so this
// works on node 18 and later without any package settings.
// Use: node frame_geometry_parity_runner.mjs CASES.json [PATH/TO/frame-geometry.js]
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const casesPath = process.argv[2];
const modulePath = process.argv[3] ?? join(here, '..', '..', 'paper-film', 'scenes', 'frame-geometry.js');
const source = readFileSync(modulePath, 'utf8');
const geometry = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

const camel = (name) => name.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
const builders = { turn: 'cameraFromTurn', looking_at: 'cameraLookingAt', blender_quaternion: 'cameraFromBlenderQuaternion', three: 'cameraFromThree' };
function build(spec) {
  const fn = geometry[builders[spec.from]];
  if (!fn) throw new Error(`no camera builder for ${spec.from}`);
  return fn(...spec.args);
}
const cases = JSON.parse(readFileSync(casesPath, 'utf8'));
const results = [];
for (const c of cases) {
  try {
    if (c.function === 'camera') { results.push({ id: c.id, value: build(c.camera) }); continue; }   // compare the camera itself
    const fn = geometry[camel(c.function)];
    if (!fn) { results.push({ id: c.id, error: `no function ${camel(c.function)} in frame-geometry.js` }); continue; }
    let args = c.args;
    if (c.function === 'slide_magnifications') args = [build(c.cameras[0]), build(c.cameras[1]), ...c.args];
    else if (c.camera) args = [build(c.camera), ...c.args];
    results.push({ id: c.id, value: fn(...args) });
  } catch (problem) {
    results.push({ id: c.id, error: String(problem) });
  }
}
process.stdout.write(JSON.stringify(results));
