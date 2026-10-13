// What this does: a test scene, not part of any film (log 22). The 1973 petrol station painting
// (chapter 2, page 7) as a painted room with depth, with the red car and the three pumps rebuilt as
// real 3D models by SAM 3D (fal-ai/sam-3/3d-objects) and stood exactly where they are in the painting.
// The teal car further back stays painted (a painted room is enough that far away). The painting
// behind is a "clean plate" (assets/reliefs/sam-3d-test/): the same painting with those four things
// painted out by Flux 3 edit (used only inside their outlines) and a flat floor in the depth picture
// where they stood (paper-film/tools/ground_under_objects.py).
//
// How the models are placed: SAM 3D gives each model a size, a turn and a position in its own guess of
// the camera (assets/models/sam-3d-test/layout.json, mapped by paper-film/tools/sam3d_fit_layout.py).
// Its lens is wider than the film's, so each model keeps its turn and its spot in the picture, is slid
// along its line of sight until its lowest points touch the ground fitted around its base, and is
// sized so it covers the same part of the picture.
//
// How they look painted: each model wears the painting itself, projected from where it was painted,
// on every surface the painting showed (the real brushwork, the glowing headlights, the windscreen's
// interior). Only surfaces the painting never showed use SAM 3D's own surface, tinted to match by
// comparing the two where both exist. They take only a touch of the lamp (the painting already has its
// light painted in) and cast shadows on the painted ground.
//
// Views (?view= in the address, set with PAPER_FILM_QUERY):
//   painting     from where the painting was painted (should look like the painting)
//   small-push   a short straight push towards the car (the snapshot's third picture)
//   original     the original painting as a painted room, without models (for comparison)
//   also: gentle-push, push-in, small-push-2, moved, side, step-right, low-left (bigger moves tear the
//   painted room: its canopy post and kiosk bend)
// Use: PAPER_FILM_QUERY=view=small-push node paper-film/tools/render-paper-film.mjs sam-3d-petrol-station-test OUT --stills 190
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';

const view = new URLSearchParams(location.search).get('view') ?? 'painting';
const MODELS = '/assets/models/sam-3d-test';

