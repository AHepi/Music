    // part B things
    towers.forEach((tower) => {
      let h = 0;
      const base = tower.base;
      tower.shadowHolder.visible = !a && t >= tower.bundles[0].landAt - 0.05;
      tower.bundles.forEach((b) => {
        if (a) { b.group.visible = false; return; }
        dropBundle(b, t, base.x, base.y + h, base.z, 0.36, 2.6);
        h += b.height;
      });
    });
    // the coins: each falls straight down onto its spot (the flagstones, the coin below it, or the
    // top of the rich tower) and stays there, lying with the slope of the surface
    pour.forEach((c) => {
      const fall = Math.sqrt(2 * c.drop / 30), age = t - c.land;
      if (a || age < -fall) { c.group.visible = false; return; }
      c.group.visible = true;
      if (age < 0) {
        const k = 1 + age / fall;
        c.group.position.set(c.spot.x, c.restY + c.drop * (1 - k * k), c.spot.z);
        c.group.rotation.set(c.tilt0 + age * c.spin, c.yaw, 0);
      } else {
        // a tiny hop just after landing (always upward from the resting height), then still
        const hop = 0.025 * Math.exp(-age / 0.06) * Math.abs(Math.sin(Math.PI * age / 0.1));
        c.group.position.set(c.spot.x, c.restY + hop, c.spot.z);
        c.group.rotation.set(-c.spot.slope, c.yaw, 0, 'YXZ');
      }
    });
    coinFloorSpots.forEach((s) => { if (s.shadow) s.shadow.visible = !a && t >= s.firstLand; });
