// What this does: shines a painting back onto the 3D set it was painted from (plan 3 of
// experiments/26 Plans: a set built in Blender is drawn once from its main camera, the "plate"; the
// plate is painted over; the painting is projected back onto the same shapes here), so the camera
// can move a little without anything tearing.
//
// Every mesh of the set gets a material that:
//   1. shows the painting, projected from the projector (the camera the plate was drawn from), on
//      every surface point the projector actually saw: inside its frame, facing it, and not hidden
//      behind something else. "Hidden" is tested against a distance map: the set's distances from
//      the projector, drawn once when the projection is made (one lookup per pixel per frame). The
//      painting shows at its painted brightness: no stage lamp, shadow or haze is added to it.
//   2. elsewhere (surfaces the plate never saw: backs, the far side of things, ground hidden behind a
//      house) shows the mesh's own texture, darkened and tinted toward the painting's average colour
//      and lit by the page's lights, so they read as the same place, not black holes or bright raw
//      textures.
// Two soft fades keep the seams quiet once the camera has moved away from the projector:
//   - stretch: a surface the plate saw nearly edge-on, now seen more face-on, would show a few
//     painted pixels stretched into streaks; it fades to its own texture as the stretch grows.
//   - occlusion edges: just beside the outline of a near thing, the far surface behind it holds a
//     smear of the near thing's paint (the painter's brush crosses outlines); a thin band there fades
//     to its own texture.
// Both fades scale with how far the camera has moved from the projector, so from the projector's own
// view the set shows the painting exactly.
//
// Use in a page (three.js r169; works in the software renderer, SwiftShader):
//   import { loadProjector, projectPaintingOnto } from '../projected-set.js';
//   const set = await loadModel('/assets/models/chapter-3/pit-village.glb');
//   kit.scene.add(set);
//   const projector = await loadProjector('/assets/models/chapter-3/pit-village-camera.json');
//   const painting = await loadTexture('/assets/paintings/chapter-3/pit-village-painted.jpg');
//   const projection = projectPaintingOnto(kit, set, painting, projector);
//   // the projector's own view, for the page's camera (it shows the painting exactly):
//   kit.stillShot({ position: projector.position.toArray(), target: projector.userData.target.toArray(), fov: projector.fov }, [...]);
//
// camera.json (written by the Blender plate script): position [x, y, z] and quaternion [x, y, z, w]
// in three.js world space (Y up; the same space the set's glb lands in), fov (vertical, degrees),
// aspect (width / height), near, far.

import { THREE } from './cinema-kit.js';
import { renderer } from '../stage/cinema-stage.js';

// ------------------------------------------------------------------------------- the projector

// A projector camera from plain settings: { position, quaternion, fov, aspect, near, far }.
// position and quaternion may be arrays ([x, y, z], [x, y, z, w]), objects with x, y, z (and w), or
// three.js vectors. userData.target is a point 10 m ahead, for kit.stillShot.
export function projectorCamera({ position, quaternion, fov, aspect, near = 0.1, far = 400 }) {
  const camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
  const xyz = (v) => (Array.isArray(v) ? v : [v.x, v.y, v.z]);
  camera.position.set(...xyz(position));
  camera.quaternion.set(...(Array.isArray(quaternion) ? quaternion : [quaternion.x, quaternion.y, quaternion.z, quaternion.w])).normalize();
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  camera.userData.target = new THREE.Vector3(0, 0, -10).applyQuaternion(camera.quaternion).add(camera.position);
  return camera;
}

// Loads a camera.json (see the top of this file) and returns the projector camera.
export async function loadProjector(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`projected-set: could not load the projector camera ${url} (${response.status})`);
  const settings = await response.json();
  for (const field of ['position', 'quaternion', 'fov', 'aspect']) {
    if (settings[field] === undefined) throw new Error(`projected-set: ${url} has no "${field}"`);
  }
  return projectorCamera(settings);
}

// The settings of a camera, as a camera.json holds them (for writing one from the stage).
export function projectorSettings(camera) {
  camera.updateMatrixWorld(true);
  return {
    position: camera.position.toArray(), quaternion: camera.quaternion.toArray(),
    fov: camera.fov, aspect: camera.aspect, near: camera.near, far: camera.far,
  };
}

// ----------------------------------------------------------------- the distance map (made once)

const passCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const passScene = new THREE.Scene();
const passQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), null);
passQuad.frustumCulled = false;
passScene.add(passQuad);
const passVertex = 'varying vec2 vUv;\nvoid main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }';
function runPass(material, target) {
  // a full-frame pass ignores depth: a target that also served as the distance picture still holds
  // the set's depths, which would hide most of the pass
  material.depthTest = false;
  material.depthWrite = false;
  passQuad.material = material;
  renderer.setRenderTarget(target);
  renderer.render(passScene, passCamera);
}

// a float picture for distances: 32-bit if the graphics allow drawing into it, else 16-bit
function distanceTarget(width, height, depthBuffer) {
  const float = renderer.extensions.has('EXT_color_buffer_float');
  return new THREE.WebGLRenderTarget(width, height, {
    type: float ? THREE.FloatType : THREE.HalfFloatType, format: THREE.RGBAFormat, colorSpace: THREE.NoColorSpace,
    minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, generateMipmaps: false, depthBuffer,
  });
}

// Draws every surface of the set as its distance along the projector's view (both sides of every
// face, as Blender draws them), into the red channel.
const distanceMaterial = new THREE.ShaderMaterial({
  side: THREE.DoubleSide,
  vertexShader: `
    varying float vDistance;
    void main() {
      vec4 viewPosition = vec4(position, 1.0);
      #ifdef USE_INSTANCING
        viewPosition = instanceMatrix * viewPosition;
      #endif
      viewPosition = modelViewMatrix * viewPosition;
      vDistance = -viewPosition.z;
      gl_Position = projectionMatrix * viewPosition;
    }`,
  fragmentShader: 'varying float vDistance;\nvoid main() { gl_FragColor = vec4(vDistance, 0.0, 0.0, 1.0); }',
});

