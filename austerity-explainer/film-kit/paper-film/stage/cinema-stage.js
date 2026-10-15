// What this does: the cinema stage. It films pages that are small 3D worlds (a painting given depth,
// paper figures and card models standing in it, moving labels and charts) through a camera with a
// real lens: focus that blurs what is near or far, glow around bright lights, film colour, a dark
// edge to the frame and fine grain. It also joins one page to the next (the page peels away like a
// book page, or the two pictures dissolve into each other).
//
// How the pieces fit:
//   - a page (scenes/<chapter>/page-N.js, through cinema-kit.js) owns a THREE.Scene, a camera and its
//     lights, and says for any moment where everything is, where the camera looks and what is in focus.
//   - this file draws one page's moment in four steps: the 3D world into a picture with its distances
//     (depth), the focus blur, the glow, and the finishing (exposure, film colour, words and charts
//     drawn on top, dark edges, grain). The result is one frame.
//   - during a join, it draws both pages and lays the old one over the new as a peeling paper sheet
//     (or blends them).
//   - cinema-chapter.js decides which page is showing when; this file only draws.
//
// The page calls window.renderFrame(seconds) and gets back one finished frame as a JPEG.

import * as THREE from '/paper-film/node_modules/three/build/three.module.js';

export { THREE };
export const FRAME_WIDTH = 1080;
export const FRAME_HEIGHT = 1920;

export const renderer = new THREE.WebGLRenderer({
  canvas: document.getElementById('stage'), antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance',
});
renderer.setPixelRatio(1);
renderer.setSize(FRAME_WIDTH, FRAME_HEIGHT, false);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // the finishing step does its own colour
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.autoClear = true;

// ------------------------------------------------------------------------------- render targets
function makeTarget(width, height, { depth = false, samples = 0, type = THREE.HalfFloatType } = {}) {
  const target = new THREE.WebGLRenderTarget(width, height, {
    type, format: THREE.RGBAFormat, colorSpace: THREE.LinearSRGBColorSpace, samples,
    minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: depth,
  });
  if (depth) {
    target.depthTexture = new THREE.DepthTexture(width, height);
    target.depthTexture.type = THREE.FloatType;
  }
  return target;
}
const W = FRAME_WIDTH, H = FRAME_HEIGHT;
// edge smoothing (multisampling): 4 samples a pixel by default; ?samples=0 turns it off (about how much faster: see
// tools/profile_frame.mjs); a filming run can set it with PAPER_FILM_QUERY=samples=N
const SCENE_SAMPLES = Number(new URLSearchParams(location.search).get('samples') ?? 4);
const sceneTarget = makeTarget(W, H, { depth: true, samples: SCENE_SAMPLES });
const blurTarget = makeTarget(W / 2, H / 2);
const focusTarget = makeTarget(W, H);
const brightTarget = makeTarget(W / 4, H / 4);
const glowTargets = [makeTarget(W / 4, H / 4), makeTarget(W / 4, H / 4), makeTarget(W / 8, H / 8), makeTarget(W / 8, H / 8)];
export const pageTargets = [makeTarget(W, H, { type: THREE.UnsignedByteType }), makeTarget(W, H, { type: THREE.UnsignedByteType })];

