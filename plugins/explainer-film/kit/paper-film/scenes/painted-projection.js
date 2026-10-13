// What this does: shared tools for putting 3D things into a painting so they still look painted
// (logs 22 and 23). "Projection": a surface wears the painting shone onto it from where the painting
// was painted (the painting camera: the origin, looking along -z, the painted room's lens), so its
// brushwork and painted light are kept. Used by sam-3d-petrol-station-test.js and
// station-proxies-test.js.
//   projectPainting / paintedMaterial: for 3D models (SAM 3D) that wear the painting where it showed
//     them and their own surface elsewhere, with a touch of the lamp.
//   projectedMaterial: for plain stand-in shapes (posts, walls, decks) that wear a picture exactly,
//     unlit, worked out per pixel so big flat faces don't distort; faces turned away from the painting
//     get a plain colour (its shaded side).
//   boxMesh: an upright box from its eight corners.
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';

// The pixels of a picture (for reading colours in code).
export async function pixelsOf(source) {
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
export function projectPainting(mesh, room, paint, mask, map) {
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
    const weight = THREE.MathUtils.smoothstep(facing, 0.04, 0.22) * inside(u, v);
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
  const tint = new THREE.Color(...ratio.map((r) => Math.min(4, Math.max(0.3, 0.5 * r + 0.5 * even))));
  return { paintUv, paintWeight, tint };
}
export function pixelsOfSync(image) {
  const canvas = new OffscreenCanvas(image.width, image.height), context = canvas.getContext('2d');
  context.drawImage(image, 0, 0);
  return { width: image.width, height: image.height, data: context.getImageData(0, 0, image.width, image.height).data };
}

// A material that shows the painting where the model wore it and the model's own (tinted) surface
// elsewhere, lit like the painted room: mostly its own colour, plus a little of the lamp.
// The painting already has its light painted in, so the models take only a touch of the lamp (enough
// to shade their sides and cast shadows) and show mostly their own colour: `glow` is how much of its
// colour a surface shows by itself, `lamp` how much the lamp adds.
export const LIGHT = { glow: 0.75, lamp: 0.2 };
export function paintedMaterial(map, paintTexture, tint, light = LIGHT) {
  const material = new THREE.MeshLambertMaterial({ map, color: 0xffffff, emissive: 0xffffff, emissiveIntensity: light.glow });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.paintMap = { value: paintTexture };
    shader.uniforms.ownTint = { value: tint };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec2 paintUv;\nattribute float paintWeight;\nvarying vec2 vPaintUv;\nvarying float vPaintWeight;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvPaintUv = paintUv;\nvPaintWeight = paintWeight;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D paintMap;\nuniform vec3 ownTint;\nvarying vec2 vPaintUv;\nvarying float vPaintWeight;')
      .replace('#include <map_fragment>', '#include <map_fragment>\nvec3 paintedBase = mix(diffuseColor.rgb * ownTint, texture2D(paintMap, vPaintUv).rgb, vPaintWeight);\ndiffuseColor.rgb = paintedBase * ' + light.lamp.toFixed(3) + ';')
      .replace('#include <emissivemap_fragment>', 'totalEmissiveRadiance *= paintedBase;');
  };
  return material;
}

// How high the lowest points of a model sit above the painted ground straight below them (median of
// the lowest 2%), to catch a model that is clear of the ground but floating. For a point P, the ground
// below it is found by looking down the same column of the painting until the painted surface comes
// as near as P (the floor point at P's own distance), then comparing heights.
export function groundGap(model, room) {
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

// A material for plain stand-in shapes: shows `picture` as projected from the painting camera, per
// pixel (so big flat faces don't distort), and is lit exactly as the painted room is lit (the same
// share of its own colour and of the lamp, and the same facing: towards the painting camera), so a
// stand-in matches the painted room around it from the painting's view and catches the same shadows.
// Faces the painting camera can't see (a post's side, seen from the painting's view) show `fallback`.
export function projectedMaterial(picture, room, { fallback = new THREE.Color(0.1, 0.1, 0.1), lit = 0.35 } = {}) {
  const material = new THREE.MeshLambertMaterial({ color: new THREE.Color(lit / 0.45, lit / 0.45, lit / 0.45), emissive: 0xffffff, emissiveIntensity: 1 - lit });
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, { picture: { value: picture }, fallback: { value: fallback }, tanX: { value: room.tanX }, tanY: { value: room.tanY } });
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWorld;\nvarying vec3 vWorldNormal;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;\nvWorldNormal = normalize(mat3(modelMatrix) * normal);');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D picture;\nuniform vec3 fallback;\nuniform float tanX;\nuniform float tanY;\nvarying vec3 vWorld;\nvarying vec3 vWorldNormal;')
      .replace('#include <map_fragment>', `#include <map_fragment>
        float depthHere = max(0.001, -vWorld.z);
        vec2 at = vec2((vWorld.x / depthHere / tanX + 1.0) * 0.5, (vWorld.y / depthHere / tanY + 1.0) * 0.5);
        float facing = dot(normalize(vWorldNormal), normalize(-vWorld));
        vec3 standInColour = mix(fallback, texture2D(picture, at).rgb, smoothstep(0.0, 0.015, facing));   // any face the painting saw at all wears it
        diffuseColor.rgb *= standInColour;`)
      .replace('#include <normal_fragment_begin>', '#include <normal_fragment_begin>\nnormal = normalize((viewMatrix * vec4(0.0, 0.0, 1.0, 0.0)).xyz);')
      .replace('#include <emissivemap_fragment>', 'totalEmissiveRadiance *= standInColour;');
  };
  return material;
}

