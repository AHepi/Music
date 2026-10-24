  // ------------------------------------------------------------------------------ the camera
  // The camera rule: still unless a move lands the point; at most three moves per shot.
  // Shot 1, the noodle shop: it holds on the counter (the empty spot where the money will land, the
  // bowl and its price); one zoom in as the bank "sets out to double the money", narrowing onto the
  // stack as it doubles; then it holds. Focus slides to the bowl for "they barely move" (free).
  const stackFocus = [stackBase.x, stackBase.y + 0.6, stackBase.z];
  const bowlFocus = [bowlAt.x, bowlAt.y + 0.4, bowlAt.z];
  const shotA = kit.stillShot({ position: [-0.1, 0.05, -0.2], target: [-0.3, -0.4, -24], fov: 38, focus: stackFocus }, [
    { from: T.sets - 0.1, to: T.double + 0.6, kind: 'zoom in', position: [-0.22, 0.0, -0.9], target: [-0.4, -0.3, -24], fov: 36 },
    { from: T.forEight, to: T.forEight + 0.6, kind: 'focus', focus: bowlFocus },
  ], { name: 'the noodle shop' });
  // Shot 2, the bank street: it holds low on the pavement with the bank behind while both towers
  // rise; on "the gains went to whoever owned the most" one zoom in narrows onto the rich tower as it
  // grows and the coins pour down by it; then it holds to the end.
  const richFocus = [rich.base.x, rich.base.y + 1.6, rich.base.z];
  const shotB = kit.stillShot({ position: [0, 0, 0], target: [0, -0.6, -30], fov: 40, focus: 8 }, [
    { from: T.gains - 0.1, to: T.went + 0.8, kind: 'zoom in', position: [0.3, 0.1, -1.4], target: [0.8, -0.2, -30], fov: 38, focus: richFocus },
  ], { name: 'the bank street' });
  kit.shake(T.double + 0.1, 0.008, 0.15);
  kit.shake(T.creates2 + 0.3, 0.008, 0.2);