// ------------------------------------------------------------------- held shots: the set drawn once
// Drawing a painted set is the slow part of a frame in the software renderer (log 34: 3.1 of 3.6 seconds a frame
// on the notice corner; plain grey surfaces take 0.2). While a page's camera holds still, its set looks the same
// every frame, so it is drawn once into a held picture (with its distances), and each frame only the moving
// things are drawn over a copy of it. A page marks its moving things with kit.moving(...) (they live on
// MOVING_LAYER; everything else is the set) and asks for this by returning `still: true` (or any value that
// changes when the set itself changes) from pose(t); the chapter adds the camera's place to the key, so a
// moving camera always draws everything. Two held pictures are kept, for the two pages of a page turn.
export const MOVING_LAYER = 1;
const heldPictures = [0, 1].map(() => ({ key: null, target: makeTarget(W, H, { depth: true, samples: SCENE_SAMPLES }), used: 0 }));
let heldClock = 0;
const heldCopyMaterial = new THREE.ShaderMaterial({
  vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: `varying vec2 vUv; uniform sampler2D colourMap; uniform sampler2D depthMap;
    void main() { gl_FragColor = texture2D(colourMap, vUv); gl_FragDepth = texture2D(depthMap, vUv).r; }`,
  uniforms: { colourMap: { value: null }, depthMap: { value: null } },
  depthTest: true, depthWrite: true, depthFunc: THREE.AlwaysDepth,
});
function drawSet(scene, camera, still) {
  camera.layers.enable(0);
  camera.layers.enable(MOVING_LAYER);
  if (still === null || still === undefined) {
    renderer.setRenderTarget(sceneTarget);
    renderer.render(scene, camera);
    return;
  }
  heldClock++;
  let held = heldPictures.find((h) => h.key === still);
  if (!held) {
    held = heldPictures.reduce((a, b) => (a.used <= b.used ? a : b));
    // the lights must reach the moving things too
    scene.traverse((o) => { if (o.isLight) o.layers.enable(MOVING_LAYER); });
    camera.layers.set(0);
    renderer.setRenderTarget(held.target);
    renderer.render(scene, camera);
    held.key = still;
  }
  held.used = heldClock;
  // the held set (colour and distances), then the moving things over it
  heldCopyMaterial.uniforms.colourMap.value = held.target.texture;
  heldCopyMaterial.uniforms.depthMap.value = held.target.depthTexture;
  passQuad.material = heldCopyMaterial;
  renderer.setRenderTarget(sceneTarget);
  renderer.render(passScene, passCamera);
  camera.layers.set(MOVING_LAYER);
  const shadowsUpdate = renderer.shadowMap.autoUpdate;
  renderer.shadowMap.autoUpdate = false;
  const background = scene.background;
  scene.background = null;
  renderer.autoClear = false;
  renderer.render(scene, camera);
  renderer.autoClear = true;
  scene.background = background;
  renderer.shadowMap.autoUpdate = shadowsUpdate;
  camera.layers.enable(0);
}