// An upright box from its eight corners (base four, then top four, going round), with outward faces.
export function boxMesh(corners, material) {
  const c = corners.map((p) => new THREE.Vector3(...p));
  const centre = c.reduce((s, p) => s.add(p), new THREE.Vector3()).multiplyScalar(1 / 8);
  const faces = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]];
  const positions = [], normals = [];
  for (const f of faces) {
    let [a, b, d, e] = f.map((i) => c[i]);
    let n = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(d, a)).normalize();
    const mid = a.clone().add(b).add(d).add(e).multiplyScalar(0.25);
    if (n.dot(mid.clone().sub(centre)) < 0) { [b, e] = [e, b]; n.negate(); }
    for (const p of [a, b, d, a, d, e]) { positions.push(p.x, p.y, p.z); normals.push(n.x, n.y, n.z); }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  return new THREE.Mesh(geometry, material);
}

// SAM 3D models (log 22) stood in the painted room: each placed from SAM's layout on its line of sight,
// standing on the ground fitted around its base, wearing the painting where it showed them.
// Returns [{ name, model, distance }]. `models`: the folder with layout.json and the .glb files;
// `painting`: the original painting; `masks`: the folder with each object's outline mask.
export async function placeSamModels(kit, room, { models, painting, masks, light = LIGHT }) {
  const MODELS = models;
  const placed = [];
    const layout = await (await fetch(`${MODELS}/layout.json`)).json();
    const samTanX = layout.sam_tan_x, samTanY = samTanX * layout.painting_size[1] / layout.painting_size[0];
    const flip = new THREE.Matrix4().makeScale(-1, 1, -1);                 // SAM: x left, z forward; here: x right, z back
    const quarterTurn = new THREE.Matrix4().makeRotationX(Math.PI / 2);   // the model files lie a quarter-turn from SAM's own frame
    // the original painting, projected onto the models from where it was painted (see below)
    const paintTexture = await loadTexture(painting);   // as the painted room loads it
    const paintPixels = await pixelsOf(painting);
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
      const mask = await pixelsOf(`${masks}/${object.mask}`);
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
        o.material = paintedMaterial(map, paintTexture, tint, light);
        o.castShadow = true; o.receiveShadow = true;
        const share = paintWeight.reduce((sum, v) => sum + v, 0) / paintWeight.length;
        console.warn(`${object.name}: ${(share * 100).toFixed(0)}% of its surface wears the painting; hidden sides tinted ${tint.toArray().map((v) => v.toFixed(2)).join(', ')}`);
      });
      placed.push({ name: object.name, model, distance: close });
      console.warn(`${object.name}: ${close.toFixed(2)} units away, ${(sizeAt(close)).toFixed(2)} across, clearance ${room.clearance(model).toFixed(3)}, lowest points ${groundGap(model, room).toFixed(3)} above the painted ground`);
    }
  return placed;
}

// A see-through ground that shows only shadows: the painted ground keeps its painted light, and the 3D
// things standing on it still cast shadows onto it. `ground`: [a, b, c] for y = a x + b z + c.
export function shadowCatcher(ground, { at = new THREE.Vector3(0, 0, -15), size = 60, darkness = 0.45, lift = 0.03 } = {}) {
  const [a, b, c] = ground;
  const up = new THREE.Vector3(-a, 1, -b).normalize();
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.ShadowMaterial({ opacity: darkness }));
  plane.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), up);
  plane.position.set(at.x, a * at.x + b * at.z + c, at.z).addScaledVector(up, lift);
  plane.receiveShadow = true;
  return plane;
}
