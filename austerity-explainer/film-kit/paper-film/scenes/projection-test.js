// What this does: the test of projected-set.js (plan 3: a built set, drawn once from its main camera,
// painted over, and the painting shone back onto the same shapes). It loads chapter 2's model town
// and two works (the set), stands a projector camera where chapter 2 page 3's "both works" shot
// stands (examples/projection-test/camera.json), makes a stand-in painting by drawing the set from the
// projector once and running a painterly filter over it (Kuwahara: flat brush patches with kept
// edges, plus a few colour steps), then shines that painting back onto the set and moves the camera
// 1.5 m right, 2 m forward and 0.8 m up.
//
// Timeline (examples/projection-test/timeline.json, 6.5 s): the camera holds at the projector until
// 1.0 s, moves until 5.0 s and holds there.
// Views (PAPER_FILM_QUERY=view=NAME) hold one camera for the whole timeline:
//   projector  the projector's own view, wearing the painting (must look exactly like the painting)
//   painting   the painting itself, flat across the frame (to compare with "projector")
//   moved      the moved camera, wearing the painting
//   weights    the moved camera; orange = wears the painting, blue = its own surface
//   original   the moved camera, the set's own materials, no painting (what the shapes really are)
// PAPER_FILM_QUERY=matte=1 loads the set with matte materials before painting it (a fairer timing).
// PAPER_FILM_QUERY=time=1 also times the drawing of the 3D scene (without the finishing passes) with
// and without the projection, from the moved camera, and prints it as a warning.
//
// Use: cd paper-pop-up-film-kit && node paper-film/tools/render-paper-film.mjs projection-test OUT --stills 1 3 5
//      PAPER_FILM_QUERY=view=weights node paper-film/tools/render-paper-film.mjs projection-test OUT --stills 5
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { renderer, FRAME_WIDTH, FRAME_HEIGHT } from '../stage/cinema-stage.js';
import { loadModel, modelFactory } from './model-loader.js';
import { loadProjector, projectPaintingOnto } from './projected-set.js';

const MODELS = '/assets/models/inflation-chapter-2';
const QUERY = new URLSearchParams(location.search);
const VIEW = QUERY.get('view') ?? 'move';
const TIMING = QUERY.get('time') === '1';
const MATTE = QUERY.get('matte') === '1';   // load the set with matte materials (for a fair timing)

// ------------------------------------------------------------- the stand-in painting (test only)
const passCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const passScene = new THREE.Scene();
const passQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), null);
passQuad.frustumCulled = false;
passScene.add(passQuad);
const passVertex = 'varying vec2 vUv;\nvoid main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }';
const SRGB = 'vec3 toSrgb(vec3 c) { c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }';
// Kuwahara filter: each pixel takes the mean colour of the calmest of the four squares around it, so
// flat patches form like brush strokes and edges stay; then a few colour steps (sRGB bytes out).
const painterlyMaterial = new THREE.ShaderMaterial({
  vertexShader: passVertex,
  uniforms: { picture: { value: null }, texel: { value: new THREE.Vector2(1 / FRAME_WIDTH, 1 / FRAME_HEIGHT) }, steps: { value: 18 } },
  fragmentShader: `
    varying vec2 vUv; uniform sampler2D picture; uniform vec2 texel; uniform float steps;
    ${SRGB}
    const int R = 5;
    void main() {
      vec3 bestMean = vec3(0.0); float bestSpread = 1e9;
      for (int q = 0; q < 4; q++) {
        vec2 direction = vec2(q == 0 || q == 2 ? -1.0 : 1.0, q < 2 ? -1.0 : 1.0);
        vec3 sum = vec3(0.0), sumSquares = vec3(0.0);
        for (int y = 0; y <= R; y++) for (int x = 0; x <= R; x++) {
          vec3 c = toSrgb(texture2D(picture, vUv + vec2(float(x), float(y)) * direction * texel).rgb);
          sum += c; sumSquares += c * c;
        }
        float n = float((R + 1) * (R + 1));
        vec3 mean = sum / n, spread = sumSquares / n - mean * mean;
        float total = spread.r + spread.g + spread.b;
        if (total < bestSpread) { bestSpread = total; bestMean = mean; }
      }
      gl_FragColor = vec4(floor(bestMean * steps + 0.5) / steps * 0.85 + bestMean * 0.15, 1.0);
    }`,
});
const toBytesMaterial = new THREE.ShaderMaterial({
  vertexShader: passVertex, uniforms: { picture: { value: null } },
  fragmentShader: `varying vec2 vUv; uniform sampler2D picture; ${SRGB}\nvoid main() { gl_FragColor = vec4(toSrgb(texture2D(picture, vUv).rgb), 1.0); }`,
});
const linearTarget = new THREE.WebGLRenderTarget(FRAME_WIDTH, FRAME_HEIGHT, { type: THREE.HalfFloatType, samples: 4, colorSpace: THREE.LinearSRGBColorSpace });
const bytesTarget = new THREE.WebGLRenderTarget(FRAME_WIDTH, FRAME_HEIGHT, { type: THREE.UnsignedByteType, colorSpace: THREE.NoColorSpace });

