// What this does: the camera sums of kit/calculators/frame_geometry.py, for page files and other JavaScript: where a
// 3D point lands on the 1080 x 1920 film frame (or the plate) without drawing anything, how big a thing comes out in
// pixels, metres per pixel, where a street's lines meet, how far a camera may stand for a thing to reach a given height
// on the frame ("down"), the eye height needed, what a turn or a sideways slide moves, how much a near thing slides
// against what is behind it, and how much a slide magnifies the painting (the limit comes from the painting's height).
// It imports nothing (no three.js), so node can run it too: kit/calculators/tests/test_frame_geometry_parity.py proves
// it gives the same numbers as the Python, case by case.
//
// Places are Blender metres (x across, y forward, z up). three.js is (x, z, -y): toThree() and fromThree() convert, and
// cameraFromThree() / cameraFromThreeLookAt() take a three.js camera directly. On the frame, "across" runs 0 (left) to 1
// (right) and "down" 0 (top) to 1 (bottom). Turn is + to the left of straight up +y; tilt is + looking up.
//
// The house numbers (frame size, lenses, the painting's height) live in kit/film-settings.json; pass them in, or read
// them with settingValue(settings, 'frame.width_pixels') from the parsed file.
//
// Use in a page file:
//   import { cameraFromThreeLookAt, projectPoint, toThree } from './frame-geometry.js';
//   const camera = cameraFromThreeLookAt([0.55, 1.45, 8.9], [-1.15, 0.85, 3.0], 60.4, 1080, 1920);
//   const where = projectPoint(camera, fromThree([-0.15, 1.05, 3.75]));   // { across, down, xPixels, yPixels, depth, inFront }

// ------------------------------------------------------------------------------------------------ small vector sums
export const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const subtract = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const length = (a) => Math.sqrt(dot(a, a));
export function normalise(a) {
  const n = length(a);
  if (n === 0) throw new Error('a direction of length 0 has no direction');
  return [a[0] / n, a[1] / n, a[2] / n];
}
export const toThree = (p) => [p[0], p[2], -p[1]];
export const fromThree = (p) => [p[0], -p[2], p[1]];
const radians = (d) => (d * Math.PI) / 180;
const degrees = (r) => (r * 180) / Math.PI;

// ------------------------------------------------------------------------------------------------ lenses
export function focalLengthPixels(verticalFovDegrees, frameHeight) {
  return frameHeight / 2 / Math.tan(radians(verticalFovDegrees) / 2);
}
export function horizontalFovDegrees(verticalFovDegrees, frameWidth, frameHeight) {
  return degrees(2 * Math.atan(Math.tan(radians(verticalFovDegrees) / 2) * frameWidth / frameHeight));
}

// ------------------------------------------------------------------------------------------------ cameras
export function makeCamera(position, forward, up, verticalFovDegrees, frameWidth, frameHeight, name = '') {
  const f = normalise(forward);
  const right = normalise(cross(f, up));
  const trueUp = cross(right, f);
  return { name, position: position.map(Number), forward: f, right, up: trueUp, verticalFovDegrees: Number(verticalFovDegrees),
    frame: [frameWidth, frameHeight], focal: focalLengthPixels(verticalFovDegrees, frameHeight) };
}
const multiply = (a, b) => [0, 1, 2].map((i) => [0, 1, 2].map((j) => a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]));
const apply = (m, v) => [0, 1, 2].map((i) => m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2]);
export function blenderEulerMatrix(xDegrees, yDegrees, zDegrees) {
  const [cx, sx] = [Math.cos(radians(xDegrees)), Math.sin(radians(xDegrees))];
  const [cy, sy] = [Math.cos(radians(yDegrees)), Math.sin(radians(yDegrees))];
  const [cz, sz] = [Math.cos(radians(zDegrees)), Math.sin(radians(zDegrees))];
  const rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]];
  const ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]];
  const rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]];
  return multiply(rz, multiply(ry, rx));
}
// as the project's scripts set a camera: Blender rotation (90 + tilt, roll, turn), XYZ order
export function cameraFromTurn(position, turnDegrees = 0, tiltDegrees = 0, rollDegrees = 0, verticalFovDegrees = 60.4, frameWidth = 1080, frameHeight = 1920, name = '') {
  const m = blenderEulerMatrix(90 + tiltDegrees, rollDegrees, turnDegrees);
  return makeCamera(position, apply(m, [0, 0, -1]), apply(m, [0, 1, 0]), verticalFovDegrees, frameWidth, frameHeight, name);
}
export function cameraLookingAt(position, target, verticalFovDegrees = 60.4, frameWidth = 1080, frameHeight = 1920, name = '') {
  return makeCamera(position, subtract(target, position), [0, 0, 1], verticalFovDegrees, frameWidth, frameHeight, name);
}
export function quaternionMatrix(w, x, y, z) {
  const n = Math.sqrt(w * w + x * x + y * y + z * z);
  [w, x, y, z] = [w / n, x / n, y / n, z / n];
  return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]];
}
export function cameraFromBlenderQuaternion(position, quaternionWxyz, verticalFovDegrees, frameWidth = 1080, frameHeight = 1920, name = '') {
  const m = quaternionMatrix(...quaternionWxyz);
  return makeCamera(position, apply(m, [0, 0, -1]), apply(m, [0, 1, 0]), verticalFovDegrees, frameWidth, frameHeight, name);
}
// a three.js camera: position and quaternion [x, y, z, w] in three.js space
export function cameraFromThree(positionThree, quaternionXyzwThree, verticalFovDegrees, frameWidth = 1080, frameHeight = 1920, name = '') {
  const [x, y, z, w] = quaternionXyzwThree;
  const m = quaternionMatrix(w, x, y, z);
  return makeCamera(fromThree(positionThree), fromThree(apply(m, [0, 0, -1])), fromThree(apply(m, [0, 1, 0])), verticalFovDegrees, frameWidth, frameHeight, name);
}
// a three.js camera aimed at a target (as kit.stillShot poses are written), kept level
export function cameraFromThreeLookAt(positionThree, targetThree, verticalFovDegrees, frameWidth = 1080, frameHeight = 1920, name = '') {
  return cameraLookingAt(fromThree(positionThree), fromThree(targetThree), verticalFovDegrees, frameWidth, frameHeight, name);
}
export function cameraAngles(camera) {
  const [f, r] = [camera.forward, camera.right];
  return { turnDegrees: degrees(Math.atan2(-f[0], f[1])), tiltDegrees: degrees(Math.asin(Math.max(-1, Math.min(1, f[2])))),
    rollDegrees: degrees(Math.asin(Math.max(-1, Math.min(1, -r[2])))) };
}
export function withLens(camera, verticalFovDegrees, frameWidth, frameHeight) {
  return makeCamera(camera.position, camera.forward, camera.up, verticalFovDegrees, frameWidth ?? camera.frame[0], frameHeight ?? camera.frame[1], camera.name);
}
export function movedTo(camera, position) {
  return makeCamera(position, camera.forward, camera.up, camera.verticalFovDegrees, camera.frame[0], camera.frame[1], camera.name);
}