const testPage = {
  async build(kit) {
    // the same light as page 7: a warm lamp under the canopy, a cool sky
    kit.lightRig({ keyColour: 0xffd09a, keyShare: 0.75, keyFrom: [2.8, 5.5, -3.5], keyTarget: [0, -2.1, -7.6], fillSky: 0x6f86a0, fillGround: 0x1c1a18,
      fillShare: 0.22, haze: 0x101823, hazeDensity: 0.004, shadowBox: 6, shadowSoftness: 5, background: 0x0b1118, reflections: 0.3 });
    const original = view === 'original';
    // the clean plate lives in its own folder; borrow it for this one painted room
    const chapterReliefs = kit.reliefFolder;
    if (!original) kit.reliefFolder = '/assets/reliefs/sam-3d-test';
    const room = await kit.relief(original ? '409-bg-petrol-station-1973' : '409-petrol-station-clean', { near: 6, far: 70, fov: 40, margin: 0.22 });
    kit.reliefFolder = chapterReliefs;
    const placed = [];
    if (!original) {
      const layout = await (await fetch(`${MODELS}/layout.json`)).json();
      const samTanX = layout.sam_tan_x, samTanY = samTanX * layout.painting_size[1] / layout.painting_size[0];
      const flip = new THREE.Matrix4().makeScale(-1, 1, -1);                 // SAM: x left, z forward; here: x right, z back
      const quarterTurn = new THREE.Matrix4().makeRotationX(Math.PI / 2);   // the model files lie a quarter-turn from SAM's own frame
      // the original painting, projected onto the models from where it was painted (see below)
      const paintTexture = await loadTexture('/assets/reliefs/inflation-chapter-2/409-bg-petrol-station-1973.jpg');   // as the painted room loads it
      const paintPixels = await pixelsOf('/assets/reliefs/inflation-chapter-2/409-bg-petrol-station-1973.jpg');
      for (const object of layout.objects) {
        if (object.keep_painted) continue;                                  // far things stay part of the painted room
        const model = await loadModel(`${MODELS}/${object.file}`, { reflections: 0.15 });
        const [w, x, y, z] = object.rotation_wxyz;
        const samTurn = new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion(x, y, z, w).invert());
        const turn = new THREE.Matrix4().multiplyMatrices(flip, samTurn).multiply(quarterTurn);
        model.quaternion.setFromRotationMatrix(turn);
        // where SAM put it in the picture, as a direction from the film's camera
        const [tx, ty, tz] = object.translation;
        const across = -(tx / tz) / samTanX, up = (ty / tz) / samTanY;     // -1..1 across and up the picture
        const direction = new THREE.Vector3(across * room.tanX, up * room.tanY, -1);
        const sizeAt = (distance) => object.scale * (room.tanX / samTanX) * distance / tz;
        const setDistance = (distance) => { model.position.copy(direction).multiplyScalar(distance); model.scale.setScalar(sizeAt(distance)); };
        kit.scene.add(model);
        model.traverse((o) => { if (o.isMesh && !o.geometry.attributes.normal) o.geometry.computeVertexNormals(); });
        // stand it on the ground under it: sliding along its line of sight keeps it on the same spot of
        // the picture, so find the distance where its lowest points (the lowest 1%) are 0.01 above the
        // ground found around its base (ground_under_objects.py: y = a x + b z + c)
        setDistance(1); model.updateMatrixWorld(true);
        const [ga, gb, gc] = object.ground;
        const heights = [];
        model.traverse((o) => {
          if (!o.isMesh) return;
          const position = o.geometry.attributes.position, q = new THREE.Vector3();
          for (let i = 0; i < position.count; i += 2) { q.fromBufferAttribute(position, i).applyMatrix4(o.matrixWorld); heights.push(q.y - ga * q.x - gb * q.z); }
        });
        heights.sort((m, n) => m - n);
        const close = (0.01 + gc) / heights[Math.floor(heights.length * 0.01)];
        setDistance(close);
        model.updateMatrixWorld(true);
        const mask = await pixelsOf(`/assets/reliefs/sam-3d-test/${object.mask}`);
        model.traverse((o) => {
          if (!o.isMesh) return;
          // SAM 3D's files carry no surface directions (normals); without them the lamp's shading
          // turns to garbage and the glow spreads it as black blocks (worked out above)
          const map = o.material.map;
          // (the surface picture keeps the loader's standard colour handling, the same as the painted room's)
          // PROJECTION: wherever this surface was visible in the painting (facing the painter's eye and
          // inside the object's outline), it wears the painting's own pixels, projected from where the
          // painting was painted: the real brushwork, glowing headlights, the windscreen's interior.
          // Only surfaces the painting never showed (backs, far sides) use SAM 3D's invented surface,
          // tinted to match by comparing the two where both exist.
          const { paintUv, paintWeight, tint } = projectPainting(o, room, paintPixels, mask, map);
          o.geometry.setAttribute('paintUv', new THREE.BufferAttribute(paintUv, 2));
          o.geometry.setAttribute('paintWeight', new THREE.BufferAttribute(paintWeight, 1));
          o.material = paintedMaterial(map, paintTexture, tint);
          o.castShadow = true; o.receiveShadow = true;
          const share = paintWeight.reduce((sum, v) => sum + v, 0) / paintWeight.length;
          console.warn(`${object.name}: ${(share * 100).toFixed(0)}% of its surface wears the painting; hidden sides tinted ${tint.toArray().map((v) => v.toFixed(2)).join(', ')}`);
        });
        placed.push({ name: object.name, model, distance: close });
        console.warn(`${object.name}: ${close.toFixed(2)} units away, ${(sizeAt(close)).toFixed(2)} across, clearance ${room.clearance(model).toFixed(3)}, lowest points ${groundGap(model, room).toFixed(3)} above the painted ground`);
      }
    }
    const car = placed.find((p) => p.name.includes('red-car'))?.model.position.clone() ?? room.pointAt(0.22, 0.38);
    const pump = placed.find((p) => p.name.includes('pump-middle'))?.model.position.clone() ?? room.pointAt(0.62, 0.45);
    const pivot = car.clone().lerp(pump, 0.45);
    const around = (yaw, closer, lift) => {
      const offset = new THREE.Vector3(0, 0, 0).sub(pivot).applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(yaw)).multiplyScalar(1 - closer);
      return pivot.clone().add(offset).add(new THREE.Vector3(0, lift, 0));
    };
    const cameras = {
      painting: { position: [0, 0, 0], target: [0, 0, -30], fov: 40 },
      original: { position: [0, 0, 0], target: [0, 0, -30], fov: 40 },
      // a painted room only holds together for small moves, so these stay modest
      moved: { position: around(-7, 0.2, 0.25).toArray(), target: pivot.clone().add(new THREE.Vector3(0, 0.9, 0)).toArray(), fov: 40 },
      side: { position: around(-15, 0.32, 0.45).toArray(), target: pivot.clone().add(new THREE.Vector3(0.2, 0.6, 0)).toArray(), fov: 40 },
    };
    // candidate gentle moves, to find which shows the models best with the least tearing
    const toward = (point, share) => new THREE.Vector3(0, 0, 0).lerp(point, share);
    cameras['push-in'] = { position: toward(car, 0.3).add(new THREE.Vector3(0, 0.1, 0)).toArray(), target: car.clone().add(new THREE.Vector3(0.6, 0.3, 0)).toArray(), fov: 40 };
    cameras['gentle-push'] = { position: toward(car, 0.16).add(new THREE.Vector3(0, 0.05, 0)).toArray(), target: car.clone().lerp(new THREE.Vector3(0, -2, -30), 0.5).toArray(), fov: 40 };
    cameras['step-right'] = { position: [0.9, 0.15, -2.2], target: car.clone().add(new THREE.Vector3(0.9, 0.5, 0)).toArray(), fov: 40 };
    cameras['low-left'] = { position: [-0.7, -0.35, -2.6], target: car.clone().add(new THREE.Vector3(1.0, 0.4, 0)).toArray(), fov: 40 };
    // a short straight push towards the car, looking the same way as the painting: the smallest move
    // that still shows the models are solid, and the least tearing of the painted room
    cameras['small-push'] = { position: [-0.45, -0.05, -1.6], target: [-0.45, -0.6, -31.6], fov: 40 };
    cameras['small-push-2'] = { position: [-0.7, 0.05, -2.4], target: [-0.9, -0.7, -32.4], fov: 40 };
    const camera = cameras[view] ?? cameras.painting;
    const focus = new THREE.Vector3(...camera.position).distanceTo(car);
    return {
      pose: () => ({ camera: { position: new THREE.Vector3(...camera.position), target: new THREE.Vector3(...camera.target), fov: camera.fov, roll: 0, focus },
        look: { aperture: 6, maxBlur: 10, exposure: 0.95, glowThreshold: 0.92, glowStrength: 0.6, contrast: 1.06, fade: 0 } }),
    };
  },
};

