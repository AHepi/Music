  // ------------------------------------------------------- part B: a City of London bank street
  // a dry painting (no wet reflections the 3D money could not match): the bank at an angle on the
  // left, open flagstones on the right and across the bottom. The towers stand on that pavement.
  const plaza = await kit.relief('406b-bg-london-bank-dry', { near: 6, far: 70, fov: 40 });
  // the floor under a spot: its point and its slope (the angle the flagstones rise toward us)
  const floorAt = (u, v) => {
    const p = plaza.pointAt(u, v), q = plaza.pointAt(u, v + 0.02);
    return { point: p, slope: Math.atan2(p.y - q.y, p.z - q.z) };   // rise per unit toward the camera
  };
  const BUNDLE = 1.15, FIRST = 12, GROW = 8;
  const towers = [floorAt(0.33, 0.085), floorAt(0.67, 0.085)].map((floor, side) => {
    const base = floor.point.clone();
    base.y += 0.03;   // the front edge of a bundle meets the slightly rising flagstones: lift so it never sinks in
    const r = seededRandom(70 + side);
    const bundles = [];
    const count = FIRST + (side === 1 ? GROW : 0);
    for (let i = 0; i < count; i++) {
      const b = banknoteBundle({ width: 0.8, depth: 0.4, notes: 44 });
      b.group.traverse((o) => { if (o.material) [].concat(o.material).forEach((m) => { m.color.multiplyScalar(0.8); }); }); // notes read as green, not white, in this light
      b.group.scale.setScalar(BUNDLE);
      b.height *= BUNDLE;
      b.group.rotation.y = (r() - 0.5) * 0.3;
      b.twist = (r() - 0.5) * 0.3;
      b.shift = [(r() - 0.5) * 0.06, (r() - 0.5) * 0.06];
      // the first ones land on "creates hundreds of billions"; on the right tower, more land on
      // "the gains went", so it grows clearly taller than the left one
      b.landAt = i < FIRST ? T.creates2 - 0.05 + i * 0.12 + side * 0.06 : T.went - 0.1 + (i - FIRST) * 0.12;
      kit.scene.add(b.group);
      bundles.push(b);
    }
    // a soft contact shadow under the tower, lying on the flagstones (tilted with them)
    const shadow = contactShadow(1.5, 0.95, 0.75);
    const shadowHolder = new THREE.Group();
    shadowHolder.add(shadow);
    shadowHolder.position.set(floor.point.x, floor.point.y + 0.012, floor.point.z);
    shadowHolder.rotation.x = floor.slope;
    kit.scene.add(shadowHolder);
    return { base, bundles, floor, shadowHolder };
  });
  const rich = towers[1];
  const richTop = rich.base.y + rich.bundles.reduce((h, b) => h + b.height, 0);
  const lastBundle = rich.bundles[rich.bundles.length - 1];
  // the gold coins: they pour down by the rich tower. Each one falls straight down onto its own spot
  // and stays there: before the tower has finished growing they land in little stacks on the
  // flagstones at its foot; after, on its top. Every coin rests exactly on the surface or coin below.
  const COIN_R = 0.13, COIN_T = 0.03;
  const pour = [];
  {
    const r = seededRandom(23);
    const floorSpots = [];
    // spots in front of and beside the tower's foot (clear of its footprint), as (u, v) on the painting
    [[0.56, 0.058], [0.61, 0.05], [0.66, 0.045], [0.71, 0.05], [0.76, 0.058], [0.585, 0.03], [0.64, 0.024], [0.695, 0.026], [0.745, 0.034], [0.79, 0.075], [0.53, 0.07]]
      .forEach(([u, v]) => { const f = floorAt(u, v); floorSpots.push({ x: f.point.x, y: f.point.y, z: f.point.z, slope: f.slope, count: 0 }); });
    // spots on the top of the tower (inside the top bundle's face)
    const topSpots = [[-0.22, -0.06], [0, 0.05], [0.2, -0.05], [-0.1, 0.1], [0.12, 0.1]]
      .map(([dx, dz]) => ({ x: rich.base.x + lastBundle.shift[0] + dx, y: richTop + 0.006, z: rich.base.z + lastBundle.shift[1] + dz, slope: 0, count: 0 }));
    const count = 56, from = T.gains + 0.05, to = T.last + 0.6;
    const topFrom = lastBundle.landAt + 0.35;
    for (let i = 0; i < count; i++) {
      const c = coin({ radius: COIN_R, thickness: COIN_T });
      kit.scene.add(c.group);
      const land = from + (i / count) * (to - from) + r() * 0.03;
      const spots = land > topFrom && i % 3 !== 0 ? topSpots : floorSpots;
      const spot = spots[Math.floor(r() * spots.length)];
      const layer = spot.count++;
      pour.push({ group: c.group, land, spot, restY: spot.y + COIN_T * (layer + 0.5) + 0.004 + layer * 0.001,
        drop: 2.2 + r() * 0.8, spin: 6 + r() * 8, tilt0: r() * Math.PI, yaw: r() * Math.PI * 2 });
    }
    // small shadows under the coin stacks on the flagstones
    floorSpots.filter((s) => s.count > 0).forEach((s) => {
      const holder = new THREE.Group(); holder.add(contactShadow(0.42, 0.3, 0.55));
      holder.position.set(s.x, s.y + 0.006, s.z); holder.rotation.x = s.slope;
      s.shadow = holder; kit.scene.add(holder);
      s.firstLand = Math.min(...pour.filter((c) => c.spot === s).map((c) => c.land));
    });
    var coinFloorSpots = floorSpots;
  }
  const plazaMotes = new Motes(kit.scene, { count: 120, min: [-2.5, -2.2, -14], max: [2.5, 2.5, -6], size: 0.03, seed: 29, opacity: 0.35, colour: 0xdfe6ee });
