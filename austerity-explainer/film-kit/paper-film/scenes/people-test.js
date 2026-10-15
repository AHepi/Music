// What this does: the people test (plan 34, part "People"; order of work step 3), 4 seconds, no narration:
// the pit village street at dusk a few metres back from the notice corner, with men waiting round a brazier
// (four from behind at 6 to 9 m, one facing us at about 7 m) and six small walkers 40 to 60 m up the street
// (assemble_people_test.py; the figures from build_figures.py). The camera holds still at the plate camera's
// place. No painting has been paid for: the PLATE stands in for the painting, shone back onto the set
// (projected-set.js), so the test costs nothing and shows whether the plan's two ways of showing people work
// in the film stage before any money is spent.
// Two versions (PAPER_FILM_QUERY=view=NAME):
//   painted (default)  the figures are part of the plate ("painted people"). At 2.0 s a time cut swaps to the
//                      STATE PICTURE and the figures leave the set: the men are simply gone (plan: "the film
//                      makes a time cut to the state picture"). The state picture (people-test-state.jpg, made by
//                      paper-film/tools/make_state_picture.py) is the plate everywhere except where the men were
//                      and where the light and shadows they changed fall (found by comparing the plate with the
//                      helper plate, joined with the men's outlines): there it is the helper plate (the same view
//                      drawn without them). So at the cut only that area changes, as it will with two real
//                      paintings; round 1 swapped the whole picture, which with two paintings would change every
//                      brushstroke in the frame. The held shot is drawn once before the cut and once after (pose
//                      returns still: 'men there' or 'men gone', a value that changes at the cut).
//   silhouettes        the helper plate throughout, with the figures standing on it as their own dark surfaces
//                      (never painted): near-black wool with a rim of light from the lit street behind them,
//                      and a soft contact shadow under each.
//   weights            the painted version's colours (orange wears the painting, blue its own surface).
// Live on top in every version: the brazier's flames, sparks, smoke and glow (kit.moving: redrawn every frame). The
// smoke drifts right; the man at the lamp post now stands clear of it, back from the kerb (in round 1 he stood
// straight behind the brazier and came out a washed-out grey ghost).
// Use: cd film-kit && node paper-film/tools/render-paper-film.mjs people-test OUT --stills 1 3
//      PAPER_FILM_QUERY=view=silhouettes node paper-film/tools/render-paper-film.mjs people-test OUT.mp4
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';
import { loadProjector, projectPaintingOnto, paintedSkyOnly } from './projected-set.js';
import { Smoke } from './effects.js';
import { glow, Flames, Sparks, paintedSkyColour, contactShadow, groundUnder } from './pit-village-effects.js';

const FOLDER = '/assets/models/inflation-chapter-2-newcomers/people-test';
const VIEW = new URLSearchParams(location.search).get('view') ?? 'painted';
const SILHOUETTES = VIEW === 'silhouettes';
// Blender (x, y, z) -> three.js (x, z, -y)
const fromBlender = ([x, y, z]) => new THREE.Vector3(x, z, -y);

// The dark own surface of a figure that is never painted: near-black wool, lit only at its edges by the lamp-lit
// street behind it (a rim strongest along the tops of the shoulders and the cap, where the surface turns away from
// the camera toward the light), fading out toward the feet (the tops of the boots caught it and seemed to glow).
// Unlit by the page's lamps, so it stays a silhouette whatever the stage's light.
function silhouetteMaterial({ base = 0x050504, rim = 0xd9b98c, strength = 0.55, behind = [0.0, 0.45, -1.0] } = {}) {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      baseColour: { value: new THREE.Color(base) }, rimColour: { value: new THREE.Color(rim) },
      rimStrength: { value: strength }, lightBehind: { value: new THREE.Vector3(...behind).normalize() },
    },
    vertexShader: `
      varying vec3 vNormal; varying vec3 vToCamera; varying float vHeight;
      void main() {
        vHeight = position.y;   // each figure's own height above its feet (its origin is on the ground)
        vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
        vToCamera = -viewPosition.xyz;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * viewPosition;
      }`,
    fragmentShader: `
      uniform vec3 baseColour; uniform vec3 rimColour; uniform float rimStrength; uniform vec3 lightBehind;
      varying vec3 vNormal; varying vec3 vToCamera; varying float vHeight;
      void main() {
        vec3 normal = normalize(vNormal);
        float edge = pow(1.0 - abs(dot(normal, normalize(vToCamera))), 3.0);   // 1 at the outline, 0 face-on
        float towardLight = clamp(dot(normal, lightBehind) + 0.35, 0.0, 1.0);   // the side the street's light reaches
        float aboveFeet = smoothstep(0.1, 0.5, vHeight);
        gl_FragColor = vec4(baseColour + rimColour * rimStrength * edge * towardLight * aboveFeet, 1.0);
      }`,
  });
  material.name = 'figure silhouette';
  return material;
}