// The pixels of a picture (for reading colours in code).
async function pixelsOf(source) {
  const bitmap = typeof source === 'string' ? await createImageBitmap(await (await fetch(source)).blob()) : source;
  const canvas = new OffscreenCanvas(bitmap.width, bitmap.height), context = canvas.getContext('2d');
  context.drawImage(bitmap, 0, 0);
  return { width: bitmap.width, height: bitmap.height, data: context.getImageData(0, 0, bitmap.width, bitmap.height).data };
}
const toLinear = (value) => { const c = value / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };   // the stage works in linear light
const pixelAt = (pixels, x, y) => {
  const i = (Math.min(pixels.height - 1, Math.max(0, Math.round(y))) * pixels.width + Math.min(pixels.width - 1, Math.max(0, Math.round(x)))) * 4;
  return [pixels.data[i], pixels.data[i + 1], pixels.data[i + 2]];
};

// For each corner of a model: where it lands in the painting (seen from the painter's eye at the
// origin), and how much it should wear the painting (facing the eye, and well inside the object's
// outline in the painting). Also the tint for the hidden sides: the painting's colour against the
// model's own surface colour, compared where the model wears the painting.
function projectPainting(mesh, room, paint, mask, map) {
  const position = mesh.geometry.attributes.position, normal = mesh.geometry.attributes.normal, uv = mesh.geometry.attributes.uv;
  const paintUv = new Float32Array(position.count * 2), paintWeight = new Float32Array(position.count);
  const normalMatrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
  const p = new THREE.Vector3(), n = new THREE.Vector3();
  const own = map?.image ? pixelsOfSync(map.image) : null;
  const sums = { paint: [0, 0, 0], own: [0, 0, 0] };
  const inside = (u, v) => {                                  // the outline, shrunk by about 8 pixels
    let least = 255;
    for (const [dx, dy] of [[0, 0], [8, 0], [-8, 0], [0, 8], [0, -8]]) least = Math.min(least, pixelAt(mask, u * mask.width + dx, (1 - v) * mask.height + dy)[0]);
    return least / 255;
  };
  for (let i = 0; i < position.count; i++) {
    p.fromBufferAttribute(position, i).applyMatrix4(mesh.matrixWorld);
    n.fromBufferAttribute(normal, i).applyMatrix3(normalMatrix).normalize();
    const d = -p.z, u = (p.x / d / room.tanX + 1) / 2, v = (p.y / d / room.tanY + 1) / 2;
    paintUv[i * 2] = u; paintUv[i * 2 + 1] = v;
    const facing = n.dot(p.clone().negate().normalize());
    const weight = THREE.MathUtils.smoothstep(facing, 0.12, 0.4) * inside(u, v);
    paintWeight[i] = weight;
    if (weight > 0.6 && own && uv) {
      const a = pixelAt(paint, u * paint.width, (1 - v) * paint.height);
      const b = pixelAt(own, uv.getX(i) * own.width, uv.getY(i) * own.height);
      for (let c = 0; c < 3; c++) { sums.paint[c] += toLinear(a[c]); sums.own[c] += toLinear(b[c]); }
    }
  }
  // (the model's surface picture is stored top row first: three.js loads glTF pictures unflipped)
  // per colour, but pulled halfway to an even change, so neutral parts (chrome, glass) don't shift hue
  const ratio = sums.paint.map((v, c) => v / Math.max(1, sums.own[c]));
  const even = (ratio[0] + ratio[1] + ratio[2]) / 3;
  const tint = new THREE.Color(...ratio.map((r) => Math.min(3, Math.max(0.3, 0.5 * r + 0.5 * even))));
  return { paintUv, paintWeight, tint };
}
function pixelsOfSync(image) {
  const canvas = new OffscreenCanvas(image.width, image.height), context = canvas.getContext('2d');
  context.drawImage(image, 0, 0);
  return { width: image.width, height: image.height, data: context.getImageData(0, 0, image.width, image.height).data };
}

