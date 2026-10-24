// What this does: the notice corner clip (log 31), 13 seconds, no narration: Britain, 1926, a pit
// village street at dusk on the first day of the miners' lockout. It rebuilds, with our own 3D street,
// props and correct notice, the composition the user liked in log 30 ("30 Test - composed by Nano
// Banana - own camera"), following "07 Composing a shot": the camera stands on the right-hand pavement
// at a standing person's eye height, level, turned so the street's lines meet at the notice board's
// edge; the story props touch as one group at the board (the drum burning on the kerb's edge, the
// empty chair with a lit lantern on its seat, a pail, a gas lamp above).
//   0-8.5 s   one slow slide toward the notice, 1.5 m, never turning (rule 11): the street's lines keep
//             meeting at the board's edge and the notice keeps its place on screen while it grows
//   1-5 s     BRITAIN 1926 in the dim sky, top left
//   8.5-12 s  held on the composed frame: LOCKED OUT / FROM 1 MAY 1926 top left
//   12-13 s   fade out
// The set was drawn once from the start of the slide (the plate, assemble_notice_corner.py), repainted
// in the series' style, and the painting is shone back onto the same 3D shapes (projected-set.js), with
// a "behind" painting (the near props painted out) for what they hid, the painted sky on a far card,
// and the notice board's own sharp surfaces (the painter garbles small print).
// Live on top: the drum's flames, sparks and smoke, the lantern's flicker, and soft shadows under the
// near props once the camera moves. (Two chimney smokes were dropped: both chimneys are out of the frame, log 32.)
// Views (PAPER_FILM_QUERY=view=NAME): move (default), projector (holds the first frame), end (holds the
// composed frame), weights (the composed frame: orange wears the painting, green the behind painting,
// blue its own surface), weights-move (the same colours through the whole slide).
// Use: cd paper-pop-up-film-kit && node paper-film/tools/render-paper-film.mjs notice-corner OUT --stills 0.5 4.5 9
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
// the near props, painted out of the behind painting (names as exported, before Blender's .001)
const NEAR_PROPS = ['brazier', 'kitchen-chair', 'hurricane-lantern', 'lantern_flame', 'wooden-pail', 'notice-on-board', 'notice-board-post', 'gas-lamp-post'];
const NEAR = 12;   // metres from the projector: further copies of the same props stay in the behind painting
// Blender (x, y, z) -> three.js (x, z, -y)
const fromBlender = ([x, y, z]) => new THREE.Vector3(x, z, -y);