const page = {
  async build(kit) {
    // dusk: the plate carries the light; the page's lamps only touch surfaces the plate never saw
    kit.lightRig({ keyColour: 0xffc48a, keyShare: 0.45, keyFrom: [2.6, 2.6, -22.0], keyTarget: [2.6, 1.8, -22.8], fillSky: 0x50637e, fillGround: 0x1c1712,
      fillShare: 0.35, haze: 0x1a2330, hazeDensity: 0.008, shadowBox: 14, shadowSoftness: 6, background: 0x0e141c, reflections: 0.2 });
    kit.lights.key.castShadow = false;

    const [set, signs, figures, projector, shot] = await Promise.all([loadModel(`${FOLDER}/people-test-set.glb`), loadModel(`${FOLDER}/people-test-signs.glb`),
      loadModel(`${FOLDER}/people-test-figures.glb`), loadProjector(`${FOLDER}/people-test-camera.json`), fetch(`${FOLDER}/people-test-shot.json`).then((r) => r.json())]);
    const [plate, helperPlate, statePicture] = await Promise.all([loadTexture(`${FOLDER}/people-test-plate.jpg`),
      loadTexture(`${FOLDER}/people-test-helper-plate.jpg`), loadTexture(`${FOLDER}/people-test-state.jpg`)]);

    // the painted version shines the plate onto the people too; the silhouettes stand outside the projection, so
    // the ground behind them still wears the plate where they hide it
    const everything = new THREE.Group();
    everything.add(set, signs);
    if (!SILHOUETTES) everything.add(figures);
    kit.scene.add(everything);
    if (SILHOUETTES) kit.scene.add(figures);
    everything.updateMatrixWorld(true);
    figures.updateMatrixWorld(true);
    const dome = set.getObjectByName('sky_dome');   // past the film camera's reach; the sky card stands in
    if (dome) dome.visible = false;

    const projection = projectPaintingOnto(kit, everything, SILHOUETTES ? helperPlate : plate, projector, { ownSurface: ['colliery-board-paint'] });
    if (VIEW === 'weights') projection.showWeights(true);

    // the sky: a card far out, square to the projector, wearing the painted sky alone
    const skyDistance = 300;
    const skyHeight = 2 * skyDistance * Math.tan(THREE.MathUtils.degToRad(projector.fov / 2)) * 1.6;
    const skyCard = new THREE.Mesh(new THREE.PlaneGeometry(skyHeight * 1.5, skyHeight), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }));
    skyCard.material.name = 'sky card';
    skyCard.position.copy(projector.position).addScaledVector(new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion), skyDistance);
    skyCard.quaternion.copy(projector.quaternion);
    const skyGroup = new THREE.Group();
    skyGroup.add(skyCard);
    kit.scene.add(skyGroup);
    const skyColour = paintedSkyColour(plate);
    const skyProjection = projectPaintingOnto(kit, skyGroup, paintedSkyOnly(projection, plate), projector, { calibrate: false, averageColour: skyColour, darken: 1, tint: 1, matte: false });
    skyProjection.materials[0].color.setRGB(skyColour.r / skyProjection.fallbackTint.x, skyColour.g / skyProjection.fallbackTint.y, skyColour.b / skyProjection.fallbackTint.z);
    kit.scene.background = skyColour.clone();

    if (SILHOUETTES) {
      // each figure near-black with a rim of light, and a soft shadow on the ground under it (the helper plate has none)
      const dark = silhouetteMaterial();
      figures.traverse((o) => { if (o.isMesh) o.material = dark; });
      for (const figure of shot.figures) {
        const feet = fromBlender(figure.feet);
        const near = figure.distance_metres < 20;
        const shadow = contactShadow(near ? 0.8 : 0.6, near ? 0.6 : 0.45);
        shadow.holder.position.set(feet.x, groundUnder(set, feet.x, feet.z, []) + 0.012, feet.z);
        shadow.material.opacity = 0.6;
        kit.scene.add(shadow.holder);
      }
    }

    // the time cut (painted version): at the cut the men leave the set and the projection swaps to the state picture,
    // which shows neither them nor their shadows and is the plate everywhere else; the distance map is drawn again
    // without them, so the ground they stood on wears the state picture. Depends only on t, so frames can be drawn in
    // any order.
    let menGone = false;
    const setMenGone = (gone) => {
      if (gone === menGone) return;
      menGone = gone;
      figures.visible = !gone;
      projection.setPainting(gone ? statePicture : plate);
      projection.refresh();
    };

    // the fire: flames on the coals, a flickering glow, sparks, smoke (all redrawn every frame; the set is drawn once
    // for each held view)
    const coals = fromBlender([shot.brazier[0], shot.brazier[1], shot.coals_z]);
    const brazierTop = coals.clone().add(new THREE.Vector3(0, 0.1, 0));
    const effectsDone = kit.movingFromHere();
    const fireGlow = glow(0xff9a40, 1.3, 0.38); fireGlow.position.copy(brazierTop); kit.scene.add(fireGlow);
    const flames = new Flames(kit.scene, coals);
    const sparks = new Sparks(kit.scene, coals.clone().add(new THREE.Vector3(0, 0.08, 0)));
    const brazierSmoke = new Smoke(kit.scene, { count: 14, life: 3.6, seed: 21, colour: [150, 146, 140] });
    for (const puff of brazierSmoke.puffs) puff.sprite.material.color.setRGB(0.5, 0.48, 0.46);
    effectsDone();

    // the camera holds at the plate camera's place, with the film's lens, focused on the group at the brazier
    const ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion);
    const groupDistance = shot.figures.filter((f) => f.distance_metres < 20).reduce((sum, f) => sum + f.distance_metres, 0) / 5;
    const camera = kit.stillShot({ position: projector.position.toArray(), target: projector.position.clone().addScaledVector(ahead, 10).toArray(),
      fov: shot.film_fov_degrees, focus: groupDistance }, [], { name: 'people test, held' });
    const T = { cut: kit.at('cut') };

    function poseAt(t) {
      if (!SILHOUETTES) setMenGone(t >= T.cut);
      const flicker = 0.75 + 0.15 * Math.sin(t * 17.3) + 0.1 * Math.sin(t * 29.1 + 1.3);
      fireGlow.material.opacity = 0.38 * flicker;
      fireGlow.scale.setScalar(1.25 + 0.02 * Math.sin(t * 11.7));
      flames.set(t);
      sparks.set(t);
      brazierSmoke.set({ t, origin: brazierTop.clone().add(new THREE.Vector3(0, 0.35, 0)).toArray(), scale: 0.75, wind: 0.9 });
      // held throughout: the set is drawn once with the men and once without them (the value changes at the cut)
      const still = SILHOUETTES ? 'silhouettes' : menGone ? 'men gone' : 'men there';
      return { camera: camera(t), still, look: { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fade: 0 } };
    }
    return { pose: poseAt };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/people-test/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page],
    pageNumbers: [1],
  });
}