// A material that shows the painting where the model wore it and the model's own (tinted) surface
// elsewhere, lit like the painted room: mostly its own colour, plus a little of the lamp.
// The painting already has its light painted in, so the models take only a touch of the lamp (enough
// to shade their sides and cast shadows) and show mostly their own colour: `glow` is how much of its
// colour a surface shows by itself, `lamp` how much the lamp adds.
const LIGHT = { glow: 0.8, lamp: 0.22 };
function paintedMaterial(map, paintTexture, tint) {
  const material = new THREE.MeshLambertMaterial({ map, color: 0xffffff, emissive: 0xffffff, emissiveIntensity: LIGHT.glow });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.paintMap = { value: paintTexture };
    shader.uniforms.ownTint = { value: tint };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec2 paintUv;\nattribute float paintWeight;\nvarying vec2 vPaintUv;\nvarying float vPaintWeight;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvPaintUv = paintUv;\nvPaintWeight = paintWeight;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D paintMap;\nuniform vec3 ownTint;\nvarying vec2 vPaintUv;\nvarying float vPaintWeight;')
      .replace('#include <map_fragment>', '#include <map_fragment>\nvec3 paintedBase = mix(diffuseColor.rgb * ownTint, texture2D(paintMap, vPaintUv).rgb, vPaintWeight);\ndiffuseColor.rgb = paintedBase * ' + LIGHT.lamp.toFixed(3) + ';')
      .replace('#include <emissivemap_fragment>', 'totalEmissiveRadiance *= paintedBase;');
  };
  return material;
}

// How high the lowest points of a model sit above the painted ground straight below them (median of
// the lowest 2%), to catch a model that is clear of the ground but floating. For a point P, the ground
// below it is found by looking down the same column of the painting until the painted surface comes
// as near as P (the floor point at P's own distance), then comparing heights.
function groundGap(model, room) {
  const points = [];
  model.traverse((o) => {
    if (!o.isMesh) return;
    const position = o.geometry.attributes.position, p = new THREE.Vector3();
    for (let i = 0; i < position.count; i += 3) points.push(p.fromBufferAttribute(position, i).applyMatrix4(o.matrixWorld).clone());
  });
  points.sort((a, b) => a.y - b.y);
  const lowest = points.slice(0, Math.max(5, Math.floor(points.length * 0.02)));
  const gaps = lowest.map((q) => {
    const d = -q.z, u = (q.x / d / room.tanX + 1) / 2;
    let v = (q.y / d / room.tanY + 1) / 2;
    while (v > 0 && room.distanceAt(u, v) > d) v -= 0.0005;            // down the column to the floor at P's distance
    return q.y - (v * 2 - 1) * room.tanY * d;
  }).sort((a, b) => a - b);
  return gaps[Math.floor(gaps.length / 2)];
}

export async function build() {
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2/timeline.json', piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles: [testPage], pageNumbers: [7] });
}