// ------------------------------------------------------------------------------------------------ projection
export function projectPoint(camera, point) {
  const d = subtract(point, camera.position);
  const depth = dot(d, camera.forward);
  const [width, height] = camera.frame;
  if (Math.abs(depth) < 1e-12) return { across: null, down: null, xPixels: null, yPixels: null, depth, inFront: false };
  const across = 0.5 + camera.focal * dot(d, camera.right) / (depth * width);
  const down = 0.5 - camera.focal * dot(d, camera.up) / (depth * height);
  return { across, down, xPixels: across * width, yPixels: down * height, depth, inFront: depth > 0 };
}
export function projectDirection(camera, direction) {
  const depth = dot(direction, camera.forward);
  if (depth <= 0) return null;
  const [width, height] = camera.frame;
  return { across: 0.5 + camera.focal * dot(direction, camera.right) / (depth * width),
    down: 0.5 - camera.focal * dot(direction, camera.up) / (depth * height) };
}
export function boxCorners(low, high) {
  const corners = [];
  for (const x of [low[0], high[0]]) for (const y of [low[1], high[1]]) for (const z of [low[2], high[2]]) corners.push([x, y, z]);
  return corners;
}
export function boxFromCentre(centre, size) {
  const half = size.map((s) => s / 2);
  return [subtract(centre, half), add(centre, half)];
}
export function projectBox(camera, points) {
  const landed = points.map((p) => projectPoint(camera, p));
  const front = landed.filter((p) => p.inFront);
  if (!front.length) return { box: null, nearestDepth: null, allInFront: false };
  return { box: [Math.min(...front.map((p) => p.across)), Math.min(...front.map((p) => p.down)),
    Math.max(...front.map((p) => p.across)), Math.max(...front.map((p) => p.down))],
  nearestDepth: Math.min(...front.map((p) => p.depth)), allInFront: front.length === landed.length };
}
export function inFrame(landed, margin = 0) {
  return Boolean(landed.inFront && landed.across >= margin && landed.across <= 1 - margin && landed.down >= margin && landed.down <= 1 - margin);
}

// ------------------------------------------------------------------------------------------------ sizes
export const metresPerPixel = (camera, depth) => depth / camera.focal;
export const sizeInPixels = (camera, sizeMetres, depth) => sizeMetres * camera.focal / depth;
export const sizeNeeded = (camera, pixels, depth) => pixels * depth / camera.focal;
export const distanceForSize = (camera, sizeMetres, pixels) => sizeMetres * camera.focal / pixels;
export const frameShare = (camera, areaSquareMetres, depth) => areaSquareMetres * (camera.focal / depth) ** 2 / (camera.frame[0] * camera.frame[1]);
export const distanceForWidthShare = (camera, widthMetres, share) => widthMetres * camera.focal / (share * camera.frame[0]);