// Marks the far side of every jump in distance (an outline of a near thing against a far surface):
// a texel whose 4 neighbours include one nearer by more than `jump` (a share of its own distance).
const jumpMaterial = new THREE.ShaderMaterial({
  vertexShader: passVertex,
  uniforms: { distanceMap: { value: null }, texel: { value: new THREE.Vector2() }, jump: { value: 0.03 } },
  fragmentShader: `
    varying vec2 vUv; uniform sampler2D distanceMap; uniform vec2 texel; uniform float jump;
    void main() {
      float here = texture2D(distanceMap, vUv).r;
      float nearest = min(min(texture2D(distanceMap, vUv + vec2(texel.x, 0.0)).r, texture2D(distanceMap, vUv - vec2(texel.x, 0.0)).r),
                          min(texture2D(distanceMap, vUv + vec2(0.0, texel.y)).r, texture2D(distanceMap, vUv - vec2(0.0, texel.y)).r));
      float farSide = step(jump, (here - nearest) / max(here, 1e-4));
      gl_FragColor = vec4(here, farSide, 0.0, 1.0);
    }`,
});

// Spreads each outline mark across a band `radius` texels wide on the far surface only (not onto the
// near thing in front): green = 1 at the outline, falling to 0 at the band's edge.
const bandMaterial = new THREE.ShaderMaterial({
  vertexShader: passVertex,
  uniforms: { jumpMap: { value: null }, texel: { value: new THREE.Vector2() }, radius: { value: 8 }, sameSurface: { value: 0.03 } },
  fragmentShader: `
    varying vec2 vUv; uniform sampler2D jumpMap; uniform vec2 texel; uniform float radius; uniform float sameSurface;
    const int STEPS = 6;
    void main() {
      float here = texture2D(jumpMap, vUv).r;
      float band = 0.0;
      for (int y = -STEPS; y <= STEPS; y++) {
        for (int x = -STEPS; x <= STEPS; x++) {
          vec2 offset = vec2(float(x), float(y)) / float(STEPS);
          float reach = length(offset);
          if (reach > 1.0) continue;
          vec2 mark = texture2D(jumpMap, vUv + offset * radius * texel).rg;
          // only marks on a surface at least as far as this one (this texel is on the far side too)
          float sameSide = step(mark.r * (1.0 - sameSurface), here);
          band = max(band, mark.g * sameSide * (1.0 - reach));
        }
      }
      gl_FragColor = vec4(here, smoothstep(0.0, 1.0, band), 0.0, 1.0);
    }`,
});

