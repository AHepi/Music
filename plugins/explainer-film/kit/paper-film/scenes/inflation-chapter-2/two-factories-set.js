// What this does: builds the "two factories" set used on pages 3 and 8 of chapter 2: two ivory card
// model factories standing on a dark card table, in front of a painted dusk skyline of an industrial
// town (a flat backdrop far behind), lit by one warm lamp from the front left. The left factory (A)
// starts idle; the right one (B) runs flat out. Each has a flip counter on a post showing its price,
// a yard where coins land, and a place where its shells stand.
//
// Positions (world units): the table top is y = 0; factory A stands at x = -3.2, factory B at
// x = +3.2, both at z = -2, fronts facing the camera (+z).

import { THREE } from '../cinema-kit.js';
import { paper, PAPER, paperGround, paperFactory, splitFlap, shell } from '../models.js';
import { Smoke, Motes } from '../effects.js';

export const FACTORY_A = new THREE.Vector3(-1.4, 0, 2.2);
export const FACTORY_B = new THREE.Vector3(1.6, 0, -4.2);

export async function buildTwoFactories(kit, { shellsA = 6, shellsB = 8 } = {}) {
  kit.lightRig({ keyColour: 0xffc98a, keyShare: 0.8, keyFrom: [-12, 6.5, 7], keyTarget: [0, 0, -1], fillSky: 0x6f8796, fillGround: 0x241e18,
    fillShare: 0.24, haze: 0x1a2228, hazeDensity: 0.018, shadowBox: 10, shadowSoftness: 6, background: 0x10161b });
  const backdrop = await kit.backdrop('402-bg-dusk-skyline', { distance: 52, fov: 40 });
  backdrop.position.set(0, 13, -52);
  backdrop.scale.setScalar(1.65); // wide enough to fill the frame from the far opening camera
  const table = paperGround({ at: [0, 0, -8], width: 70, depth: 60, colour: 0x2e2c28 });
  kit.scene.add(table.group);

  const make = (at, seed) => {
    const factory = paperFactory({ width: 3.2, depth: 2.0, height: 1.3, bays: 4 });
    factory.group.position.copy(at);
    kit.scene.add(factory.group);
    const smoke = new Smoke(kit.scene, { count: 12, life: 3.4, seed });
    const chimney = factory.chimneyTop.clone().add(at);
    // a flip counter on a post to the right of the door, showing the price of a shell
    const board = splitFlap({ cells: 5, cellWidth: 0.13, gap: 0.018 });
    const boardAt = new THREE.Vector3(at.x + 1.25, 1.05, at.z + 1.55);
    board.group.position.copy(boardAt);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.9, 10), paper(PAPER.charcoal));
    post.position.set(boardAt.x, 0.45, boardAt.z - 0.05);
    post.castShadow = true;
    kit.scene.add(board.group, post);
    const shells = [];
    for (let i = 0; i < 10; i++) {
      const s = shell({ height: 0.28 });
      s.group.position.set(at.x - 1.45 + i * 0.17, 0, at.z + 1.35);
      kit.scene.add(s.group);
      shells.push(s);
    }
    return { factory, smoke, chimney, board, boardAt, post, shells,
      shellAt: (i) => new THREE.Vector3(at.x - 1.45 + i * 0.17, 0, at.z + 1.35),
      yard: new THREE.Vector3(at.x - 0.1, 0, at.z + 2.1), door: factory.doorAt.clone().add(at) };
  };
  const a = make(FACTORY_A, 31), b = make(FACTORY_B, 47);
  const motes = new Motes(kit.scene, { count: 200, min: [-5, 0.2, -8], max: [5, 4, 5], size: 0.025, seed: 11, opacity: 0.55 });
  return { a, b, motes, shellsA, shellsB };
}