// ------------------------------------------------------------------------------------------------ closed forms for planning
export function meetingPointLevel(turnDegrees, slope, verticalFovDegrees, frameWidth, frameHeight) {
  const f = focalLengthPixels(verticalFovDegrees, frameHeight);
  const psi = radians(turnDegrees);
  return { across: 0.5 + f * Math.tan(psi) / frameWidth, down: 0.5 - f * slope / (frameHeight * Math.cos(psi)) };
}
export function turnForMeetingPoint(across, verticalFovDegrees, frameWidth, frameHeight) {
  return degrees(Math.atan((across - 0.5) * frameWidth / focalLengthPixels(verticalFovDegrees, frameHeight)));
}
export function turnMovesPerDegree(verticalFovDegrees, frameWidth, frameHeight) {
  return focalLengthPixels(verticalFovDegrees, frameHeight) * Math.PI / 180 / frameWidth;
}
export function groundPointDown(depth, eyeAboveSurface, meetingDown, verticalFovDegrees, frameHeight) {
  return meetingDown + focalLengthPixels(verticalFovDegrees, frameHeight) * eyeAboveSurface / (depth * frameHeight);
}
export function reachDistance(reachDown, eyeAboveSurface, meetingDown, verticalFovDegrees, frameHeight) {
  if (reachDown <= meetingDown) return null;
  return focalLengthPixels(verticalFovDegrees, frameHeight) * eyeAboveSurface / ((reachDown - meetingDown) * frameHeight);
}
export function eyeNeeded(depth, reachDown, meetingDown, surfaceHeight, verticalFovDegrees, frameHeight) {
  return surfaceHeight + (reachDown - meetingDown) * frameHeight * depth / focalLengthPixels(verticalFovDegrees, frameHeight);
}
export function slideForScreenShift(shiftShareOfWidth, depth, verticalFovDegrees, frameWidth, frameHeight) {
  return shiftShareOfWidth * frameWidth * depth / focalLengthPixels(verticalFovDegrees, frameHeight);
}
export function parallaxSidewaysPixels(slideMetres, nearDepth, behindDepth, verticalFovDegrees, frameHeight) {
  return focalLengthPixels(verticalFovDegrees, frameHeight) * slideMetres * Math.abs(1 / nearDepth - 1 / behindDepth);
}
export function parallaxForwardPixels(offsetPixelsFromCentre, slideMetres, nearDepth, behindDepth) {
  return offsetPixelsFromCentre * slideMetres * (behindDepth - nearDepth) / ((nearDepth - slideMetres) * (behindDepth - slideMetres));
}
export function slideLimit(paintingHeightPixels, filmHeightPixels, filmVerticalFovDegrees, plateVerticalFovDegrees) {
  return (paintingHeightPixels / filmHeightPixels) * Math.tan(radians(filmVerticalFovDegrees) / 2) / Math.tan(radians(plateVerticalFovDegrees) / 2);
}
export function slideMagnifications(startCamera, endCamera, namedPoints) {
  return namedPoints.map(([name, point]) => {
    const start = projectPoint(startCamera, point).depth;
    const end = projectPoint(endCamera, point).depth;
    return { name, point, depthStart: start, depthEnd: end, magnification: end > 0 && start > 0 ? start / end : null };
  });
}
export const longestSlide = (nearestDepthAtEnd, limit) => nearestDepthAtEnd * (limit - 1);
export function turnAllowanceDegrees(filmVerticalFovDegrees, plateVerticalFovDegrees, frameWidth, frameHeight) {
  return { turnEachWayDegrees: (horizontalFovDegrees(plateVerticalFovDegrees, frameWidth, frameHeight) - horizontalFovDegrees(filmVerticalFovDegrees, frameWidth, frameHeight)) / 2,
    tiltEachWayDegrees: (plateVerticalFovDegrees - filmVerticalFovDegrees) / 2 };
}
export function sidewaysAllowanceMetres(nearestDepth, filmVerticalFovDegrees, plateVerticalFovDegrees, frameWidth, frameHeight) {
  const aspect = frameWidth / frameHeight;
  return nearestDepth * (Math.tan(radians(plateVerticalFovDegrees) / 2) * aspect - Math.tan(radians(filmVerticalFovDegrees) / 2) * aspect);
}

// ------------------------------------------------------------------------------------------------ house numbers
// One value from a parsed kit/film-settings.json, by its dotted key; stops with a clear message when it is missing.
export function settingValue(settings, key) {
  let node = settings;
  for (const part of key.split('.')) {
    if (!node || typeof node !== 'object' || !(part in node)) throw new Error(`film-settings.json has no "${key}" ("${part}" is missing)`);
    node = node[part];
  }
  if (!node || typeof node !== 'object' || !('value' in node)) throw new Error(`film-settings.json: "${key}" is a section, not a single number`);
  return node.value;
}
