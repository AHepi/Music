// NOTE (plain words): checking copy of the film's lockout scene as it is NOW (new look: toe 1, frame edge 0.25), with ONE change: the two painting file names can be given in the address (?painting=NAME&behind=NAME). Made by wet_lockout_film/tools/make_hook_scenes.py.
// What this does: the plan 3 test clip (log 29), 12 seconds, no narration: Britain, 1926, a pit
// village street at dusk during the miners' lockout. The street, the cottages, the pithead and the
// props are real 3D (built in Blender: paper-film/blender/pit-village/), drawn once from the main
// camera (the plate), repainted in the series' painted style by Flux, and the painting is shone back
// onto the same 3D shapes (projected-set.js), so the camera can move without anything tearing.
//   0-2 s     fade in on the painted street: BRITAIN 1926
//   2-7.2 s   the camera moves up the street (one move: 1.4 m forward, a little right and up, turning
//             5 degrees right and 1.5 down, narrowing its lens from 40 to 26 degrees), ending with the
//             notice board near the middle, the colliery's sign and the pithead gone off the left.
//             The turn is kept small so the frame never leaves the painted area (the narrower lens
//             is what lets it turn at all), and most of the push in is the lens: a lens change
//             uncovers nothing the plate didn't see.
//   7.3 s     cut to the notice board, close, square to it (one slow push in)
//   8-11 s    LOCKED OUT / FROM 1 MAY 1926 above the notice
//   11-12 s   fade out
// Three paintings are shone onto the set: the painting itself; a "behind" painting of the same view
// with the near props painted out (Flux), for the road and walls those props hid, uncovered as the
// camera moves; and the painted sky alone (paintedSkyOnly) on a far card, so the sky uncovered behind
// the pithead is painted sky. The notice board keeps its own sharp surfaces (the painter garbled the
// small print), matched in colour to the painting where it stands.
// Live on top: flames on the brazier's coals, sparks, smoke from the brazier and some chimneys, and
// the fire's flickering light on the surfaces the painting doesn't cover (the notice board).
// Views (PAPER_FILM_QUERY=view=NAME): move (default), projector (holds the first frame), moved
// (holds the end of the street move), notice (holds the end of the close shot), weights (the end of
// the street move: orange wears the painting, green the behind painting, blue its own surface),
// weights-move (the same colours through the whole clip).
// Use: cd paper-pop-up-film-kit && node paper-film/tools/render-paper-film.mjs lockout-test OUT --stills 1.5 5 7 9
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE, smooth, clamp01 } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';
import { loadProjector, projectPaintingOnto, paintedSkyOnly } from './projected-set.js';
import { Smoke } from './effects.js';
import { placeTitle, hook } from './graphics.js';
import { glow, Flames, Sparks, paintedSkyColour, contactShadow, groundUnder, facingOf } from './pit-village-effects.js';

const SET = '/assets/models/pit-village';
const VIEW = new URLSearchParams(location.search).get('view') ?? 'move';
// the near props painted out of the behind painting (names as exported, before Blender's .001)
const NEAR_PROPS = ['handcart', 'coal-sacks', 'coal-pile', 'wooden-pail', 'hurricane-lantern', 'spade', 'brazier', 'dustbins', 'notice-on-board', 'Cube'];
const NEAR = 16;   // metres from the projector: further copies of the same props stay in the behind painting

