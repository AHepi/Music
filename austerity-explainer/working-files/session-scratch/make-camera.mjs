// writes the test projector's camera.json from a position and an aim point
import * as THREE from '/home/user/work/paper-pop-up-film-kit/paper-film/node_modules/three/build/three.module.js';
import fs from 'node:fs';
const camera = new THREE.PerspectiveCamera(44, 1080 / 1920, 0.1, 200);
camera.position.set(-2.6, 1.25, 12.6);
camera.lookAt(0.4, 1.05, -1.8);
camera.updateMatrixWorld(true);
const settings = { note: 'Test projector for projection-test.js: the camera the stand-in painting is drawn from (three.js Y-up world space; fov is vertical, degrees). Same pose as chapter 2 page 3\'s "both works" shot.',
  position: camera.position.toArray(), quaternion: camera.quaternion.toArray().map((v) => +v.toFixed(7)), fov: 44, aspect: 1080 / 1920, near: 0.1, far: 200 };
fs.writeFileSync('/home/user/work/paper-pop-up-film-kit/examples/projection-test/camera.json', JSON.stringify(settings, null, 1));
console.log(settings);