// ----------------------------------------------------------------------------- full-frame passes
const passCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const passScene = new THREE.Scene();
const passQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), null);
passQuad.frustumCulled = false;
passScene.add(passQuad);
function runPass(material, target) {
  passQuad.material = material;
  renderer.setRenderTarget(target);
  renderer.render(passScene, passCamera);
}
const passVertex = /* glsl */`
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
const pass = (fragmentShader, uniforms) => new THREE.ShaderMaterial({ vertexShader: passVertex, fragmentShader, uniforms, depthTest: false, depthWrite: false });

// How far from the camera a pixel is, and how blurred it should be (its circle of confusion, in pixels).
const depthHelpers = /* glsl */`
  uniform sampler2D depthMap; uniform float cameraNear; uniform float cameraFar;
  uniform float focusDistance; uniform float aperture; uniform float maxBlur;
  float viewDistance(vec2 uv) {
    float d = texture2D(depthMap, uv).x;
    float z = d * 2.0 - 1.0;
    return (2.0 * cameraNear * cameraFar) / (cameraFar + cameraNear - z * (cameraFar - cameraNear));
  }
  float blurPixels(float distance) {
    // a lens: blur grows with how far a point is from the focus, relative to its distance;
    // aperture = how many pixels wide a point at a great distance is blurred
    float coc = aperture * abs(distance - focusDistance) / max(distance, 0.001);
    return min(maxBlur, coc);
  }`;

// 1. the focus blur, worked out at half size: each pixel gathers from a disc as wide as its own blur,
//    taking only neighbours that are themselves at least that blurred (so sharp things keep their edges).
const blurMaterial = pass(/* glsl */`
  varying vec2 vUv;
  uniform sampler2D colourMap; uniform vec2 texel;
  ${depthHelpers}
  const int TAPS = 28;
  void main() {
    float centreBlur = blurPixels(viewDistance(vUv));
    vec3 sum = texture2D(colourMap, vUv).rgb; float weight = 1.0;
    float radius = centreBlur;
    for (int i = 0; i < TAPS; i++) {
      float f = (float(i) + 0.5) / float(TAPS);
      float r = sqrt(f) * radius;
      float a = float(i) * 2.39996323;
      vec2 offset = vec2(cos(a), sin(a)) * r * texel;
      vec2 uv = vUv + offset;
      float tapBlur = blurPixels(viewDistance(uv));
      float w = smoothstep(r - 1.5, r + 0.5, max(tapBlur, centreBlur * 0.6));
      sum += texture2D(colourMap, uv).rgb * w; weight += w;
    }
    gl_FragColor = vec4(sum / weight, centreBlur);
  }`, {
  colourMap: { value: null }, depthMap: { value: null }, texel: { value: new THREE.Vector2(1 / W, 1 / H) },
  cameraNear: { value: 0.1 }, cameraFar: { value: 100 }, focusDistance: { value: 10 }, aperture: { value: 0 }, maxBlur: { value: 18 },
});

// 2. sharp where in focus, blurred where not
const focusMaterial = pass(/* glsl */`
  varying vec2 vUv;
  uniform sampler2D colourMap; uniform sampler2D blurMap;
  ${depthHelpers}
  void main() {
    vec3 sharp = texture2D(colourMap, vUv).rgb;
    vec4 blurred = texture2D(blurMap, vUv);
    float coc = blurPixels(viewDistance(vUv));
    float k = smoothstep(0.6, 2.2, coc);
    gl_FragColor = vec4(mix(sharp, blurred.rgb, k), 1.0);
  }`, {
  colourMap: { value: null }, blurMap: { value: null }, depthMap: { value: null },
  cameraNear: { value: 0.1 }, cameraFar: { value: 100 }, focusDistance: { value: 10 }, aperture: { value: 0 }, maxBlur: { value: 18 },
});

// 3. glow: the brightest parts, spread out softly
const brightMaterial = pass(/* glsl */`
  varying vec2 vUv; uniform sampler2D colourMap; uniform float threshold; uniform float exposure;
  void main() {
    vec3 c = texture2D(colourMap, vUv).rgb * exposure;
    float brightness = max(c.r, max(c.g, c.b));
    float knee = 0.35;
    float soft = clamp(brightness - threshold + knee, 0.0, 2.0 * knee);
    soft = soft * soft / (4.0 * knee + 1e-4);
    float amount = max(soft, brightness - threshold) / max(brightness, 1e-4);
    gl_FragColor = vec4(c * amount, 1.0);
  }`, { colourMap: { value: null }, threshold: { value: 1.0 }, exposure: { value: 1 } });
const glowBlurMaterial = pass(/* glsl */`
  varying vec2 vUv; uniform sampler2D colourMap; uniform vec2 direction;
  void main() {
    vec3 sum = texture2D(colourMap, vUv).rgb * 0.2270270270;
    sum += texture2D(colourMap, vUv + direction * 1.3846153846).rgb * 0.3162162162;
    sum += texture2D(colourMap, vUv - direction * 1.3846153846).rgb * 0.3162162162;
    sum += texture2D(colourMap, vUv + direction * 3.2307692308).rgb * 0.0702702703;
    sum += texture2D(colourMap, vUv - direction * 3.2307692308).rgb * 0.0702702703;
    gl_FragColor = vec4(sum, 1.0);
  }`, { colourMap: { value: null }, direction: { value: new THREE.Vector2() } });

// 4. the finish: exposure, glow, a filmic curve, film colour (cool shadows, warm lights), a touch of
//    colour fringing at the edges, words and charts on top, dark edges and grain. Output is sRGB.
const finishMaterial = pass(/* glsl */`
  varying vec2 vUv;
  uniform sampler2D colourMap; uniform sampler2D glowNear; uniform sampler2D glowFar; uniform sampler2D overlayMap;
  uniform float useOverlay; uniform float exposure; uniform float glowStrength; uniform float contrast; uniform float saturation;
  uniform vec3 shadowTint; uniform vec3 highlightTint; uniform float tintAmount;
  uniform float vignette; uniform float grain; uniform float fringe; uniform float seed; uniform float lift; uniform float fade;
  vec3 aces(vec3 x) { return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
  float hash(vec2 p) { p = fract(p * vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y) * p.x); }
  vec3 toSrgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
  void main() {
    vec2 centred = vUv - 0.5;
    vec2 shift = centred * fringe * dot(centred, centred);
    vec3 c;
    c.r = texture2D(colourMap, vUv - shift).r;
    c.g = texture2D(colourMap, vUv).g;
    c.b = texture2D(colourMap, vUv + shift).b;
    c *= exposure;
    c += (texture2D(glowNear, vUv).rgb * 0.6 + texture2D(glowFar, vUv).rgb * 0.8) * glowStrength;
    c = aces(c);
    float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
    c = mix(vec3(luma), c, saturation);
    c = (c - 0.5) * contrast + 0.5;
    vec3 tint = mix(shadowTint, highlightTint, smoothstep(0.05, 0.75, luma));
    c = mix(c, c * tint * 2.0, tintAmount);
    c = c + lift * (1.0 - c);
    c = clamp(c, 0.0, 1.0);
    vec3 outColour = toSrgb(c);
    if (useOverlay > 0.5) {
      vec4 o = texture2D(overlayMap, vUv);
      outColour = outColour * (1.0 - o.a) + o.rgb;
    }
    float edge = smoothstep(0.85, 0.2, length(centred * vec2(0.9, 1.0)) * 1.25);
    outColour *= mix(1.0 - vignette, 1.0, edge);
    float n = hash(vUv * vec2(1080.0, 1920.0) + seed) - 0.5;
    outColour += n * grain * (1.0 - 0.6 * outColour);
    outColour *= (1.0 - fade);
    gl_FragColor = vec4(clamp(outColour, 0.0, 1.0), 1.0);
  }`, {
  colourMap: { value: null }, glowNear: { value: null }, glowFar: { value: null }, overlayMap: { value: null },
  useOverlay: { value: 0 }, exposure: { value: 1 }, glowStrength: { value: 0.6 }, contrast: { value: 1.04 }, saturation: { value: 1.0 },
  shadowTint: { value: new THREE.Vector3(0.44, 0.52, 0.56) }, highlightTint: { value: new THREE.Vector3(0.56, 0.5, 0.42) }, tintAmount: { value: 0.35 },
  vignette: { value: 0.32 }, grain: { value: 0.035 }, fringe: { value: 0.006 }, seed: { value: 0 }, lift: { value: 0.015 }, fade: { value: 0 },
});

// The finishing settings every page starts from; a page changes only what it needs.
export const DEFAULT_LOOK = {
  exposure: 1.0, glowStrength: 0.55, glowThreshold: 0.9, contrast: 1.05, saturation: 1.0,
  shadowTint: [0.44, 0.52, 0.56], highlightTint: [0.56, 0.5, 0.42], tintAmount: 0.35,
  vignette: 0.32, grain: 0.035, fringe: 0.006, lift: 0.015, fade: 0,
  aperture: 0.0, maxBlur: 16,
};

// The words, labels and charts drawn flat on top of the picture (each page draws its own).
export const overlayCanvas = document.createElement('canvas');
overlayCanvas.width = W; overlayCanvas.height = H;
export const overlayContext = overlayCanvas.getContext('2d', { willReadFrequently: true });
// The canvas is copied out pixel by pixel for every page (not handed to the graphics card as a
// canvas): the browser sometimes reused an old copy of the canvas when two pages were drawn in one
// frame, so one page's words showed on the next during a page turn.
const overlayPixels = new Uint8Array(W * H * 4);
const overlayTexture = new THREE.DataTexture(overlayPixels, W, H, THREE.RGBAFormat);
overlayTexture.flipY = true;
overlayTexture.magFilter = THREE.LinearFilter;
overlayTexture.colorSpace = THREE.NoColorSpace;
overlayTexture.premultiplyAlpha = true;
overlayTexture.generateMipmaps = false;
overlayTexture.minFilter = THREE.LinearFilter;

// Draws one page's moment into `target` (a finished sRGB picture), or to the screen if target is null.
// shot = { scene, camera, focusDistance, look, drawOverlay(context) | null, time }
export function drawPage(shot, target) {
  const look = { ...DEFAULT_LOOK, ...(shot.look ?? {}) };
  const { scene, camera } = shot;
  drawSet(scene, camera, shot.still);

  const depthUniforms = (material) => {
    material.uniforms.depthMap.value = sceneTarget.depthTexture;
    material.uniforms.cameraNear.value = camera.near;
    material.uniforms.cameraFar.value = camera.far;
    material.uniforms.focusDistance.value = shot.focusDistance ?? 10;
    material.uniforms.aperture.value = look.aperture;
    material.uniforms.maxBlur.value = look.maxBlur;
  };
  let colourForFinish = sceneTarget.texture;
  if (look.aperture > 0) {
    depthUniforms(blurMaterial);
    blurMaterial.uniforms.colourMap.value = sceneTarget.texture;
    blurMaterial.uniforms.texel.value.set(1 / W, 1 / H);
    runPass(blurMaterial, blurTarget);
    depthUniforms(focusMaterial);
    focusMaterial.uniforms.colourMap.value = sceneTarget.texture;
    focusMaterial.uniforms.blurMap.value = blurTarget.texture;
    runPass(focusMaterial, focusTarget);
    colourForFinish = focusTarget.texture;
  }

  brightMaterial.uniforms.colourMap.value = colourForFinish;
  brightMaterial.uniforms.threshold.value = look.glowThreshold;
  brightMaterial.uniforms.exposure.value = look.exposure;
  runPass(brightMaterial, brightTarget);
  const blurOnce = (source, target, dx, dy, size) => {
    glowBlurMaterial.uniforms.colourMap.value = source.texture;
    glowBlurMaterial.uniforms.direction.value.set(dx / size.x, dy / size.y);
    runPass(glowBlurMaterial, target);
  };
  const quarter = new THREE.Vector2(W / 4, H / 4), eighth = new THREE.Vector2(W / 8, H / 8);
  blurOnce(brightTarget, glowTargets[0], 1, 0, quarter); blurOnce(glowTargets[0], glowTargets[1], 0, 1, quarter);
  blurOnce(glowTargets[1], glowTargets[2], 1.5, 0, eighth); blurOnce(glowTargets[2], glowTargets[3], 0, 1.5, eighth);

  const u = finishMaterial.uniforms;
  u.colourMap.value = colourForFinish;
  u.glowNear.value = glowTargets[1].texture;
  u.glowFar.value = glowTargets[3].texture;
  u.exposure.value = look.exposure; u.glowStrength.value = look.glowStrength; u.contrast.value = look.contrast; u.saturation.value = look.saturation;
  u.shadowTint.value.set(...look.shadowTint); u.highlightTint.value.set(...look.highlightTint); u.tintAmount.value = look.tintAmount;
  u.vignette.value = look.vignette; u.grain.value = look.grain; u.fringe.value = look.fringe; u.lift.value = look.lift; u.fade.value = look.fade;
  u.seed.value = ((shot.time ?? 0) * 30) % 97;
  u.useOverlay.value = 0;
  if (shot.drawOverlay) {
    // start every page's graphics from a blank canvas with fresh settings: a page that leaves a
    // transform, clip or fade behind must not stop the next page's wipe (or its words would linger)
    if (overlayContext.reset) overlayContext.reset();
    else { overlayContext.setTransform(1, 0, 0, 1, 0, 0); overlayContext.globalAlpha = 1; overlayContext.globalCompositeOperation = 'source-over'; }
    overlayContext.clearRect(0, 0, W, H);
    overlayContext.save();
    const drewSomething = shot.drawOverlay(overlayContext);
    overlayContext.restore();
    if (drewSomething !== false) {
      overlayPixels.set(overlayContext.getImageData(0, 0, W, H).data);
      overlayTexture.needsUpdate = true;
      u.overlayMap.value = overlayTexture;
      u.useOverlay.value = 1;
    }
  }
  runPass(finishMaterial, target);
}

// ------------------------------------------------------------------------------- joining pages
// The old page's finished picture, printed on a sheet of paper that peels from its bottom-right
// corner, rolls over (showing its plain back) and leaves, uncovering the new page. The new page
// darkens a little where the curl hangs over it.
// The sheet's own shading (lit as paper) comes in over the first part of the peel (PEEL_SHADING_IN of
// its length, about 8 frames of a 0.85 s peel), not at once: lit as a flat sheet the whole old page is
// about 11% darker, and at once that showed as a small dimming jump on each page turn's first frame
// (log 34, round 3).
const PEEL_WIDTH = 2, PEEL_HEIGHT = 2 * H / W;   // the frame, in the join's own units
const CURL_DIRECTION = new THREE.Vector2(0.93, -0.36).normalize();
const CURL_RADIUS = 0.16;
const PEEL_SHADING_IN = 0.3;
const peelGeometry = new THREE.PlaneGeometry(PEEL_WIDTH, PEEL_HEIGHT, 48, 86);
const peelRest = peelGeometry.attributes.position.array.slice();
const peelMaterial = new THREE.ShaderMaterial({
  uniforms: { picture: { value: null }, lightDirection: { value: new THREE.Vector3(-0.45, 0.55, 0.7).normalize() }, shading: { value: 1 } },
  side: THREE.DoubleSide,
  vertexShader: /* glsl */`
    varying vec2 vUv; varying vec3 vNormal;
    void main() { vUv = uv; vNormal = normal; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */`
    varying vec2 vUv; varying vec3 vNormal; uniform sampler2D picture; uniform vec3 lightDirection; uniform float shading;
    void main() {
      vec3 n = normalize(vNormal);
      float light;
      vec3 colour;
      if (gl_FrontFacing) { light = 0.55 + 0.45 * max(0.0, dot(n, lightDirection)); colour = texture2D(picture, vUv).rgb; }
      else { light = 0.5 + 0.5 * max(0.0, dot(-n, lightDirection)); colour = vec3(0.85, 0.82, 0.76); }
      gl_FragColor = vec4(colour * mix(1.0, light, 0.85 * shading) * (gl_FrontFacing ? 1.0 : 1.0), 1.0);
    }`,
});
const peelMesh = new THREE.Mesh(peelGeometry, peelMaterial);
const underMaterial = pass(/* glsl */`
  varying vec2 vUv; uniform sampler2D picture; uniform float fold; uniform vec2 curlDirection; uniform float aspect;
  void main() {
    vec2 p = (vUv - 0.5) * vec2(2.0, 2.0 * aspect);
    float u = dot(p, curlDirection) - fold;
    float shade = 1.0 - 0.45 * smoothstep(0.55, 0.0, abs(u + 0.1)) * step(-0.6, u);
    gl_FragColor = vec4(texture2D(picture, vUv).rgb * shade, 1.0);
  }`, { picture: { value: null }, fold: { value: 0 }, curlDirection: { value: CURL_DIRECTION.clone() }, aspect: { value: H / W } });