const page = {
  async build(kit) {
    // dusk: the painting carries the light; the page's lamps only touch surfaces the plate never saw
    // and the notice board's own surfaces
    kit.lightRig({ keyColour: 0xffc48a, keyShare: 0.45, keyFrom: [2.8, 2.6, -21.7], keyTarget: [3.4, 1.8, -22.3], fillSky: 0x50637e, fillGround: 0x1c1712,
      fillShare: 0.35, haze: 0x1a2330, hazeDensity: 0.008, shadowBox: 14, shadowSoftness: 6, background: 0x0e141c, reflections: 0.2 });
    kit.lights.key.castShadow = false;

    const [set, signs, projector, shot] = await Promise.all([loadModel(`${SET}/notice-corner-set.glb`), loadModel(`${SET}/notice-corner-signs.glb`),
      loadProjector(`${SET}/notice-corner-camera.json`), fetch(`${SET}/notice-corner-shot.json`).then((r) => r.json())]);
    const everything = new THREE.Group();
    everything.add(set, signs);
    kit.scene.add(everything);
    everything.updateMatrixWorld(true);
    const dome = set.getObjectByName('sky_dome');   // past the film camera's reach; the sky card stands in
    if (dome) dome.visible = false;
    const [painting, behindPainting] = await Promise.all([loadTexture(`${SET}/notice-corner-painted.jpg`), loadTexture(`${SET}/notice-corner-behind.jpg`)]);

    const nearProps = [];
    const centre = new THREE.Vector3();
    for (const root of [...set.children, ...signs.children]) {
      if (!NEAR_PROPS.some((name) => root.name.startsWith(name))) continue;
      new THREE.Box3().setFromObject(root).getCenter(centre);
      if (centre.distanceTo(projector.position) < NEAR) nearProps.push(root);
    }
    const boardMaterials = new Set();
    for (const root of signs.children) {
      if (!root.name.startsWith('notice-on-board') && !root.name.startsWith('notice-board-post')) continue;
      root.traverse((o) => { if (o.isMesh) for (const m of [o.material].flat()) boardMaterials.add(m.name); });
    }
    boardMaterials.delete('notice-paper');
    let paper = null;
    signs.traverse((o) => { if (o.isMesh && [o.material].flat().some((m) => m.name === 'notice-paper')) paper = o; });
    if (paper?.material.map) paper.material.map.anisotropy = 8;

    // where things are (from assemble_notice_corner.py)
    const drum = shot.drum;
    const coals = fromBlender([drum[0], drum[1], shot.coals_z]);   // the top of the coal bed, where the flames stand
    const brazierTop = coals.clone().add(new THREE.Vector3(0, 0.16, 0));
    const lanternFlame = fromBlender(shot.lantern_light);
    const notice = new THREE.Box3().setFromObject(paper).getCenter(new THREE.Vector3());

    // the fire's and the lantern's light, made before the painting is shone on so the colour match
    // includes them: they only show on surfaces the painting doesn't cover (the notice board, and
    // anything uncovered as the camera moves), lit from below as in the painting (rule 6)
    const fireLight = new THREE.PointLight(0xff9a50, 4, 9, 2);
    // at the height of the Blender fire light the painting was made with, so the board's own surface is lit the same way
    fireLight.position.copy(shot.fire_light ? fromBlender(shot.fire_light) : coals.clone().add(new THREE.Vector3(0, 0.12, 0)));
    const lanternLight = new THREE.PointLight(0xffa860, 0.8, 3, 2);
    lanternLight.position.copy(lanternFlame);
    kit.scene.add(fireLight, lanternLight);
    // the warm light from just over the coals onto the notice's bottom edge, a copy of Blender's (rule 6): the
    // notice wears its own surface here, so without it the notice was lit evenly, not warmer at its bottom
    // (the second critics' skeptic, log 31); as strong against the fire's light as in Blender
    const glowSettings = shot.notice_glow;
    const noticeGlowStrength = glowSettings ? 4 * glowSettings.watts / glowSettings.fire_watts : 0;
    const noticeGlow = new THREE.SpotLight(0xffad61, noticeGlowStrength,   // Blender's (1, 0.42, 0.12) as a colour code
      glowSettings?.reach ?? 1.4,
      THREE.MathUtils.degToRad((glowSettings?.cone_degrees ?? 50) / 2), glowSettings?.blend ?? 0.9, 2);
    if (glowSettings) {
      noticeGlow.position.copy(fromBlender(glowSettings.at));
      noticeGlow.target.position.copy(fromBlender(glowSettings.aim_at));
      kit.scene.add(noticeGlow, noticeGlow.target);
    }

    const projection = projectPaintingOnto(kit, everything, painting, projector, {
      ownSurface: ['notice-paper', 'colliery-board-paint', ...[...boardMaterials].map((name) => [name, 'notice-paper'])],
      behind: { painting: behindPainting, hide: nearProps },
      stretch: [2.0, 4.0],
    });

    // the sky: a card 300 m out, square to the projector and wider than its frame, wearing the painted
    // sky alone, so any sky uncovered behind the pithead is painted sky
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
    skyProjection.materials[0].color.setRGB(skyColour.r / skyProjection.fallbackTint.x, skyColour.g / skyProjection.fallbackTint.y, skyColour.b / skyProjection.fallbackTint.z);
    kit.scene.background = skyColour.clone();
    if (VIEW === 'weights' || VIEW === 'weights-move') { projection.showWeights(true); skyProjection.showWeights(true); }

    // soft contact shadows under the drum, the chair and the pail (the behind painting has none of
    // theirs), faded in as the slide begins
    const shadows = [[shot.drum, 1.0, 1.0], [shot.chair, 0.75, 0.75], [shot.pail, 0.55, 0.55]].map(([[x, y], width, depth]) => {
      const shadow = contactShadow(width, depth);
      shadow.holder.position.set(x, groundUnder(set, x, -y, nearProps) + 0.012, -y);
      kit.scene.add(shadow.holder);
      return shadow;
    });

    // the fire: flames on the coals, a flickering glow, sparks, smoke; the lantern's small glow
    const fireGlow = glow(0xff9a40, 1.3, 0.38); fireGlow.position.copy(brazierTop); kit.scene.add(fireGlow);
    const flames = new Flames(kit.scene, coals);
    const sparks = new Sparks(kit.scene, coals.clone().add(new THREE.Vector3(0, 0.08, 0)));
    const lanternGlow = glow(0xffb060, 0.32, 0.5); lanternGlow.position.copy(lanternFlame); kit.scene.add(lanternGlow);
    const brazierSmoke = new Smoke(kit.scene, { count: 14, life: 3.6, seed: 21, colour: [150, 146, 140] });
    for (const puff of brazierSmoke.puffs) puff.sprite.material.color.setRGB(0.5, 0.48, 0.46);

    // the slide: from the plate's own place (the frame is the middle of the painting, which is drawn a
    // little wider than the film's lens) toward the notice, facing the same way throughout
    const ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion);
    const fov = shot.film_fov_degrees;
    const pose = (position) => ({ position: position.toArray(), target: position.clone().addScaledVector(ahead, 10).toArray(), fov, focus: position.distanceTo(notice) });
    const start = pose(projector.position.clone());
    const end = pose(fromBlender(shot.camera_end));

    const T = { title: kit.at('title'), move: kit.at('move'), arrive: kit.at('arrive'), locked: kit.at('locked'), end: kit.at('end') };
    const camera = VIEW === 'projector' ? kit.stillShot(start, [], { name: 'projector' })
      : VIEW === 'end' || VIEW === 'weights' ? kit.stillShot(end, [], { name: 'composed frame' })
        : kit.stillShot(start, [{ kind: 'zoom in', from: T.move, to: T.arrive, ...end }], { name: 'slide to the notice' });

    function poseAt(t) {
      const flicker = 0.75 + 0.15 * Math.sin(t * 17.3) + 0.1 * Math.sin(t * 29.1 + 1.3);
      fireGlow.material.opacity = 0.38 * flicker;
      fireGlow.scale.setScalar(1.25 + 0.02 * Math.sin(t * 11.7));   // its size barely breathes: its rim slid 20 pixels on the road (log 32)
      fireLight.intensity = 4 * (0.75 + 0.25 * flicker);
      noticeGlow.intensity = noticeGlowStrength * (0.75 + 0.25 * flicker);
      const lanternFlicker = 0.9 + 0.06 * Math.sin(t * 9.1) + 0.04 * Math.sin(t * 23.7 + 0.6);
      lanternGlow.material.opacity = 0.5 * lanternFlicker;
      lanternLight.intensity = 0.8 * lanternFlicker;
      flames.set(t);
      sparks.set(t);
      for (const shadow of shadows) shadow.material.opacity = 0.55 * smooth((t - T.move) / 0.8);
      brazierSmoke.set({ t, origin: brazierTop.clone().add(new THREE.Vector3(0, 0.35, 0)).toArray(), scale: 0.75, wind: 0.9 });
      const fade = Math.max(1 - clamp01(t / 1.0), smooth((t - T.end) / 1.0));
      return { camera: camera(t), look: { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fade } };
    }
    function draw2D(ctx, t) {
      // titles in the dim sky, top left, clear of the gas lamp (rule 12); a soft dark band behind the first as
      // behind the last, so the amber 1926 stands out from the sky (it measured 2.2 to 1 against it, log 32)
      const firstShade = clamp01((t - T.title + 0.2) / 0.5) * (1 - clamp01((t - T.title - 4.0) / 0.5));
      if (firstShade > 0) {
        const g = ctx.createLinearGradient(0, 0, 0, 320);
        g.addColorStop(0, `rgba(5,8,12,${0.5 * firstShade})`); g.addColorStop(1, 'rgba(5,8,12,0)');
        ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 320);
      }
      placeTitle(ctx, t, { at: T.title, until: T.title + 4.0, place: 'Britain', year: 1926, x: 70, y: 150, size: 56 });
      const shade = clamp01((t - T.locked + 0.2) / 0.5) * (1 - clamp01((t - T.end - 0.4) / 0.5));
      if (shade > 0) {
        const g = ctx.createLinearGradient(0, 0, 0, 420);
        g.addColorStop(0, `rgba(5,8,12,${0.6 * shade})`); g.addColorStop(1, 'rgba(5,8,12,0)');
        ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 420);
      }
      hook(ctx, t, { at: T.locked, until: T.end + 0.9, text: 'LOCKED OUT', x: 66, y: 110, size: 92, align: 'left' });
      hook(ctx, t, { at: T.locked + 0.5, until: T.end + 0.9, text: 'FROM 1 MAY 1926', x: 70, y: 196, size: 42, colour: '#e8a33d', align: 'left' });
      return true;
    }
    return { pose: poseAt, draw2D };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/notice-corner/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page],
    pageNumbers: [1],
  });
}
