"""What this does: one-off edit of the chapter 2 page 3 files (diagonal layout, new camera)."""
p='two-factories-set.js'
s=open(p).read()
start=s.index("export const FACTORY_A")
s=s[:start]+'''export const FACTORY_A = new THREE.Vector3(-1.4, 0, 2.2);
export const FACTORY_B = new THREE.Vector3(1.6, 0, -4.2);

export async function buildTwoFactories(kit, { shellsA = 6, shellsB = 8 } = {}) {
  kit.lightRig({ keyColour: 0xffc98a, keyShare: 0.95, keyFrom: [-12, 6.5, 7], keyTarget: [0, 0, -1], fillSky: 0x6f8796, fillGround: 0x241e18,
    fillShare: 0.24, haze: 0x1a2228, hazeDensity: 0.018, shadowBox: 10, shadowSoftness: 6, background: 0x10161b });
  const backdrop = await kit.backdrop('402-bg-dusk-skyline', { distance: 52, fov: 40 });
  backdrop.position.set(0, 9, -52);
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
'''
open(p,'w').write(s)

p='page-3.js'
s=open(p).read()
def rep(a,b):
    global s
    assert a in s, a[:60]
    s=s.replace(a,b)
rep("wordMachines: kit.at('machines'),","wordMachines: kit.at('machines', 2),")
rep("const queue = await kit.cutout('workers-queue', { at: [FACTORY_A.x + 1.75, 0, FACTORY_A.z + 1.95], width: 2.2, yaw: 0 });",
    "const queue = await kit.cutout('workers-queue', { at: [FACTORY_A.x + 1.05, 0, FACTORY_A.z + 1.2], width: 1.7, yaw: 0 });")
rep("radius: 0.75, start: T.money1 + 0.05, spread: 0.9, coinRadius: 0.085, seed: 5 });","radius: 0.7, start: T.money1 + 0.05, spread: 0.9, coinRadius: 0.06, seed: 5 });")
rep("radius: 0.75, start: T.money2 + 0.05, spread: 0.9, coinRadius: 0.085, seed: 8 });","radius: 0.7, start: T.money2 + 0.05, spread: 0.9, coinRadius: 0.06, seed: 8 });")
rep("centre: [FACTORY_B.x + 1.0, 0, FACTORY_B.z + 2.05], height: 2.5, start: T.bid, spread: T.climb - T.bid + 0.6, coinRadius: 0.07,",
    "centre: [b.boardAt.x - 0.32, 0, b.boardAt.z + 0.25], height: 2.5, start: T.bid, spread: T.climb - T.bid + 0.6, coinRadius: 0.055,")
