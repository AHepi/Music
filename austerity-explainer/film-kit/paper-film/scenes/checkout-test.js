// What this does: the checkout test (plan 34, part 1 "B. The checkout", the film's opening picture; page 1's slide), 7
// seconds, no narration: the checkout lane at closing time (assemble_checkout.py), the basket on the belt and the
// newspaper bill beyond it. The camera holds at the plate's spot, slides 0.7 m toward the basket (3.1 m to 2.4 m from
// it, 1.29 times nearer, the plan's largest), starting and stopping gently and never turning, as page 1 does from "same"
// to "inflation", then holds on the composed frame. No painting has been paid for: the PLATE stands in for the
// painting, shone back onto the set from the plate camera (projected-set.js), so this shows for free whether the plate
// and the set hold together in the film stage through the slide.
// What it loads (assets/models/inflation-chapter-2-newcomers/checkout, all written by build_checkout.sh):
//   checkout-set.glb      everything the painting is shone onto
//   checkout-signs.glb    every lettered face (own surfaces: they keep their own pictures, as the painter garbles print)
//   checkout-camera-c1.json  the plate camera, the projector
//   checkout-shot.json    the views' spots, the film's lens, the lettering's material names, spots for labels
//   checkout-c1-plate.jpg the plate (standing in for the painting)
//   checkout-c1-behind-plate.jpg  the plate drawn with the basket, its groceries and the divider left out (standing in for
//                         the behind painting: what they hide, shown round them once the camera moves)
// Versions (PAPER_FILM_QUERY=view=NAME):
//   plate (default)  as above
//   weights          the same, with the projection's weights shown: orange where the painting (here the plate) is shone,
//                    blue where a surface wears its own picture because the plate never saw it. Blue at a frame edge
//                    means the camera has left the painted area there.
// Use: cd film-kit && node paper-film/tools/render-paper-film.mjs checkout-test OUT --stills 0.5 3.45 6.5
//      PAPER_FILM_QUERY=view=weights node paper-film/tools/render-paper-film.mjs checkout-test OUT --stills 0.5 6.5
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';
import { loadProjector, projectPaintingOnto, paintedSkyOnly } from './projected-set.js';

const FOLDER = '/assets/models/inflation-chapter-2-newcomers/checkout';
const VIEW = new URLSearchParams(location.search).get('view') ?? 'plate';
// Blender (x, y, z) -> three.js (x, z, -y)
const fromBlender = ([x, y, z]) => new THREE.Vector3(x, z, -y);
// the night outside the window, as the plate shows it (Blender's world colour through the shop's camera and look)
const NIGHT = 0x06080d;

const page = {
  async build(kit) {
    // evening, inside: the plate carries the light; the page's lamps only touch surfaces the plate never saw and the own
    // surfaces (the lettering is matched to the plate's brightness where it stands)
    kit.lightRig({ keyColour: 0xffb874, keyShare: 0.45, keyFrom: [0.4, 3.3, -1.5], keyTarget: [0.3, 0.9, -2.2], fillSky: 0x58606e, fillGround: 0x1e1a16,
      fillShare: 0.35, haze: 0x0b0d12, hazeDensity: 0.002, shadowBox: 8, shadowSoftness: 6, background: NIGHT, reflections: 0.2 });
    kit.lights.key.castShadow = false;
    kit.camera.near = 0.05;
    kit.camera.far = 400;

    const [set, signs, projector, shot, plate, behindPlate] = await Promise.all([
      loadModel(`${FOLDER}/checkout-set.glb`), loadModel(`${FOLDER}/checkout-signs.glb`), loadProjector(`${FOLDER}/checkout-camera-c1.json`),
      fetch(`${FOLDER}/checkout-shot.json`).then((r) => r.json()), loadTexture(`${FOLDER}/checkout-c1-plate.jpg`),
      loadTexture(`${FOLDER}/checkout-c1-behind-plate.jpg`)]);

    const everything = new THREE.Group();
    everything.add(set, signs);
    kit.scene.add(everything);
    everything.updateMatrixWorld(true);
    // what the behind picture leaves out: the basket with everything in it, and the divider bar
    const near = [];
    for (const name of ['basket', 'divider-bar']) set.getObjectByName(name)?.traverse((o) => { if (o.isMesh) near.push(o); });
    const projection = projectPaintingOnto(kit, everything, plate, projector, {
      ownSurface: shot.lettering?.materials ?? [],
      behind: { painting: behindPlate, hide: near },
    });
    if (VIEW === 'weights') projection.showWeights(true);

    // the sky beyond the window: a card far out, square to the projector, wearing the plate's sky alone (where the plate
    // shows no surface at all), so sky uncovered by the slide is the plate's sky
    const skyDistance = 300;
    const skyHeight = 2 * skyDistance * Math.tan(THREE.MathUtils.degToRad(projector.fov / 2)) * 1.6;
    const skyCard = new THREE.Mesh(new THREE.PlaneGeometry(skyHeight * 1.5, skyHeight), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }));
    skyCard.material.name = 'sky card';
    skyCard.position.copy(projector.position).addScaledVector(new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion), skyDistance);
    skyCard.quaternion.copy(projector.quaternion);
    const skyGroup = new THREE.Group();
    skyGroup.add(skyCard);
    kit.scene.add(skyGroup);
    const night = new THREE.Color(NIGHT);
    const skyProjection = projectPaintingOnto(kit, skyGroup, paintedSkyOnly(projection, plate), projector, { calibrate: false, averageColour: night, darken: 1, tint: 1, matte: false });
    skyProjection.materials[0].color.setRGB(night.r / skyProjection.fallbackTint.x, night.g / skyProjection.fallbackTint.y, night.b / skyProjection.fallbackTint.z);
    kit.scene.background = night.clone();

    // the camera: the plate's spot, then one slide (never turning) to the composed spot, with the film's lens; focused
    // on the basket
    const view = shot.views.c1;
    const ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion);
    const cameraAt = (spot) => {
      const place = fromBlender(view[spot]);
      const basket = fromBlender(shot.spots.basket);
      return { position: place.toArray(), target: place.clone().addScaledVector(ahead, 10).toArray(), fov: shot.film_fov_degrees,
        focus: basket.clone().sub(place).dot(ahead) };
    };
    const T = { slide: kit.at('slide'), stop: kit.at('stop') };
    const camera = kit.stillShot(cameraAt('plate'), [{ kind: 'zoom in', from: T.slide, to: T.stop, ...cameraAt('composed') }], { name: 'checkout, the slide in' });

    function pose(t) {
      const sliding = t > T.slide && t < T.stop;
      return { camera: camera(t), still: sliding ? false : (t >= T.stop ? 'composed' : 'plate spot'),
        look: { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.5, contrast: 1.04, vignette: 0.3, fade: 0 } };
    }
    return { pose };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/checkout-test/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page],
    pageNumbers: [1],
  });
}