// draws `scene` from `camera` and returns the frame as sRGB bytes (bottom row first), through `filter`
function drawToBytes(scene, camera, filter) {
  renderer.setRenderTarget(linearTarget);
  renderer.render(scene, camera);
  filter.uniforms.picture.value = linearTarget.texture;
  passQuad.material = filter;
  renderer.setRenderTarget(bytesTarget);
  renderer.render(passScene, passCamera);
  const bytes = new Uint8Array(FRAME_WIDTH * FRAME_HEIGHT * 4);
  renderer.readRenderTargetPixels(bytesTarget, 0, 0, FRAME_WIDTH, FRAME_HEIGHT, bytes);
  renderer.setRenderTarget(null);
  return bytes;
}
function bytesToTexture(bytes) {
  const canvas = document.createElement('canvas');
  canvas.width = FRAME_WIDTH; canvas.height = FRAME_HEIGHT;
  const context = canvas.getContext('2d');
  const image = context.createImageData(FRAME_WIDTH, FRAME_HEIGHT), row = FRAME_WIDTH * 4;
  for (let y = 0; y < FRAME_HEIGHT; y++) image.data.set(bytes.subarray((FRAME_HEIGHT - 1 - y) * row, (FRAME_HEIGHT - y) * row), y * row);
  context.putImageData(image, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Number(QUERY.get('anisotropy') ?? renderer.capabilities.getMaxAnisotropy());
  return texture;
}
// how far two byte frames differ: the mean difference (0..255) and the share of pixels off by more than 8
function compareBytes(a, b) {
  let total = 0, off = 0;
  for (let i = 0; i < a.length; i += 4) {
    const d = Math.max(Math.abs(a[i] - b[i]), Math.abs(a[i + 1] - b[i + 1]), Math.abs(a[i + 2] - b[i + 2]));
    total += d; if (d > 8) off++;
  }
  return { mean: total / (a.length / 4), offShare: off / (a.length / 4) };
}
// draws the 3D scene alone `count` times and returns the mean milliseconds (reading one pixel back
// each time, so the software renderer has really finished)
function timeDraw(scene, camera, count = 4) {
  const pixel = new Uint8Array(4);
  renderer.setRenderTarget(linearTarget); renderer.render(scene, camera);   // compile and warm up
  const started = performance.now();
  for (let i = 0; i < count; i++) {
    renderer.setRenderTarget(bytesTarget);
    renderer.render(scene, camera);
    renderer.readRenderTargetPixels(bytesTarget, 0, 0, 1, 1, pixel);
  }
  renderer.setRenderTarget(null);
  return (performance.now() - started) / count;
}

// ----------------------------------------------------------------------------------- the page
const page = {
  async build(kit) {
    kit.lightRig({ keyColour: 0xffc98a, keyShare: 0.8, keyFrom: [-12, 6.5, 7], keyTarget: [0, 0, -1], fillSky: 0x6f8796, fillGround: 0x241e18,
      fillShare: 0.24, haze: 0x1a2228, hazeDensity: 0.022, shadowBox: 10, shadowSoftness: 6, background: 0x10161b, reflections: 0.3 });
    // the set: the town, the two works and a painted dusk sky card far behind (all of it wears the painting)
    const set = new THREE.Group();
    kit.scene.add(set);
    set.add(await loadModel(`${MODELS}/town.glb`, { matte: MATTE }));
    const worksA = await modelFactory(`${MODELS}/factory-a.glb`, { matte: MATTE }), worksB = await modelFactory(`${MODELS}/factory-b.glb`, { matte: MATTE });
    worksA.group.position.set(-1.4, 0, 2.2); worksB.group.position.set(1.6, 0, -4.2);
    worksA.setRunning(0.3); worksB.setRunning(1);
    set.add(worksA.group, worksB.group);
    const sky = await kit.backdrop('402-bg-dusk-skyline', { distance: 52, fov: 40 });
    sky.position.set(0, 13, -52); sky.scale.setScalar(4.6);
    set.add(sky);
    let triangles = 0;
    set.traverse((o) => { if (o.isMesh) triangles += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; });

    const projector = await loadProjector('/examples/projection-test/camera.json');
    // the moved camera: 1.5 m to the projector's right, 2 m forward (level), 0.8 m up, same aim
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(projector.quaternion).setY(0).normalize();
    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion).setY(0).normalize();
    const movedPosition = projector.position.clone().addScaledVector(right, 1.5).addScaledVector(forward, 2).add(new THREE.Vector3(0, 0.8, 0));
    const movedTarget = projector.userData.target.clone().add(movedPosition).sub(projector.position);
    const atProjector = { position: projector.position.toArray(), target: projector.userData.target.toArray(), fov: projector.fov };
    const atMoved = { position: movedPosition.toArray(), target: movedTarget.toArray(), fov: projector.fov };
    const movedCamera = projector.clone(); movedCamera.position.copy(movedPosition); movedCamera.updateMatrixWorld(true);

    // the stand-in painting: the set drawn from the projector, then painterly-filtered
    let started = performance.now();
    kit.scene.updateMatrixWorld(true);
    const paintingBytes = drawToBytes(kit.scene, projector, painterlyMaterial);
    const painting = bytesToTexture(paintingBytes);
    console.warn(`projection-test: set ${Math.round(triangles)} triangles; stand-in painting made in ${(performance.now() - started).toFixed(0)} ms`);
    const timeOriginal = TIMING ? timeDraw(kit.scene, movedCamera) : 0;

    let projection = null;
    if (VIEW !== 'original') {
      started = performance.now();
      projection = projectPaintingOnto(kit, set, painting, projector);
      console.warn(`projection-test: projection set up in ${(performance.now() - started).toFixed(0)} ms`);
      // the check: from the projector the set must show the painting exactly
      const seen = drawToBytes(kit.scene, projector, toBytesMaterial);
      const { mean, offShare } = compareBytes(seen, paintingBytes);
      console.warn(`projection-test: projector view vs painting: mean difference ${mean.toFixed(2)} / 255, ${(offShare * 100).toFixed(2)}% of pixels off by more than 8 / 255`);
      if (TIMING) {
        const timeProjected = timeDraw(kit.scene, movedCamera);
        console.warn(`projection-test: drawing the 3D scene once (1080 x 1920, no finishing passes): own materials ${timeOriginal.toFixed(0)} ms, projected ${timeProjected.toFixed(0)} ms`);
      }
      if (VIEW === 'weights') projection.showWeights(true);
    }
    if (VIEW === 'painting') {
      // the painting flat across the frame, just in front of the projector
      set.visible = false;
      const tanY = Math.tan(THREE.MathUtils.degToRad(projector.fov / 2));
      const card = new THREE.Mesh(new THREE.PlaneGeometry(2 * tanY * projector.aspect, 2 * tanY), new THREE.MeshBasicMaterial({ map: painting, fog: false }));
      card.position.set(0, 0, -1).applyQuaternion(projector.quaternion).add(projector.position);
      card.quaternion.copy(projector.quaternion);
      kit.scene.add(card);
    }

    const hold = (pose) => kit.stillShot(pose, [], { name: VIEW });
    const shot = VIEW === 'projector' || VIEW === 'painting' ? hold(atProjector)
      : VIEW === 'moved' || VIEW === 'weights' || VIEW === 'original' ? hold(atMoved)
        : kit.stillShot(atProjector, [{ from: kit.at('move'), to: kit.at('arrive'), kind: 'zoom in', ...atMoved }], { name: 'projection move' });
    return {
      pose: (t) => ({ camera: shot(t), look: { aperture: 0, exposure: 1.0, glowThreshold: 0.95, glowStrength: 0.5 } }),
    };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/projection-test/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page],
    pageNumbers: [1],
  });
}
