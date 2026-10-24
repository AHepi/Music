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
  // How much of the painting this point wears (0..1), and the painting's colour there.
  float projectionWeight(out vec3 paintColour) {
    vec4 clip = projectorViewProjection * vec4(vProjectionWorld, 1.0);
    vec2 at = clip.xy / max(clip.w, 1e-4) * 0.5 + 0.5;
    // (both pictures are read before any early return, so the painting's mipmaps stay smooth)
    paintColour = texture2D(projectionPainting, clamp(at, 0.0, 1.0)).rgb;
    vec2 visibility = texture2D(projectionVisibility, clamp(at, 0.0, 1.0)).rg;
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
    seen *= 1.0 - smoothstep(projectionStretch.x, projectionStretch.y, stretch);
    seen *= smoothstep(0.0, 0.004, facingProjector);
    // the far side of a near thing's outline
    seen *= 1.0 - visibility.g * moved;
    // the projector's frame edge: a hard cut from the projector's view, a soft band once moved
    vec2 fromEdge = min(at, 1.0 - at);
    seen *= mix(1.0, smoothstep(0.0, projectionFrameEdge, min(fromEdge.x, fromEdge.y)), moved);
    return seen * projectionStrength;
  }`;
const FRAGMENT_MAP = `
  #include <map_fragment>
  vec3 projectionPaint;
  float projectionAmount = projectionWeight(projectionPaint);
  diffuseColor.rgb *= projectionFallbackTint;   // its own surface, darkened and tinted toward the painting
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
  if (projectionShowWeights > 0.5) gl_FragColor.rgb = mix(vec3(0.05, 0.12, 0.5), vec3(1.0, 0.55, 0.15), projectionAmount) * (0.35 + 0.65 * dot(gl_FragColor.rgb, vec3(0.3, 0.59, 0.11)) / max(0.05, dot(projectionPaint, vec3(0.3, 0.59, 0.11)) + 0.05));`;

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
function projectedVersion(material, uniforms, matte) {
  // unlit (Basic) materials stay unlit: a painted sky card, a glowing sign
  const keepKind = material.isMeshBasicMaterial || material.isMeshLambertMaterial || material.isMeshPhongMaterial || material.isMeshStandardMaterial;
  const projected = keepKind && !(matte && material.isMeshStandardMaterial) ? material.clone() : matteCopy(material);
  if (projected.isMeshBasicMaterial) projected.defines = { ...(projected.defines ?? {}), PROJECTION_UNLIT: '' };
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
  projected.customProgramCacheKey = () => `projected-set-2|${material.customProgramCacheKey?.() ?? ''}`;
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
// Returns { projector, materials, uniforms, fallbackTint (the unseen surfaces' tint), visibility (the distance map), refresh()
// (draw the distance map again after the set moves), setStrength(k) (0 = no painting),
// showWeights(on) (debug: orange = painting, blue = own surface), dispose() }.
export function projectPaintingOnto(kit, setGroup, painting, projector, options = {}) {
  const {
    mapSize = 2048, bias = 0.004, jump = 0.03, edgeWidth = 0.006, stretch = [2.5, 5], moveAngle = 0.01, frameEdge = 0.03,
    darken = 0.75, darkenUnlit = 1, tint = 0.6, fill = 0.35, calibrate = true, matte = true,
  } = options;
  const averageColour = options.averageColour ?? (calibrate ? null : averageColourOf(painting));
  const camera = projector.isPerspectiveCamera ? projector : projectorCamera(projector);
  camera.updateMatrixWorld(true);
  camera.updateProjectionMatrix();
  painting.wrapS = painting.wrapT = THREE.ClampToEdgeWrapping;

  const height = mapSize, width = Math.round(mapSize * camera.aspect);
  const distances = distanceTarget(width, height, true);
  const jumps = distanceTarget(width, height, false);
  const visibility = distanceTarget(width, height, false);

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
  };

  // the distance map: the set alone, from the projector, then its outlines and their bands
  const refresh = () => {
    const started = performance.now();
    camera.updateMatrixWorld(true);
    uniforms.projectorViewProjection.value.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    uniforms.projectorPosition.value.setFromMatrixPosition(camera.matrixWorld);
    const parent = setGroup.parent;
    setGroup.updateMatrixWorld(true);
    const holder = new THREE.Group();   // keeps the set where its parent puts it while drawn alone
    holder.matrixAutoUpdate = false;
    if (parent) { parent.updateMatrixWorld(true); holder.matrix.copy(parent.matrixWorld); }
    const alone = new THREE.Scene();
    alone.overrideMaterial = distanceMaterial;
    alone.add(holder);
    holder.add(setGroup);
    const hidden = [];
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
    bandMaterial.uniforms.jumpMap.value = jumps.texture;
    bandMaterial.uniforms.texel.value.copy(texel);
    bandMaterial.uniforms.radius.value = Math.max(1, edgeWidth * height);
    bandMaterial.uniforms.sameSurface.value = jump;
    runPass(bandMaterial, visibility);
    renderer.setRenderTarget(previousTarget);
    return performance.now() - started;
  };

  const materials = new Map();   // one projected material for each original material
  setGroup.traverse((o) => {
    if (!o.isMesh) return;
    const swap = (m) => {
      if (!materials.has(m)) materials.set(m, projectedVersion(m, uniforms, matte));
      return materials.get(m);
    };
    o.material = Array.isArray(o.material) ? o.material.map(swap) : swap(o.material);
  });
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
    const average = () => {
      renderer.setRenderTarget(small);
      renderer.render(scene, camera);
      const count = small.width * small.height * 4;
      const raw = float ? new Float32Array(count) : new Uint16Array(count);
      renderer.readRenderTargetPixels(small, 0, 0, small.width, small.height, raw);
      const value = float ? (i) => raw[i] : (i) => THREE.DataUtils.fromHalfFloat(raw[i]);
      const sum = [0, 0, 0]; let covered = 0;
      for (let i = 0; i < count; i += 4) {
        if (value(i + 3) < 0.5) continue;
        covered++;
        for (let c = 0; c < 3; c++) sum[c] += Math.min(4, value(i + c));
      }
      return sum.map((v) => v / Math.max(1, covered));
    };
    scene.background = null;
    renderer.setClearColor(0x000000, 0);
    const paint = average();
    uniforms.projectionStrength.value = 0;
    uniforms.projectionFallbackTint.value.set(1, 1, 1);
    const own = average();
    uniforms.projectionStrength.value = 1;
    scene.background = background;
    renderer.setClearColor(previousClear, previousAlpha);
    renderer.setRenderTarget(previousTarget);
    small.dispose();
    const ratio = paint.map((v, c) => v / Math.max(1e-4, own[c]));
    const even = (ratio[0] + ratio[1] + ratio[2]) / 3;
    fallbackTint.set(...ratio.map((r) => Math.min(8, Math.max(0.05, darken * (tint * r + (1 - tint) * even)))));
    calibration = ` (painting average ${paint.map((v) => v.toFixed(3)).join(', ')}, own surfaces ${own.map((v) => v.toFixed(3)).join(', ')})`;
  }
  console.warn(`projected-set: distance map ${width} x ${height} (${distances.texture.type === THREE.FloatType ? '32' : '16'}-bit) drawn in ${drawMilliseconds.toFixed(0)} ms; ${materials.size} materials; hidden surfaces tinted ${fallbackTint.toArray().map((v) => v.toFixed(2)).join(', ')}${calibration}`);

  return {
    projector: camera, materials: [...materials.values()], uniforms, fallbackTint, visibility, refresh,
    setStrength: (k) => { uniforms.projectionStrength.value = k; },
    showWeights: (on) => { uniforms.projectionShowWeights.value = on ? 1 : 0; },
    dispose: () => { distances.dispose(); jumps.dispose(); visibility.dispose(); for (const m of materials.values()) m.dispose(); },
  };
}
