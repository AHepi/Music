// What this does: chapter 1, page 1, "The speech" (parliament). Source: Clara E. Mattei, The
// Capital Order (2022).
//
// What happens, tied to Malina's words:
//   "You've heard the speech"      an invented politician at a lectern folds up (no real person)
//   "Times are tough ... down"     his paper jaw moves with Malina's voice, as if he gives the speech
//   "cut spending"                 scissors cutting a paper chain of people fold up
//   "push up interest rates"       a stack of coins with an arrow folds up, and jumps on "up"
//   "hold wages down"              a pay packet folds up; an iron weight drops on it on "down"
//   "austerity"                    AUSTERITY pops up
//   "birthday"                     a birthday cake with one candle drops onto the lectern
//   "Economist Clara E. Mattei"    the politician goes; her book folds up (title and name only)
//   "dug through the archives"     a stack of archive boxes folds up
//   "First World War"              a single artillery shell drops in
//   "stopping something"           AUSTERITY folds away; STOP WHAT? pops up

import { popUp, popUpUntil, foldDown, dropIn, hop, slapFlat, degrees, knock, loadMouthTrack } from '../paper-kit.js';

export const SHEETS = ['parliament'];

export async function build(kit) {
  const at = kit.at;
  const politician = await kit.speaker('politician', { width: 7.6, x: 0, y: 0.0, z: 1.4, jawDropShare: 0.018 });
  const mouthOpen = await loadMouthTrack('/paper-film/scene-data/chapter-1-page-1-mouth.json');
  const scissors = await kit.piece('scissors-chain', { width: 3.2, x: -2.6, y: 10.4, z: 0.9 });
  const coins = await kit.piece('coins-arrow', { width: 1.9, x: 2.7, y: 10.3, z: 0.9 });
  const payPacket = await kit.piece('pay-packet', { width: 2.3, x: 0, y: 12.5, z: 0.8 });
  const weight = await kit.piece('iron-weight', { width: 1.8, x: 0.05, y: 12.5, z: 1.1 });
  const austerity = await kit.word(['AUSTERITY'], { size: 1.0, x: 0, y: 12.3, z: 0.55 });
  const cake = await kit.piece('cake', { width: 2.4, x: 0.2, y: 1.45, z: 2.3 });
  const book = await kit.piece('book', { width: 3.5, x: 1.3, y: 2.4, z: 1.5, yaw: degrees(-5) });
  const boxes = await kit.piece('archive-boxes', { width: 2.2, x: -2.6, y: 1.5, z: 2.2 });
  const shell = await kit.piece('shell-4', { width: 0.8, x: -0.55, y: 1.7, z: 2.7 });
  const stopWhat = await kit.word(['STOP WHAT?'], { size: 1.0, x: 0, y: 12.3, z: 0.55 });

  const T = {
    politician: at("You've") - 0.18,
    mouthFrom: at('Times') - 0.05, mouthTo: kit.end('down') + 0.05,
    scissors: at('Cut') - 0.12,
    coins: at('push') - 0.10, coinsUp: at('up') + 0.02,
    payPacket: at('hold') - 0.10,
    weightLands: at('down') + 0.04,
    objectsAway: at('But') - 0.25,
    austerity: at('austerity') - 0.06,
    cakeLands: at('birthday') + 0.02,
    politicianAway: at('Economist') - 0.32,
    book: at('Economist') - 0.08,
    bookHop: at('found') + 0.02, bookHop2: at('argues') + 0.02,
    boxes: at('dug') - 0.10,
    shellLands: at('War') + 0.04,
    austerityAway: at('budgets') + 0.30,
    stopWhat: at('stopping') - 0.06,
  };
  kit.shake(T.weightLands, 0.05, 0.12);
  kit.shake(T.cakeLands, 0.03, 0.1);
  kit.shake(T.shellLands, 0.04, 0.12);

  function pose(t) {
    // the politician, speaking (his jaw follows Malina's voice while she quotes the speech);
    // he jolts a little when the cake lands on his lectern
    const politicianPose = popUpUntil(t, T.politician, T.politicianAway, politician.piece);
    if (politicianPose.visible && t > T.cakeLands && t < T.politicianAway) politicianPose.fold = (politicianPose.fold ?? 0) + knock(t - T.cakeLands, degrees(2), 4, 0.15);
    kit.place(politician.piece, politicianPose);
    politician.setOpen(t >= T.mouthFrom && t <= T.mouthTo ? mouthOpen(t) : 0);

    // the three promises
    const wiggle = t > T.scissors + 0.3 ? degrees(2.5) * Math.sin(2 * Math.PI * 1.6 * (t - T.scissors)) * Math.exp(-(t - T.scissors - 0.3) / 0.9) : 0;
    kit.place(scissors, { ...popUpUntil(t, T.scissors, T.objectsAway, scissors), roll: wiggle });
    const rise = t > T.coinsUp ? 0.5 * (1 - Math.exp(-(t - T.coinsUp) / 0.12)) : 0;
    kit.place(coins, { ...popUpUntil(t, T.coins, T.objectsAway + 0.05, coins), dy: rise });

    // the pay packet is squashed: the weight lands on top of it, it slaps flat and the weight sinks to the floor
    if (t < T.weightLands) kit.place(payPacket, popUp(t, T.payPacket, payPacket));
    else kit.place(payPacket, t < T.weightLands + 0.4 ? slapFlat(t, T.weightLands, 0.1) : { visible: false });
    const onPacket = payPacket.height * 0.55;
    const fall = dropIn(t, T.weightLands, { fall: 0.3, height: 9, roll: 5, bounce: 0.15 });
    const sink = t < T.weightLands ? onPacket : onPacket * Math.max(0, 1 - (t - T.weightLands) / 0.1);
    const weightPose = fall.visible ? { ...fall, dy: fall.dy + sink } : fall;
    kit.place(weight, t < T.objectsAway + 0.1 ? weightPose : foldDown(t, T.objectsAway + 0.1, 0.2));

    // AUSTERITY, then the cake on the lectern
    kit.place(austerity, popUpUntil(t, T.austerity, T.austerityAway, austerity));
    const cakePose = dropIn(t, T.cakeLands, { fall: 0.28, height: 10, roll: -6, bounce: 0.18 });
    kit.place(cake, t < T.politicianAway ? cakePose : foldDown(t, T.politicianAway, 0.2));

    // Mattei's book and the archives
    kit.place(book, { ...popUp(t, T.book, book), dy: hop(t, T.bookHop, 0.2) + hop(t, T.bookHop2, 0.16) });
    kit.place(boxes, popUp(t, T.boxes, boxes));
    kit.place(shell, dropIn(t, T.shellLands, { fall: 0.3, height: 11, roll: 8, bounce: 0.2 }));
    kit.place(stopWhat, popUp(t, T.stopWhat, stopWhat));
  }

  return { pose };
}