// The average colour of a picture (linear light), from a 32 x 32 copy of it.
export function averageColourOf(texture) {
  const image = texture?.image;
  if (!image || !(image.width > 0)) return new THREE.Color(0.18, 0.17, 0.16);
  const canvas = new OffscreenCanvas(32, 32), context = canvas.getContext('2d');
  context.drawImage(image, 0, 0, 32, 32);
  const data = context.getImageData(0, 0, 32, 32).data;
  const toLinear = (value) => { const c = value / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const sum = [0, 0, 0];
  for (let i = 0; i < data.length; i += 4) for (let c = 0; c < 3; c++) sum[c] += toLinear(data[i + c]);
  const count = data.length / 4;
  return new THREE.Color(sum[0] / count, sum[1] / count, sum[2] / count);
}

// The painting's sky alone, for a far sky card: every pixel where the projector saw something nearer
// than `farther` (houses, a pithead) is filled from the painted sky round it, so when the camera
// moves, the sky uncovered behind a tower is painted sky, not a flat colour or a ghost of the tower.
// `projection` is the result of projectPaintingOnto for the set (its distance map says what is sky);
// `grow` (painting pixels) also replaces a thin band round each outline, where the painter's brush
// crosses it. Returns a texture (sRGB) the size of the painting.
export function paintedSkyOnly(projection, painting, { farther = 1000, grow = 4 } = {}) {
  const target = projection.visibility, mapWidth = target.width, mapHeight = target.height;
  const float = target.texture.type === THREE.FloatType;
  const raw = float ? new Float32Array(mapWidth * mapHeight * 4) : new Uint16Array(mapWidth * mapHeight * 4);
  renderer.readRenderTargetPixels(target, 0, 0, mapWidth, mapHeight, raw);
  const distanceAt = float ? (i) => raw[i * 4] : (i) => THREE.DataUtils.fromHalfFloat(raw[i * 4]);
  const image = painting.image, width = image.width, height = image.height;
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const context = canvas.getContext('2d');
  context.drawImage(image, 0, 0);
  const pixels = context.getImageData(0, 0, width, height);
  const data = pixels.data;
  // sky = farther than `farther` in the distance map (its rows run bottom up)
  const solid = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    const mapRow = mapHeight - 1 - Math.min(mapHeight - 1, Math.floor((y + 0.5) / height * mapHeight));
    for (let x = 0; x < width; x++) {
      const mapColumn = Math.min(mapWidth - 1, Math.floor((x + 0.5) / width * mapWidth));
      solid[y * width + x] = distanceAt(mapRow * mapWidth + mapColumn) < farther ? 1 : 0;
    }
  }
  // grow the solid parts by `grow` pixels (a square reach, rows then columns)
  const grown = new Uint8Array(solid);
  if (grow > 0) {
    const across = new Uint8Array(width * height);
    for (let y = 0; y < height; y++) {
      let last = -Infinity;
      for (let x = 0; x < width; x++) { if (solid[y * width + x]) last = x; if (x - last <= grow) across[y * width + x] = 1; }
      last = Infinity;
      for (let x = width - 1; x >= 0; x--) { if (solid[y * width + x]) last = x; if (last - x <= grow) across[y * width + x] = 1; }
    }
    for (let x = 0; x < width; x++) {
      let last = -Infinity;
      for (let y = 0; y < height; y++) { if (across[y * width + x]) last = y; grown[y * width + x] = y - last <= grow ? 1 : 0; }
      last = Infinity;
      for (let y = height - 1; y >= 0; y--) { if (across[y * width + x]) last = y; if (last - y <= grow) grown[y * width + x] = 1; }
    }
  }
  // fill the solid parts from the sky round them: average the sky down a pyramid of halvings, then
  // bring it back up, each level filling its gaps from the smoother level below it
  const levels = [];
  let w = width, h = height;
  let colour = new Float32Array(w * h * 3), weight = new Float32Array(w * h);
  for (let i = 0; i < w * h; i++) {
    if (grown[i]) continue;
    weight[i] = 1;
    for (let c = 0; c < 3; c++) colour[i * 3 + c] = data[i * 4 + c];
  }
  levels.push({ w, h, colour, weight });
  while (w > 1 || h > 1) {
    const nw = Math.max(1, Math.ceil(w / 2)), nh = Math.max(1, Math.ceil(h / 2));
    const ncolour = new Float32Array(nw * nh * 3), nweight = new Float32Array(nw * nh);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x, j = (y >> 1) * nw + (x >> 1);
      nweight[j] += weight[i];
      for (let c = 0; c < 3; c++) ncolour[j * 3 + c] += colour[i * 3 + c];
    }
    w = nw; h = nh; colour = ncolour; weight = nweight;
    levels.push({ w, h, colour, weight });
  }
  // colours as averages (sum / weight); from the top down, gaps take the level below, read smoothly
  const average = (level, i, c) => level.colour[i * 3 + c] / level.weight[i];
  const filled = levels.map((level) => new Float32Array(level.w * level.h * 3));
  const top = levels.length - 1;
  for (let c = 0; c < 3; c++) filled[top][c] = levels[top].weight[0] > 0 ? average(levels[top], 0, c) : 128;
  for (let k = top - 1; k >= 0; k--) {
    const level = levels[k], below = levels[k + 1], belowFilled = filled[k + 1];
    for (let y = 0; y < level.h; y++) for (let x = 0; x < level.w; x++) {
      const i = y * level.w + x;
      const share = Math.min(1, level.weight[i]);
      // the level below at this point, between its four nearest pixels
      const bx = Math.min(below.w - 1, Math.max(0, (x + 0.5) / 2 - 0.5)), by = Math.min(below.h - 1, Math.max(0, (y + 0.5) / 2 - 0.5));
      const x0 = Math.floor(bx), y0 = Math.floor(by), x1 = Math.min(below.w - 1, x0 + 1), y1 = Math.min(below.h - 1, y0 + 1);
      const fx = bx - x0, fy = by - y0;
      for (let c = 0; c < 3; c++) {
        const smooth = (belowFilled[(y0 * below.w + x0) * 3 + c] * (1 - fx) + belowFilled[(y0 * below.w + x1) * 3 + c] * fx) * (1 - fy)
          + (belowFilled[(y1 * below.w + x0) * 3 + c] * (1 - fx) + belowFilled[(y1 * below.w + x1) * 3 + c] * fx) * fy;
        filled[k][i * 3 + c] = share > 0 ? average(level, i, c) * share + smooth * (1 - share) : smooth;
      }
    }
  }
  for (let i = 0; i < width * height; i++) {
    if (!grown[i]) continue;
    for (let c = 0; c < 3; c++) data[i * 4 + c] = filled[0][i * 3 + c];
  }
  context.putImageData(pixels, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

// The zone round the near props, for the behind painting: 1 where a near prop stood in front of the
// background (the set's distance is nearer than the background's alone) and close round it, falling
// to 0 at `radius` texels. There the painting's own edges belong to the props (the painter's ink
// outlines, smears), so the background takes the behind painting as soon as the camera moves.
const zoneMaterial = new THREE.ShaderMaterial({
  vertexShader: passVertex,
  uniforms: { withProps: { value: null }, withoutProps: { value: null }, mask: { value: null }, useMask: { value: 0 },
    texel: { value: new THREE.Vector2() }, radius: { value: 30 }, jump: { value: 0.03 } },
  fragmentShader: `
    varying vec2 vUv; uniform sampler2D withProps; uniform sampler2D withoutProps; uniform sampler2D mask; uniform float useMask;
    uniform vec2 texel; uniform float radius; uniform float jump;
    const int STEPS = 6;
    // a near prop here? (from the two distance maps; or, for the second, wide step, from the first)
    float propAt(vec2 at) {
      if (useMask > 0.5) return step(0.01, texture2D(mask, at).r);
      float near = texture2D(withProps, at).r, far = texture2D(withoutProps, at).r;
      return step(jump * near, far - near);
    }
    void main() {
      float zone = 0.0;
      for (int y = -STEPS; y <= STEPS; y++) {
        for (int x = -STEPS; x <= STEPS; x++) {
          vec2 offset = vec2(float(x), float(y)) / float(STEPS);
          float reach = length(offset);
          if (reach > 1.0) continue;
          zone = max(zone, propAt(vUv + offset * radius * texel) * clamp(2.0 * (1.0 - reach), 0.0, 1.0));
        }
      }
      gl_FragColor = vec4(zone, 0.0, 0.0, 1.0);
    }`,
});

// ------------------------------------------------------------------------------ the materials

const VERTEX_DECLARATIONS = 'varying vec3 vProjectionWorld;\nvarying vec3 vProjectionNormal;';
const VERTEX_BODY = `
  vec4 projectionWorld = vec4(transformed, 1.0);
  #ifdef USE_INSTANCING
    projectionWorld = instanceMatrix * projectionWorld;
  #endif
  vProjectionWorld = (modelMatrix * projectionWorld).xyz;
  #ifdef PROJECTION_UNLIT
    vProjectionNormal = normalize(mat3(modelMatrix) * normal);
  #else
    vProjectionNormal = inverseTransformDirection(transformedNormal, viewMatrix);
  #endif`;
const FRAGMENT_DECLARATIONS = `
  varying vec3 vProjectionWorld;
  varying vec3 vProjectionNormal;
  uniform sampler2D projectionPainting;
  uniform sampler2D projectionVisibility;
  uniform mat4 projectorViewProjection;
  uniform vec3 projectorPosition;
  uniform float projectorTexelAngle;
  uniform float projectionBias;
  uniform vec2 projectionStretch;
  uniform float projectionMoveAngle;
  uniform vec3 projectionFallbackTint;
  uniform float projectionStrength;
  uniform float projectionFrameEdge;
  uniform float projectionFill;
  uniform float projectionUnlitLift;
  uniform float projectionShowWeights;
  #ifdef PROJECTION_OWN
    uniform vec3 projectionOwnTint;
  #endif
  #ifdef PROJECTION_FRONT
    uniform vec2 projectionFrontStretch;
  #endif
  #ifdef PROJECTION_BEHIND
    uniform sampler2D projectionBehindPainting;
    uniform sampler2D projectionBehindVisibility;
    uniform sampler2D projectionNearZone;
    uniform float projectionQuickMove;
  #endif
  // How much of one painting this point wears (0..1), tested against that painting's distance map,
  // and the painting's colour there.
  float projectionSeenIn(sampler2D painting, sampler2D visibilityMap, out vec3 paintColour) {
    vec4 clip = projectorViewProjection * vec4(vProjectionWorld, 1.0);
    vec2 at = clip.xy / max(clip.w, 1e-4) * 0.5 + 0.5;
    // (both pictures are read before any early return, so the painting's mipmaps stay smooth)
    paintColour = texture2D(painting, clamp(at, 0.0, 1.0)).rgb;
    vec2 visibility = texture2D(visibilityMap, clamp(at, 0.0, 1.0)).rg;
    if (clip.w <= 0.0) return 0.0;
    // inside the projector's frame (hard edge: past it the painting has nothing, only streaks)
    if (at.x < 0.0 || at.x > 1.0 || at.y < 0.0 || at.y > 1.0) return 0.0;
    vec3 toProjector = projectorPosition - vProjectionWorld;
    float distanceToProjector = length(toProjector);
    vec3 surfaceNormal = normalize(vProjectionNormal) * (gl_FrontFacing ? 1.0 : -1.0);
    float facingProjector = dot(surfaceNormal, toProjector / distanceToProjector);
    if (facingProjector <= 0.0) return 0.0;
    // hidden behind something nearer? (the one distance lookup; the allowance grows on sloping
    // surfaces, where one texel of the map covers a longer stretch of distance)
    float slope = min(sqrt(max(0.0, 1.0 - facingProjector * facingProjector)) / max(facingProjector, 0.05), 20.0);
    float allowance = clip.w * (projectionBias + projectorTexelAngle * (1.5 + 1.5 * slope));
    float seen = 1.0 - smoothstep(allowance, allowance * 2.0, clip.w - visibility.r);
    // how far the camera has moved round this point from the projector: 0 = same view
    vec3 toCamera = normalize(cameraPosition - vProjectionWorld);
    float moved = smoothstep(0.0, projectionMoveAngle, 1.0 - dot(toCamera, toProjector / distanceToProjector));
    // stretch: seen nearly edge-on by the projector, now seen more face-on
    float stretch = max(0.0, dot(surfaceNormal, toCamera)) / max(facingProjector, 1e-4);
    #ifdef PROJECTION_FRONT
      vec2 stretchLimits = projectionFrontStretch;   // near props: their stretched rims carry the painter's misplaced outlines
    #else
      vec2 stretchLimits = projectionStretch;
    #endif
    seen *= 1.0 - smoothstep(stretchLimits.x, stretchLimits.y, stretch);
    seen *= smoothstep(0.0, 0.004, facingProjector);
    // the far side of a near thing's outline
    seen *= 1.0 - visibility.g * moved;
    // the projector's frame edge: a hard cut from the projector's view, a soft band once moved
    vec2 fromEdge = min(at, 1.0 - at);
    seen *= mix(1.0, smoothstep(0.0, projectionFrameEdge, min(fromEdge.x, fromEdge.y)), moved);
    return seen * projectionStrength;
  }
  // How much painting this point wears (0..1) and its colour: the painting where the projector saw
  // the point; else, with a "behind" painting, that one where only the near props hid it.
  float projectionWeight(out vec3 paintColour, out float behindShare) {
    float amount = projectionSeenIn(projectionPainting, projectionVisibility, paintColour);
    behindShare = 0.0;
    #ifdef PROJECTION_BEHIND
      // round the near props, the painting gives way to the behind painting as soon as the camera moves
      vec4 zoneClip = projectorViewProjection * vec4(vProjectionWorld, 1.0);
      float zone = texture2D(projectionNearZone, clamp(zoneClip.xy / max(zoneClip.w, 1e-4) * 0.5 + 0.5, 0.0, 1.0)).r;
      float quick = smoothstep(0.0, projectionQuickMove, 1.0 - dot(normalize(cameraPosition - vProjectionWorld), normalize(projectorPosition - vProjectionWorld)));
      amount *= 1.0 - zone * quick;
      vec3 behindColour;
      float behind = projectionSeenIn(projectionBehindPainting, projectionBehindVisibility, behindColour);
      behindShare = behind * (1.0 - amount);
      paintColour = (paintColour * amount + behindColour * behindShare) / max(amount + behindShare, 1e-4);
      amount += behindShare;
    #endif
    #ifdef PROJECTION_OWN
      behindShare = 0.0;
      return 0.0;   // keeps its own picture everywhere (sharp lettering), matched to the painting by its own tint
    #endif
    return amount;
  }`;
const FRAGMENT_MAP = `
  #include <map_fragment>
  vec3 projectionPaint;
  float projectionBehindShare;
  float projectionAmount = projectionWeight(projectionPaint, projectionBehindShare);
  #ifdef PROJECTION_OWN
    diffuseColor.rgb *= projectionOwnTint;        // its own surface, matched to the painting where it stands
  #else
    diffuseColor.rgb *= projectionFallbackTint;   // its own surface, darkened and tinted toward the painting
  #endif
  #ifdef PROJECTION_UNLIT
    diffuseColor.rgb *= projectionUnlitLift;      // unlit cards (a sky) are not darkened
  #endif`;
const FRAGMENT_EMISSIVE = `
  #include <emissivemap_fragment>
  totalEmissiveRadiance += diffuseColor.rgb * projectionFill;   // soft light from all round, so unlit sides aren't black
  totalEmissiveRadiance *= 1.0 - projectionAmount;`;
// where the painting covers a point fully, the lamps, shadows and soft light are not worked out at
// all (most of the frame near the projector's view). Measured in the software renderer on the test
// set it saved little (SwiftShader runs neighbouring pixels together), but it costs nothing.
const FRAGMENT_LIGHTS_BEGIN = `
  #if !defined( USE_CLEARCOAT ) && !defined( USE_SHEEN ) && !defined( USE_TRANSMISSION ) && !defined( PROJECTION_UNLIT )
    #define PROJECTION_SKIP_LIGHTS
  #endif
  #ifdef PROJECTION_SKIP_LIGHTS
  if (projectionAmount < 0.999) {
  #endif
  #include <lights_fragment_begin>`;
const FRAGMENT_LIGHTS_END = `
  #include <aomap_fragment>
  #ifdef PROJECTION_SKIP_LIGHTS
  }
  #endif`;
const FRAGMENT_END = `
  #include <fog_fragment>
  gl_FragColor.rgb = mix(gl_FragColor.rgb, projectionPaint, projectionAmount);   // at its painted brightness
  // weights view: orange = the painting, green = the behind painting, blue = its own surface
  if (projectionShowWeights > 0.5) gl_FragColor.rgb = (vec3(0.05, 0.12, 0.5) * (1.0 - projectionAmount) + vec3(1.0, 0.55, 0.15) * (projectionAmount - projectionBehindShare) + vec3(0.2, 0.85, 0.3) * projectionBehindShare) * (0.35 + 0.65 * dot(gl_FragColor.rgb, vec3(0.3, 0.59, 0.11)) / max(0.05, dot(projectionPaint, vec3(0.3, 0.59, 0.11)) + 0.05));`;

// A matte (Lambert) copy of a material with the same pictures, bumps, baked shading and glow.
function matteCopy(m) {
  const lambert = new THREE.MeshLambertMaterial({
    map: m.map ?? null, color: m.color ?? new THREE.Color(1, 1, 1), emissive: m.emissive ?? new THREE.Color(0, 0, 0),
    emissiveMap: m.emissiveMap ?? null, emissiveIntensity: m.emissiveIntensity ?? 1, aoMap: m.aoMap ?? null,
    aoMapIntensity: m.aoMapIntensity ?? 1, normalMap: m.normalMap ?? null, normalScale: m.normalScale ?? new THREE.Vector2(1, 1),
    transparent: m.transparent, opacity: m.opacity, side: m.side, alphaTest: m.alphaTest, vertexColors: m.vertexColors, fog: m.fog ?? true,
  });
  lambert.name = m.name;
  return lambert;
}

// Gives one material the projection (in place). Lambert, Phong, Standard and Physical materials keep
// their kind; anything else (Basic, Toon...) becomes a matte copy first. Returns the material to use.
function projectedVersion(material, uniforms, matte, own = null, behind = false, front = false) {
  // unlit (Basic) materials stay unlit: a painted sky card, a glowing sign
  const keepKind = material.isMeshBasicMaterial || material.isMeshLambertMaterial || material.isMeshPhongMaterial || material.isMeshStandardMaterial;
  const projected = keepKind && !(matte && material.isMeshStandardMaterial) ? material.clone() : matteCopy(material);
  if (projected.isMeshBasicMaterial) projected.defines = { ...(projected.defines ?? {}), PROJECTION_UNLIT: '' };
  if (own) {
    projected.defines = { ...(projected.defines ?? {}), PROJECTION_OWN: '' };
    uniforms = { ...uniforms, projectionOwnTint: own };
  }
  if (behind) projected.defines = { ...(projected.defines ?? {}), PROJECTION_BEHIND: '' };
  if (front) projected.defines = { ...(projected.defines ?? {}), PROJECTION_FRONT: '' };
  projected.name = material.name;
  const previousCompile = projected.onBeforeCompile;
  projected.onBeforeCompile = (shader, three) => {
    previousCompile?.call(projected, shader, three);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${VERTEX_DECLARATIONS}`)
      .replace('#include <project_vertex>', `#include <project_vertex>\n${VERTEX_BODY}`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${FRAGMENT_DECLARATIONS}`)
      .replace('#include <map_fragment>', FRAGMENT_MAP)
      .replace('#include <emissivemap_fragment>', FRAGMENT_EMISSIVE)
      .replace('#include <lights_fragment_begin>', FRAGMENT_LIGHTS_BEGIN)
      .replace('#include <aomap_fragment>', FRAGMENT_LIGHTS_END)
      .replace('#include <fog_fragment>', FRAGMENT_END);
  };
  projected.customProgramCacheKey = () => `projected-set-5|${own ? 'own' : ''}|${behind ? 'behind' : ''}|${front ? 'front' : ''}|${material.customProgramCacheKey?.() ?? ''}`;
  projected.needsUpdate = true;
  return projected;
}

// ------------------------------------------------------------------------------- the main call

// Shines `painting` (a texture, usually loaded with loadTexture: sRGB) onto every mesh of `setGroup`
// (already added to kit.scene and placed), from `projector` (a camera from loadProjector or
// projectorCamera, or the plain settings). Options:
//   mapSize        distance map height in texels (its width follows the projector's aspect); 2048
//   bias           allowance for "not hidden", as a share of the distance; 0.004
//   jump           a jump in distance bigger than this share marks an outline; 0.03
//   edgeWidth      the faded band beside outlines, as a share of the frame height; 0.006
//   stretch        [start, end] of the stretch fade (how much more face-on than in the plate); [2.5, 5]
//   moveAngle      how far round (1 - cos of the angle) the camera must move for the fades to be
//                  full; 0.01 (about 8 degrees)
//   frameEdge      once the camera has moved, the painting fades out over this share of the
//                  projector's frame at its edges (from the projector's view the edge stays hard); 0.03
//   darken         surfaces the plate never saw are matched to the painting's brightness, then
//                  darkened to this share of it; 0.75
//   darkenUnlit    the same for unlit (Basic) materials, such as a sky card: a darker patch on the
//                  sky where a chimney stood in the plate reads as a ghost of it; 1
//   tint           how far those are tinted toward the painting's colour (0 = their own colours,
//                  only darkened; 1 = the painting's average colour balance); 0.6
//   fill           soft light from all round on those surfaces (a share of their own colour), so the
//                  sides the lamps miss aren't black; 0.35
//   calibrate      match the brightness and colour of unseen surfaces by drawing the set once from
//                  the projector with and without the painting (a small 270 x 480 drawing); true.
//                  With false, the painting's average colour (averageColour, or read from the
//                  picture) sets the tint and only `darken` sets the brightness.
//   matte          turn realistic (Standard) materials into matte ones: about half the drawing time
//                  in the software renderer, without soft reflections; true
//   behind         { painting, hide }: a second painting of the same view with the near props in `hide`
//                  (objects of the set) painted out. Surfaces those props hid from the projector, uncovered
//                  as the camera moves (the road behind a cart), wear it instead of their own tinted
//                  surface. A second distance map is drawn without the props. The props' own materials
//                  never use it. Round the props (out to `reach`, a share of the frame height; 0.05) the
//                  background gives way to it as soon as the camera moves (`quickMove`, 1 - cos of the
//                  angle; 0.00003, about half a degree): the painter's outlines round a prop are on the
//                  background, and would be left behind as ghosts. The props themselves fade to their
//                  own surfaces sooner where the move stretches the painting on them (`frontStretch`,
//                  [1.3, 1.9]): their rims, seen edge-on in the plate, carry the painter's misplaced
//                  outline and a sliver of road.
//   ownSurface     names of materials that never wear the painting and keep their own pictures, for
//                  lettering the painter blurred or garbled (a notice, a sign). They still hide what
//                  is behind them in the distance map. With calibrate, each is matched in brightness
//                  and colour to the painting where it stands (the middle of its outline as the
//                  projector sees it); without, it gets the hidden surfaces' tint. An entry can be
//                  [name, sameTintAs] to give it another own material's tint (a board round a notice); []
// Unlit (Basic) meshes, such as a sky card, are left out of the calibration drawings, so a big card
// does not sway the match; its colour is the page's to set (divide by fallbackTint and
// uniforms.projectionUnlitLift to see a colour exactly where the painting does not reach).
// Returns { projector, materials, uniforms, fallbackTint (the unseen surfaces' tint), ownTints (name -> tint), visibility (the distance map), refresh()
// (draw the distance map again after the set moves), setStrength(k) (0 = no painting),
// showWeights(on) (debug: orange = painting, blue = own surface), dispose() }.
export function projectPaintingOnto(kit, setGroup, painting, projector, options = {}) {
  const {
    mapSize = 2048, bias = 0.004, jump = 0.03, edgeWidth = 0.006, stretch = [2.5, 5], moveAngle = 0.01, frameEdge = 0.03,
    darken = 0.75, darkenUnlit = 1, tint = 0.6, fill = 0.35, calibrate = true, matte = true, ownSurface = [], behind = null,
  } = options;
  const ownNames = ownSurface.map((entry) => (Array.isArray(entry) ? entry[0] : entry));
  const sameTintAs = new Map(ownSurface.filter(Array.isArray).map(([name, other]) => [name, other]));
  const averageColour = options.averageColour ?? (calibrate ? null : averageColourOf(painting));
  const camera = projector.isPerspectiveCamera ? projector : projectorCamera(projector);
  camera.updateMatrixWorld(true);
  camera.updateProjectionMatrix();
  painting.wrapS = painting.wrapT = THREE.ClampToEdgeWrapping;

  const height = mapSize, width = Math.round(mapSize * camera.aspect);
  const distances = distanceTarget(width, height, true);
  const jumps = distanceTarget(width, height, false);
  const visibility = distanceTarget(width, height, false);
  const behindVisibility = behind ? distanceTarget(width, height, false) : null;
  const nearZone = behind ? distanceTarget(width, height, false) : null;
  if (behind) behind.painting.wrapS = behind.painting.wrapT = THREE.ClampToEdgeWrapping;

  const fallbackTint = new THREE.Vector3(darken, darken, darken);
  if (averageColour) {
    const luminance = 0.2126 * averageColour.r + 0.7152 * averageColour.g + 0.0722 * averageColour.b;
    const towardPainting = new THREE.Vector3(averageColour.r, averageColour.g, averageColour.b).divideScalar(Math.max(1e-4, luminance));
    fallbackTint.set(1, 1, 1).lerp(towardPainting, tint).multiplyScalar(darken);
  }
  const uniforms = {
    projectionPainting: { value: painting },
    projectionVisibility: { value: visibility.texture },
    projectorViewProjection: { value: new THREE.Matrix4() },
    projectorPosition: { value: new THREE.Vector3() },
    projectorTexelAngle: { value: 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / height },
    projectionBias: { value: bias },
    projectionStretch: { value: new THREE.Vector2(...stretch) },
    projectionMoveAngle: { value: moveAngle },
    projectionFallbackTint: { value: fallbackTint },
    projectionStrength: { value: 1 },
    projectionShowWeights: { value: 0 },
    projectionFrameEdge: { value: frameEdge },
    projectionFill: { value: fill },
    projectionUnlitLift: { value: darkenUnlit / Math.max(1e-3, darken) },
    ...(behind ? { projectionBehindPainting: { value: behind.painting }, projectionBehindVisibility: { value: behindVisibility.texture },
      projectionNearZone: { value: nearZone.texture }, projectionQuickMove: { value: behind.quickMove ?? 0.00003 },
      projectionFrontStretch: { value: new THREE.Vector2(...(behind.frontStretch ?? [1.3, 1.9])) } } : {}),
  };
  // the meshes of the near props the behind painting leaves out
  const hiddenInBehind = new Set();
  for (const object of behind?.hide ?? []) object.traverse((o) => { if (o.isMesh) hiddenInBehind.add(o); });

  // the distance map: the set alone, from the projector, then its outlines and their bands (and the
  // same without the near props, for the behind painting)
  const refresh = () => {
    const started = performance.now();
    camera.updateMatrixWorld(true);
    uniforms.projectorViewProjection.value.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    uniforms.projectorPosition.value.setFromMatrixPosition(camera.matrixWorld);
    drawDistanceMap(visibility, []);
    if (behind) {
      drawDistanceMap(behindVisibility, [...hiddenInBehind]);
      const previousTarget = renderer.getRenderTarget();
      zoneMaterial.uniforms.withProps.value = visibility.texture;
      zoneMaterial.uniforms.withoutProps.value = behindVisibility.texture;
      zoneMaterial.uniforms.texel.value.set(1 / width, 1 / height);
      zoneMaterial.uniforms.jump.value = jump;
      // in two steps, like the outline band: a narrow zone first (thin props such as a cart's
      // handles are only a few texels wide, and the wide pass's 13 x 13 points would miss them),
      // then the wide one round it (the distance picture is free by now, so it holds the narrow zone)
      zoneMaterial.uniforms.useMask.value = 0;
      zoneMaterial.uniforms.radius.value = 8;
      runPass(zoneMaterial, distances);
      zoneMaterial.uniforms.useMask.value = 1;
      zoneMaterial.uniforms.mask.value = distances.texture;
      zoneMaterial.uniforms.radius.value = Math.max(1, (behind.reach ?? 0.05) * height);
      runPass(zoneMaterial, nearZone);
      renderer.setRenderTarget(previousTarget);
    }
    return performance.now() - started;
  };
  const drawDistanceMap = (result, leftOut) => {
    const parent = setGroup.parent;
    setGroup.updateMatrixWorld(true);
    const holder = new THREE.Group();   // keeps the set where its parent puts it while drawn alone
    holder.matrixAutoUpdate = false;
    if (parent) { parent.updateMatrixWorld(true); holder.matrix.copy(parent.matrixWorld); }
    const alone = new THREE.Scene();
    alone.overrideMaterial = distanceMaterial;
    alone.add(holder);
    holder.add(setGroup);
    const hidden = leftOut.map((o) => [o, o.visible]);
    for (const o of leftOut) o.visible = false;
    setGroup.traverse((o) => { if (o.isPoints || o.isLine || o.isSprite) { hidden.push([o, o.visible]); o.visible = false; } });
    const previousTarget = renderer.getRenderTarget(), previousClear = renderer.getClearColor(new THREE.Color()), previousAlpha = renderer.getClearAlpha();
    const previousShadows = renderer.shadowMap.autoUpdate;
    renderer.shadowMap.autoUpdate = false;
    renderer.setClearColor(new THREE.Color(1e6, 0, 0), 1);   // nothing there: infinitely far
    renderer.setRenderTarget(distances);
    renderer.clear();
    renderer.render(alone, camera);
    renderer.setClearColor(previousClear, previousAlpha);
    renderer.shadowMap.autoUpdate = previousShadows;
    for (const [o, visible] of hidden) o.visible = visible;
    holder.remove(setGroup);
    if (parent) parent.add(setGroup);
    setGroup.updateMatrixWorld(true);

    const texel = new THREE.Vector2(1 / width, 1 / height);
    jumpMaterial.uniforms.distanceMap.value = distances.texture;
    jumpMaterial.uniforms.texel.value.copy(texel);
    jumpMaterial.uniforms.jump.value = jump;
    runPass(jumpMaterial, jumps);
    bandMaterial.uniforms.texel.value.copy(texel);
    bandMaterial.uniforms.sameSurface.value = jump;
    const radius = Math.max(1, edgeWidth * height);
    if (radius > 8) {
      // a wide band in two steps: the band pass looks at 13 x 13 points round each texel, which at a
      // wide reach fall between the one-texel outline marks; a narrow band first gives the wide pass
      // thick marks to find (the distance picture is free by now, so it holds the narrow band)
      bandMaterial.uniforms.jumpMap.value = jumps.texture;
      bandMaterial.uniforms.radius.value = 6;
      runPass(bandMaterial, distances);
      bandMaterial.uniforms.jumpMap.value = distances.texture;
    } else {
      bandMaterial.uniforms.jumpMap.value = jumps.texture;
    }
    bandMaterial.uniforms.radius.value = radius;
    runPass(bandMaterial, result);
    renderer.setRenderTarget(previousTarget);
  };

  // materials worn by the near props never use the behind painting (it has the props painted out)
  const frontMaterials = new Set();
  for (const mesh of hiddenInBehind) for (const m of [mesh.material].flat()) frontMaterials.add(m);
  const materials = new Map();   // one projected material for each original material
  const ownTints = new Map();    // material name -> { value: tint } for the ownSurface materials
  const ownMeshes = new Map();   // material name -> the meshes wearing it (for their outline)
  setGroup.traverse((o) => {
    if (!o.isMesh) return;
    const swap = (m) => {
      const own = ownNames.includes(m.name);
      if (own) {
        if (!ownTints.has(m.name)) ownTints.set(m.name, { value: fallbackTint.clone() });
        if (!ownMeshes.has(m.name)) ownMeshes.set(m.name, new Set());
        ownMeshes.get(m.name).add(o);
      }
      if (!materials.has(m)) materials.set(m, projectedVersion(m, uniforms, matte, own ? ownTints.get(m.name) : null, behind && !frontMaterials.has(m), frontMaterials.has(m)));
      return materials.get(m);
    };
    o.material = Array.isArray(o.material) ? o.material.map(swap) : swap(o.material);
  });
  const missing = ownNames.filter((name) => !ownTints.has(name));
  if (missing.length) console.warn(`projected-set: ownSurface names not found on the set: ${missing.join(', ')}`);
  const drawMilliseconds = refresh();

  // matching the unseen surfaces to the painting: the set drawn small from the projector, once
  // wearing the painting and once wearing only its own lit surfaces; the ratio of the two averages
  // (per colour, pulled toward an even change by 1 - tint) times `darken` becomes their tint
  let calibration = '';
  if (calibrate) {
    const float = renderer.extensions.has('EXT_color_buffer_float');
    const small = new THREE.WebGLRenderTarget(270, Math.max(1, Math.round(270 / camera.aspect)), {
      type: float ? THREE.FloatType : THREE.HalfFloatType, colorSpace: THREE.NoColorSpace, depthBuffer: true,
    });
    const scene = kit.scene, background = scene.background;
    const previousTarget = renderer.getRenderTarget(), previousClear = renderer.getClearColor(new THREE.Color()), previousAlpha = renderer.getClearAlpha();
    // the drawing's pixels, and the average over a box of them ([x0, y0, x1, y1] in 0..1, y up)
    const draw = () => {
      renderer.setRenderTarget(small);
      renderer.render(scene, camera);
      const count = small.width * small.height * 4;
      const raw = float ? new Float32Array(count) : new Uint16Array(count);
      renderer.readRenderTargetPixels(small, 0, 0, small.width, small.height, raw);
      return float ? raw : Float32Array.from(raw, (v) => THREE.DataUtils.fromHalfFloat(v));
    };
    const averageOf = (pixels, box = [0, 0, 1, 1]) => {
      const [x0, y0, x1, y1] = [Math.floor(box[0] * small.width), Math.floor(box[1] * small.height), Math.ceil(box[2] * small.width), Math.ceil(box[3] * small.height)];
      const sum = [0, 0, 0]; let covered = 0;
      for (let y = Math.max(0, y0); y < Math.min(small.height, y1); y++) {
        for (let x = Math.max(0, x0); x < Math.min(small.width, x1); x++) {
          const i = (y * small.width + x) * 4;
          if (pixels[i + 3] < 0.5) continue;
          covered++;
          for (let c = 0; c < 3; c++) sum[c] += Math.min(4, pixels[i + c]);
        }
      }
      return covered ? sum.map((v) => v / covered) : null;
    };
    // the middle of each own material's outline, as the projector sees it (its bounding box's
    // corners, projected; the middle 60%, so the box's edges and what shows round it count little)
    const ownBoxes = new Map();
    for (const [name, meshes] of ownMeshes) {
      if (sameTintAs.has(name)) continue;
      const box = new THREE.Box3();
      for (const mesh of meshes) box.expandByObject(mesh);
      const corner = new THREE.Vector3(), lo = [Infinity, Infinity], hi = [-Infinity, -Infinity];
      for (let k = 0; k < 8; k++) {
        corner.set(k & 1 ? box.max.x : box.min.x, k & 2 ? box.max.y : box.min.y, k & 4 ? box.max.z : box.min.z).project(camera);
        const u = corner.x * 0.5 + 0.5, v = corner.y * 0.5 + 0.5;
        lo[0] = Math.min(lo[0], u); lo[1] = Math.min(lo[1], v); hi[0] = Math.max(hi[0], u); hi[1] = Math.max(hi[1], v);
      }
      const shrink = (a, b) => [a + (b - a) * 0.2, a + (b - a) * 0.8];
      const [x0, x1] = shrink(lo[0], hi[0]), [y0, y1] = shrink(lo[1], hi[1]);
      if (x1 > 0 && x0 < 1 && y1 > 0 && y0 < 1) ownBoxes.set(name, [x0, y0, x1, y1]);
    }
    // the painting's own colour over a box (linear light, as the projection shows it)
    const paintingAverage = (box) => {
      const image = painting.image;
      if (!image || !(image.width > 0)) return null;
      const canvas = new OffscreenCanvas(small.width, small.height), context = canvas.getContext('2d');
      context.drawImage(image, 0, 0, small.width, small.height);
      const data = context.getImageData(0, 0, small.width, small.height).data;
      const toLinear = (value) => { const c = value / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
      const sum = [0, 0, 0]; let count = 0;
      for (let y = Math.max(0, Math.floor(box[1] * small.height)); y < Math.min(small.height, Math.ceil(box[3] * small.height)); y++) {
        const row = small.height - 1 - y;   // the picture's rows run top down; the box's y runs up
        for (let x = Math.max(0, Math.floor(box[0] * small.width)); x < Math.min(small.width, Math.ceil(box[2] * small.width)); x++) {
          const i = (row * small.width + x) * 4;
          count++;
          for (let c = 0; c < 3; c++) sum[c] += toLinear(data[i + c]);
        }
      }
      return count ? sum.map((v) => v / count) : null;
    };
    // unlit cards (a sky) are left out of both drawings
    const unlit = [];
    setGroup.traverse((o) => {
      if (o.isMesh && o.visible && [o.material].flat().every((m) => m.defines && 'PROJECTION_UNLIT' in m.defines)) { unlit.push(o); o.visible = false; }
    });
    scene.background = null;
    renderer.setClearColor(0x000000, 0);
    const paint = averageOf(draw()) ?? [1, 1, 1];
    uniforms.projectionStrength.value = 0;
    uniforms.projectionFallbackTint.value.set(1, 1, 1);
    for (const tintUniform of ownTints.values()) tintUniform.value.set(1, 1, 1);
    const ownPixels = draw();
    const own = averageOf(ownPixels) ?? [1, 1, 1];
    for (const [name, box] of ownBoxes) {
      const painted = paintingAverage(box), lit = averageOf(ownPixels, box);
      if (!painted || !lit) continue;
      ownTints.get(name).value.set(...painted.map((v, c) => Math.min(8, Math.max(0.05, v / Math.max(1e-4, lit[c])))));
    }
    uniforms.projectionStrength.value = 1;
    for (const o of unlit) o.visible = true;
    scene.background = background;
    renderer.setClearColor(previousClear, previousAlpha);
    renderer.setRenderTarget(previousTarget);
    small.dispose();
    const ratio = paint.map((v, c) => v / Math.max(1e-4, own[c]));
    const even = (ratio[0] + ratio[1] + ratio[2]) / 3;
    fallbackTint.set(...ratio.map((r) => Math.min(8, Math.max(0.05, darken * (tint * r + (1 - tint) * even)))));
    // own surfaces the projector could not see (outside its frame) take the hidden surfaces' tint
    for (const [name, tintUniform] of ownTints) if (!ownBoxes.has(name)) tintUniform.value.copy(fallbackTint);
    for (const [name, other] of sameTintAs) if (ownTints.has(name) && ownTints.has(other)) ownTints.get(name).value.copy(ownTints.get(other).value);
    calibration = ` (painting average ${paint.map((v) => v.toFixed(3)).join(', ')}, own surfaces ${own.map((v) => v.toFixed(3)).join(', ')})`;
  }
  const ownReport = [...ownTints].map(([name, t]) => ` ${name} ${t.value.toArray().map((v) => v.toFixed(2)).join(', ')}`).join(';')
    + (behind ? `; behind painting: ${hiddenInBehind.size} prop meshes left out, their ${frontMaterials.size} materials: ${[...frontMaterials].map((m) => m.name).join(', ')}` : '');
  console.warn(`projected-set: distance map ${width} x ${height} (${distances.texture.type === THREE.FloatType ? '32' : '16'}-bit) drawn in ${drawMilliseconds.toFixed(0)} ms; ${materials.size} materials; hidden surfaces tinted ${fallbackTint.toArray().map((v) => v.toFixed(2)).join(', ')}${calibration}${ownReport ? `; own surfaces tinted${ownReport}` : ''}`);

  return {
    projector: camera, materials: [...materials.values()], uniforms, fallbackTint, visibility, refresh,
    ownTints: new Map([...ownTints].map(([name, t]) => [name, t.value])),
    setStrength: (k) => { uniforms.projectionStrength.value = k; },
    showWeights: (on) => { uniforms.projectionShowWeights.value = on ? 1 : 0; },
    behindVisibility,
    dispose: () => { distances.dispose(); jumps.dispose(); visibility.dispose(); behindVisibility?.dispose(); nearZone?.dispose(); for (const m of materials.values()) m.dispose(); },
  };
}