const peelScene = new THREE.Scene();
peelScene.add(peelMesh);
const peelCamera = new THREE.PerspectiveCamera(2 * Math.atan(1 / 6) * 180 / Math.PI, W / H, 0.1, 50);
peelCamera.position.set(0, 0, 6 * (H / W));
peelCamera.lookAt(0, 0, 0);
peelCamera.fov = 2 * Math.atan((PEEL_HEIGHT / 2) / peelCamera.position.z) * 180 / Math.PI;
peelCamera.updateProjectionMatrix();
const corners = [[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([a, b]) => CURL_DIRECTION.x * a * PEEL_WIDTH / 2 + CURL_DIRECTION.y * b * PEEL_HEIGHT / 2);
const FOLD_START = Math.max(...corners) + 0.01, FOLD_END = Math.min(...corners) - 0.6;

function setPeel(turn) {
  const eased = turn < 0.5 ? 2 * turn * turn : 1 - (-2 * turn + 2) ** 2 / 2;
  const fold = FOLD_START + (FOLD_END - FOLD_START) * eased;
  const positions = peelGeometry.attributes.position.array;
  const nx = CURL_DIRECTION.x, ny = CURL_DIRECTION.y, r = CURL_RADIUS;
  for (let i = 0; i < positions.length / 3; i++) {
    const x = peelRest[i * 3], y = peelRest[i * 3 + 1];
    const u = x * nx + y * ny - fold;
    let along = 0, height = 0;
    if (u > 0 && u < Math.PI * r) { const a = u / r; along = r * Math.sin(a) - u; height = r * (1 - Math.cos(a)); }
    else if (u >= Math.PI * r) { along = -(u - Math.PI * r) - u; height = 2 * r; }
    positions[i * 3] = x + along * nx;
    positions[i * 3 + 1] = y + along * ny;
    positions[i * 3 + 2] = height;
  }
  peelGeometry.attributes.position.needsUpdate = true;
  peelGeometry.computeVertexNormals();
  return fold;
}

const blendMaterial = pass(/* glsl */`
  varying vec2 vUv; uniform sampler2D fromPicture; uniform sampler2D toPicture; uniform float mixAmount; uniform float dip;
  void main() {
    vec3 a = texture2D(fromPicture, vUv).rgb, b = texture2D(toPicture, vUv).rgb;
    vec3 c = mix(a, b, smoothstep(0.0, 1.0, mixAmount));
    c *= 1.0 - dip * sin(3.14159 * mixAmount);
    gl_FragColor = vec4(c, 1.0);
  }`, { fromPicture: { value: null }, toPicture: { value: null }, mixAmount: { value: 0 }, dip: { value: 0.25 } });

// Joins two finished pictures: kind 'peel' or 'dissolve'; progress 0 (old page) to 1 (new page).
// 'run-on' (log 34): a plain blend with no darkening in the middle, for a page that runs on into the next in the same
// frame (chapter 2 for newcomers, page 4 into page 5): the two pictures are the same, so nothing shows.
export function drawJoin(kind, progress, fromTarget, toTarget) {
  renderer.setRenderTarget(null);
  if (kind === 'run-on') {
    blendMaterial.uniforms.fromPicture.value = fromTarget.texture;
    blendMaterial.uniforms.toPicture.value = toTarget.texture;
    blendMaterial.uniforms.mixAmount.value = progress;
    blendMaterial.uniforms.dip.value = 0;
    runPass(blendMaterial, null);
    return;
  }
  if (kind === 'dissolve' || kind === 'dip') {
    blendMaterial.uniforms.fromPicture.value = fromTarget.texture;
    blendMaterial.uniforms.toPicture.value = toTarget.texture;
    blendMaterial.uniforms.mixAmount.value = progress;
    blendMaterial.uniforms.dip.value = kind === 'dip' ? 0.85 : 0.2;
    runPass(blendMaterial, null);
    return;
  }
  const fold = setPeel(Math.min(1, Math.max(0, progress)));
  underMaterial.uniforms.picture.value = toTarget.texture;
  underMaterial.uniforms.fold.value = fold;
  runPass(underMaterial, null);
  peelMaterial.uniforms.picture.value = fromTarget.texture;
  peelMaterial.uniforms.shading.value = THREE.MathUtils.smoothstep(progress, 0, PEEL_SHADING_IN);
  renderer.autoClear = false;
  renderer.setRenderTarget(null);
  renderer.clearDepth();
  renderer.render(peelScene, peelCamera);
  renderer.autoClear = true;
}

// Copies a finished picture to the screen.
const copyMaterial = pass(/* glsl */`varying vec2 vUv; uniform sampler2D picture; void main() { gl_FragColor = vec4(texture2D(picture, vUv).rgb, 1.0); }`, { picture: { value: null } });
export function showPicture(target) {
  copyMaterial.uniforms.picture.value = target.texture;
  runPass(copyMaterial, null);
}

export function grabFrame() {
  return renderer.domElement.toDataURL('image/jpeg', 0.95);
}

// ------------------------------------------------------------------------------------ textures
const loader = new THREE.TextureLoader();
const loadedTextures = new Map();
export function loadTexture(url, { colour = true } = {}) {
  const key = `${url}|${colour}`;
  if (!loadedTextures.has(key)) {
    loadedTextures.set(key, loader.loadAsync(url).then((texture) => {
      texture.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
      texture.generateMipmaps = true;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      return texture;
    }));
  }
  return loadedTextures.get(key);
}
export function canvasTexture(canvas, { colour = true } = {}) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}
// Reads an image's pixels (for depth maps), as a canvas 2D context.
export async function loadPixels(url) {
  const image = new Image();
  image.src = url;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.width; canvas.height = image.height;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(image, 0, 0);
  return { width: image.width, height: image.height, data: context.getImageData(0, 0, image.width, image.height).data };
}