rep("{ name: 'worker-standing', width: 0.55, x: FACTORY_B.x - 1.15,","{ name: 'worker-standing', width: 0.42, x: FACTORY_B.x - 0.95,")
rep("{ name: 'materials', width: 1.05, x: FACTORY_B.x + 0.05,","{ name: 'materials', width: 0.8, x: FACTORY_B.x + 0.05,")
rep("{ name: 'lathe', width: 1.05, x: FACTORY_B.x + 1.3,","{ name: 'lathe', width: 0.8, x: FACTORY_B.x + 1.05,")
rep("at: [item.x, 0, FACTORY_B.z + 3.35], width: item.width });","at: [item.x, 0, FACTORY_B.z + 2.55], width: item.width });")
rep("at: [item.x, 0, FACTORY_B.z + 3.75], size: 0.17 });","at: [item.x, 0, FACTORY_B.z + 2.95], size: 0.12 });")
cam_start=s.index("  const shot = kit.shot([")
cam_end=s.index("], { handheld: 0.015, seed: 3 });")
s=s[:cam_start]+'''  const shot = kit.shot([
    { t: T.start, position: [0.6, 15, 17], target: [0.1, 0.2, -1.2], fov: 40, focus: [0, 0.5, -1] },
    { t: T.two + 0.5, position: [0.6, 8.2, 12.6], target: [0.1, 0.3, -1.4], fov: 40, focus: [0, 0.5, -1] },
    { t: T.first + 1.5, position: [0.3, 3.9, 10.2], target: [-1.2, 0.75, 2.6], fov: 38, focus: [-1.3, 0.6, 3.2] },
    { t: T.money1, position: [0.4, 3.6, 9.6], target: [-1.2, 0.55, 2.9], fov: 38, focus: [a.yard.x, 0.1, a.yard.z] },
    { t: T.shells + 0.6, position: [-0.2, 2.6, 8.2], target: [-1.6, 0.45, 3.2], fov: 38, focus: [-2.4, 0.2, 3.55] },
    { t: T.barely + 0.6, position: [0.6, 2.3, 7.4], target: [-0.3, 0.9, 3.4], fov: 36, focus: [a.boardAt.x, a.boardAt.y, a.boardAt.z] },
    { t: T.second + 1.4, position: [3.0, 3.9, 3.8], target: [1.5, 0.75, -3.8], fov: 38, focus: [1.5, 0.6, -3.2] },
    { t: T.money2, position: [3.1, 3.6, 3.2], target: [1.5, 0.55, -3.5], fov: 38, focus: [b.yard.x, 0.1, b.yard.z] },
    { t: T.bid, position: [3.6, 2.3, 1.2], target: [2.6, 0.9, -2.8], fov: 36, focus: [b.boardAt.x, b.boardAt.y, b.boardAt.z] },
    { t: T.climb + 1.0, position: [3.5, 2.1, 0.7], target: [2.75, 0.95, -2.7], fov: 34, focus: [b.boardAt.x, b.boardAt.y, b.boardAt.z] },
    { t: T.britain + 0.8, position: [2.4, 5.0, 6.5], target: [1.6, 0.9, -3.6], fov: 38, focus: [1.6, 0.8, -3.4] },
    { t: T.end + 1.2, position: [2.1, 2.4, 3.6], target: [1.75, 0.55, -1.7], fov: 38, focus: [1.7, 0.3, -1.6] },
'''+s[cam_end:]
rep("const home = new THREE.Vector3(FACTORY_A.x - 1.6 + i * 0.22, 0, FACTORY_A.z + 1.7);","const home = a.shellAt(i);")
rep("const from = new THREE.Vector3(FACTORY_A.x, 0, FACTORY_A.z + 1.25);","const from = new THREE.Vector3(FACTORY_A.x, 0, FACTORY_A.z + 1.1);")
rep("s.group.position.set(FACTORY_B.x - 1.6 + i * 0.22, 0, FACTORY_B.z + 1.7);","s.group.position.copy(b.shellAt(i));")
rep("width: 1.4, age: t - T.money1 - 0.55, scale: 0.35 });","width: 1.2, age: t - T.money1 - 0.55, scale: 0.3 });")
rep("dx: -1.2 * smooth(walk),","dx: -0.9 * smooth(walk),")
rep("look: { aperture: 11, maxBlur: 18, exposure: 1.08, glowThreshold: 0.85, glowStrength: 0.7 } };","look: { aperture: 9, maxBlur: 16, exposure: 0.92, glowThreshold: 0.95, glowStrength: 0.75, contrast: 1.08 } };")
rep("point: at([FACTORY_A.x - 0.9, 1.05, FACTORY_A.z + 1.25]), text: 'IDLE', dx: -120, dy: -260","point: at([FACTORY_A.x - 0.8, 0.95, FACTORY_A.z + 1.05]), text: 'IDLE', dx: -120, dy: -240")
rep("point: at([FACTORY_A.x - 0.6, 0.3, FACTORY_A.z + 1.7]), text: 'MORE SHELLS', dx: -60, dy: -330","point: at(a.shellAt(2).setY(0.3)), text: 'MORE SHELLS', dx: -60, dy: -300")
rep("point: at([FACTORY_A.x + 1.35, 1.45, FACTORY_A.z + 1.75]), text: 'BARELY MOVE', dx: -40, dy: -300","point: at(a.boardAt.clone().setY(1.17)), text: 'BARELY MOVE', dx: 60, dy: -260")
rep("point: at([FACTORY_B.x - 0.9, 1.05, FACTORY_B.z + 1.25]), text: 'FLAT OUT', dx: -100, dy: -280","point: at([FACTORY_B.x - 0.8, 0.95, FACTORY_B.z + 1.05]), text: 'FLAT OUT', dx: -100, dy: -260")
rep("point: at([FACTORY_B.x - 0.5, 0.35, FACTORY_B.z + 1.7]), text: 'NO MORE SHELLS', dx: -80, dy: -320","point: at(b.shellAt(4).setY(0.3)), text: 'NO MORE SHELLS', dx: -80, dy: -300")
rep("point: at([FACTORY_B.x + 1.35, 1.45, FACTORY_B.z + 1.75]), text: 'PRICES CLIMB', dx: -380, dy: -260, accent: INK.red","point: at(b.boardAt.clone().setY(1.17)), text: 'PRICES CLIMB', dx: -120, dy: -260, accent: INK.red")
open(p,'w').write(s)
print('edited')