const page = {
  async build(kit) {
    // dusk: cool sky light, warm lamps; the painting carries the light, the lamps only touch the
    // surfaces the plate never saw and the notice board's own surfaces
    kit.lightRig({ keyColour: 0xffc48a, keyShare: 0.45, keyFrom: [1, 2.4, -10.4], keyTarget: [0, 0, -14], fillSky: 0x50637e, fillGround: 0x1c1712,
      fillShare: 0.35, haze: 0x1a2330, hazeDensity: 0.008, shadowBox: 14, shadowSoftness: 6, background: 0x0e141c, reflections: 0.2 });
    kit.lights.key.castShadow = false;

    const set = await loadModel(`${SET}/lockout-set.glb`);
    const signs = await loadModel(`${SET}/lockout-signs.glb`);
    const everything = new THREE.Group();
    everything.add(set, signs);
    kit.scene.add(everything);
    everything.updateMatrixWorld(true);
    const dome = set.getObjectByName('sky_dome');   // past the film camera's reach; the sky card stands in
    if (dome) dome.visible = false;
    const projector = await loadProjector(`${SET}/lockout-camera.json`);
    const [painting, behindPainting] = await Promise.all([loadTexture(`${SET}/${new URLSearchParams(location.search).get('painting') ?? 'lockout-painted.jpg'}`), loadTexture(`${SET}/${new URLSearchParams(location.search).get('behind') ?? 'lockout-behind.jpg'}`)]);

    // the near props (painted out of the behind painting) and the notice board's materials
    const nearProps = [];
    const centre = new THREE.Vector3();
    for (const root of [...set.children, ...signs.children]) {
      if (!NEAR_PROPS.some((name) => root.name.startsWith(name))) continue;
      new THREE.Box3().setFromObject(root).getCenter(centre);
      if (centre.distanceTo(projector.position) < NEAR) nearProps.push(root);
    }
    const boardMaterials = new Set();
    for (const root of signs.children) {
      if (!root.name.startsWith('notice-on-board') && !root.name.startsWith('Cube')) continue;
      root.traverse((o) => { if (o.isMesh) for (const m of [o.material].flat()) boardMaterials.add(m.name); });
    }
    boardMaterials.delete('notice-paper');
    let paper = null;
    signs.traverse((o) => { if (o.isMesh && [o.material].flat().some((m) => m.name === 'notice-paper')) paper = o; });
    if (paper?.material.map) paper.material.map.anisotropy = 8;   // the small print stays crisp at a slant

    // the fire's light, made before the paintings are shone on so the colour match includes it: it
    // only shows on surfaces the painting doesn't cover (the notice board, and anything uncovered as
    // the camera moves), so they are warm like the painted firelight round them, and it flickers
    const fireLight = new THREE.PointLight(0xff9a50, 4, 9, 2);
    fireLight.position.set(0.95, 2.08, -10.4);
    kit.scene.add(fireLight);

    const projection = projectPaintingOnto(kit, everything, painting, projector, {
      ownSurface: ['notice-paper', 'colliery-board-paint', ...[...boardMaterials].map((name) => [name, 'notice-paper'])],
      behind: { painting: behindPainting, hide: nearProps },
      stretch: [2.0, 4.0],
    });

    // the sky: a card 300 m out, square to the projector and wider than its frame, wearing the painted
    // sky alone (nothing nearer than 1 km), so the sky uncovered behind the pithead is painted sky
    const skyDistance = 300;
    const skyHeight = 2 * skyDistance * Math.tan(THREE.MathUtils.degToRad(projector.fov / 2)) * 1.6;
    const skyCard = new THREE.Mesh(new THREE.PlaneGeometry(skyHeight * 1.5, skyHeight), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }));
    skyCard.material.name = 'sky card';
    skyCard.position.copy(projector.position).addScaledVector(new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion), skyDistance);
    skyCard.quaternion.copy(projector.quaternion);
    const skyGroup = new THREE.Group();
    skyGroup.add(skyCard);
    kit.scene.add(skyGroup);
    const skyColour = paintedSkyColour(painting);
    const skyProjection = projectPaintingOnto(kit, skyGroup, paintedSkyOnly(projection, painting), projector, { calibrate: false, averageColour: skyColour, darken: 1, tint: 1, matte: false });
    // where the painting doesn't reach, the card shows the painted sky's average colour exactly
    skyProjection.materials[0].color.setRGB(skyColour.r / skyProjection.fallbackTint.x, skyColour.g / skyProjection.fallbackTint.y, skyColour.b / skyProjection.fallbackTint.z);
    kit.scene.background = skyColour.clone();
    if (VIEW === 'weights' || VIEW === 'weights-move') { projection.showWeights(true); skyProjection.showWeights(true); }

    // soft contact shadows under the coal sacks, the handcart and the brazier (placed in assemble_lockout.py:
    // Blender (x, y, turn) -> three.js (x, -y), turned about y), faded in as the move begins
    const shadows = [[-0.2, 8.4, 18, 1.5, 1.9], [-1.75, 9.6, -70, 1.9, 1.2], [0.95, 10.4, 0, 1.15, 1.15]].map(([x, y, turn, width, depth]) => {
      const shadow = contactShadow(width, depth);
      shadow.holder.position.set(x, groundUnder(set, x, -y, nearProps) + 0.012, -y);
      shadow.holder.rotation.y = THREE.MathUtils.degToRad(turn);
      kit.scene.add(shadow.holder);
      return shadow;
    });

    // where things are, in three.js space (Blender x, y, z -> x, z, -y)
    const coals = new THREE.Vector3(0.95, 1.62, -10.4);        // the top of the coal bed, where the flames stand
    const brazierTop = new THREE.Vector3(0.95, 1.78, -10.4);   // the middle of the flames
    const notice = new THREE.Box3().setFromObject(paper).getCenter(new THREE.Vector3());
    const noticeFacing = facingOf(paper, projector.position.clone().sub(notice).normalize());
    const chimneyTops = [[-7.65, 11.74, 8.5], [-7.65, 12.37, 17.5], [7.65, 12.05, 17.5], [7.65, 12.68, 26.5], [-7.65, 13.31, 31.0]]
      .map(([x, z, y]) => new THREE.Vector3(x, z + 0.4, -y));

    // the fire: flames on the coals, a flickering glow, sparks, smoke, and its light
    const fireGlow = glow(0xff9a40, 1.5, 0.4); fireGlow.position.copy(brazierTop); kit.scene.add(fireGlow);
    const flames = new Flames(kit.scene, coals);
    const sparks = new Sparks(kit.scene, coals.clone().add(new THREE.Vector3(0, 0.08, 0)));
    // smoke sprites are not lit, so their colour is set dark enough to sit in the dusk
    const brazierSmoke = new Smoke(kit.scene, { count: 14, life: 3.6, seed: 21, colour: [150, 146, 140] });
    for (const puff of brazierSmoke.puffs) puff.sprite.material.color.setRGB(0.5, 0.48, 0.46);
    const chimneySmoke = chimneyTops.map((top, i) => ({ top, effect: new Smoke(kit.scene, { count: 10, life: 4.2, seed: 31 + i, colour: [120, 126, 136] }) }));
    for (const c of chimneySmoke) for (const puff of c.effect.puffs) puff.sprite.material.color.setRGB(0.6, 0.62, 0.66);

    // shot 1: starts exactly where the plate was drawn from (with the film's 40-degree lens the frame
    // is the middle of the painting), then moves up the street
    const ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion).setY(0).normalize();
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(projector.quaternion).setY(0).normalize();
    const start = { position: projector.position.toArray(), target: projector.userData.target.toArray(), fov: 40, focus: 9 };
    const endPosition = projector.position.clone().addScaledVector(ahead, 1.4).addScaledVector(right, 0.3).add(new THREE.Vector3(0, 0.05, 0));
    // turned 5 degrees right (with the 26-degree lens the frame's right edge stays just inside the
    // painting) and 1.5 down: the board near the middle, the fire at the bottom, the coal sacks below
    // the frame, the colliery's sign and the pithead gone off the left
    const endLook = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion).applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(-5));
    endLook.applyAxisAngle(endLook.clone().cross(new THREE.Vector3(0, 1, 0)).normalize(), THREE.MathUtils.degToRad(-1.5));
    const end = { position: endPosition.toArray(), target: endPosition.clone().addScaledVector(endLook, 10).toArray(), fov: 26, focus: endPosition.distanceTo(notice) };
    // shot 2: square to the notice (it faces almost straight at the projector, so little is uncovered),
    // the paper a little below the middle to leave room for the words above it
    const closeAt = (distance) => notice.clone().addScaledVector(noticeFacing, distance).add(new THREE.Vector3(0, -0.1, 0));
    const closeTarget = notice.clone().add(new THREE.Vector3(0, 0.2, 0));
    const close = { position: closeAt(2.7).toArray(), target: closeTarget.toArray(), fov: 34, focus: 2.7 };
    const closer = { position: closeAt(2.25).toArray(), target: closeTarget.toArray(), fov: 34, focus: 2.25 };

    const T = { title: kit.at('title'), move: kit.at('move'), arrive: kit.at('arrive'), cut: kit.at('cut'), locked: kit.at('locked'), end: kit.at('end') };
    const street = VIEW === 'projector' ? kit.stillShot(start, [], { name: 'projector' })
      : VIEW === 'moved' || VIEW === 'weights' ? kit.stillShot(end, [], { name: 'moved' })
        : VIEW === 'weights-move' ? kit.stillShot(start, [{ kind: 'zoom in', from: T.move, to: T.arrive, ...end }], { name: 'up the street, weights' })
        : kit.stillShot(start, [{ kind: 'zoom in', from: T.move, to: T.arrive, ...end }], { name: 'up the street' });
    const board = VIEW === 'notice' ? kit.stillShot(closer, [], { name: 'notice held' })
      : kit.stillShot(close, [{ kind: 'zoom in', from: T.cut, to: T.end + 1, ...closer }], { name: 'the notice' });
    const onBoard = (t) => VIEW === 'notice' || ((VIEW === 'move' || VIEW === 'weights-move') && t >= T.cut);

    function pose(t) {
      const flicker = 0.75 + 0.15 * Math.sin(t * 17.3) + 0.1 * Math.sin(t * 29.1 + 1.3);
      fireGlow.material.opacity = 0.4 * flicker;
      fireGlow.scale.setScalar(1.4 + 0.12 * Math.sin(t * 11.7));
      fireLight.intensity = 4 * (0.75 + 0.25 * flicker);
      flames.set(t);
      sparks.set(t);
      for (const shadow of shadows) shadow.material.opacity = 0.6 * smooth((t - T.move) / 0.7);
      brazierSmoke.set({ t, origin: brazierTop.clone().add(new THREE.Vector3(0, 0.35, 0)).toArray(), scale: 0.75, wind: 0.9 });
      for (const c of chimneySmoke) c.effect.set({ t, origin: c.top.toArray(), scale: 0.9, wind: 0.8 });
      const fade = Math.max(1 - clamp01(t / 1.0), smooth((t - T.end) / 1.0));
      const close = onBoard(t);
      return { camera: close ? board(t) : street(t),
        look: { exposure: 1.0, aperture: close ? 1.6 : 2.5, maxBlur: close ? 10 : 7, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.25, toe: 1, fade } };
    }
    function draw2D(ctx, t) {
      placeTitle(ctx, t, { at: T.title, until: T.move + 3.5, place: 'Britain', year: 1926, y: 300, size: 64 });
      // a soft dark fade down from the top behind LOCKED OUT, so it reads over the board and the lit window
      const shade = clamp01((t - T.locked + 0.2) / 0.5) * (1 - clamp01((t - T.end - 0.4) / 0.5));
      if (shade > 0) {
        const g = ctx.createLinearGradient(0, 0, 0, 640);
        g.addColorStop(0, `rgba(5,8,12,${0.62 * shade})`); g.addColorStop(1, 'rgba(5,8,12,0)');
        ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 640);
      }
      hook(ctx, t, { at: T.locked, until: T.end + 0.9, text: 'LOCKED OUT', y: 330, size: 104 });
      hook(ctx, t, { at: T.locked + 0.5, until: T.end + 0.9, text: 'FROM 1 MAY 1926', y: 430, size: 48, colour: '#e8a33d' });
      return true;
    }
    return { pose, draw2D };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/lockout-test/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page],
    pageNumbers: [1],
  });
}
