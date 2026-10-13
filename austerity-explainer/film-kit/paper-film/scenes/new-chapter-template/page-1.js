// What this does: a template page. Copy it for each page of a new chapter and replace the pieces,
// words and timings. Everything here is an example of one way to use the toolkit; delete what the
// page does not need.
//
// Write at the top, in plain words, what happens on which spoken word, like this:
//   "the commons"     a field with grazing cows folds up
//   "fenced off"      a fence slides in from the right; the cows fold away
//   "for sheep"       a flock of sheep drops in
//   "enclosed"        ENCLOSED pops up

import { DustBurst } from '../../stage/paper-stage.js';
import { popUp, popUpUntil, foldDown, dropIn, slideIn, hop, knock, degrees, loadMouthTrack } from '../paper-kit.js';

// The painted sheets this page uses, by their names in the cut list's "backgrounds" (top one first).
// A page with two sheets turns its first sheet over part-way through (see "turns" below); the last
// page of a film can end on 'blank', a plain dark sheet.
export const SHEETS = ['village-green'];

export async function build(kit) {
  const at = kit.at;      // at('word') = when the narrator starts that word; at('word', 2) = its second time on this page
  const end = kit.end;    // end('word') = when the word finishes

  // ---------------------------------------------------------------- the pieces
  // Positions are in world units: the visible frame is about 9 wide (x from -4.5 to 4.5) and 16 tall
  // (y from 0 at the bottom to 16 at the top). x, y place the middle of a piece's bottom edge (its
  // hinge). z is how far it stands in front of its sheet: 0.55 for words, about 0.6 to 3 for
  // pieces; further forward looks bigger, casts a longer shadow and covers what is behind it.
  // Keep each piece's edges inside the frame at its own distance (about 4.1 from the middle, less
  // for pieces further forward), or the frame cuts them off.
  const field = await kit.piece('commons-field', { width: 7.0, x: 0, y: 3.0, z: 1.0 });
  const fence = await kit.piece('fence', { width: 8.0, x: 0, y: 1.0, z: 2.0 });
  const sheep = await kit.piece('sheep-flock', { width: 6.0, x: 0.3, y: 2.2, z: 2.4 });
  // words: plain heavy letters cut from off-white card; size 1 = letters about one unit tall
  const enclosed = await kit.word(['ENCLOSED'], { size: 1.0, x: 0, y: 12.2, z: 0.55 });
  // a printed card or sign (dark ink on card); look sets colours, see makeCardTexture in the stage
  const notice = await kit.card(['NOTICE OF', 'ENCLOSURE'], { width: 4.0, x: -2.0, y: 7.0, z: 0.6 });
  // dust or smoke must be made through kit.effect, so it is put away with the page
  const dust = kit.effect(new DustBurst({ count: 20, seed: 3 }));
  // a speaking figure (face, jaw and mouth layers made by the cut list's "jaw" setting):
  // const farmer = await kit.speaker('farmer', { width: 6, x: 0, y: 0, z: 1.4 });
  // const mouthOpen = await loadMouthTrack('/examples/new-chapter-template/mouth-page-1.json');

  // ---------------------------------------------------------------- when things happen
  const T = {
    field: at('commons') - 0.12,             // pop-ups start a little before their word
    fenceSlides: at('fenced') - 0.2,
    fieldAway: at('fenced') + 0.4,
    sheepLand: at('sheep') + 0.03,           // things that land, land just after their word starts
    enclosed: at('enclosed') - 0.06,
    notice: at('enclosed') + 0.3,
  };
  kit.shake(T.sheepLand, 0.06, 0.12);        // a camera shake when something heavy lands

  // ---------------------------------------------------------------- where everything is at time t
  function pose(t) {
    kit.place(field, popUpUntil(t, T.field, T.fieldAway, field));            // folds up, later folds away
    kit.place(fence, slideIn(t, T.fenceSlides, { from: 12 }));               // slides in from the right
    const landed = dropIn(t, T.sheepLand, { fall: 0.3, height: 10 });       // falls from above and bounces
    kit.place(sheep, landed);
    dust.set({ origin: { x: sheep.restX, y: sheep.restY + 0.3, z: sheep.restZ + 0.2 }, width: sheep.width * 0.8,
      age: t >= kit.foldAwayAt.get(kit.sheets[0]) ? 9 : t - T.sheepLand });
    kit.place(enclosed, popUp(t, T.enclosed, enclosed));
    kit.place(notice, popUp(t, T.notice, notice));
    // farmer.setOpen(mouthOpen(t));  kit.place(farmer.piece, popUp(t, at('said') - 0.2, farmer.piece));
  }

  // Pieces fold away and the page turns by themselves 0.3 s after the page's last word. A page with
  // two sheets says when its first sheet turns:
  //   return { pose, turns: [{ sheet: kit.sheets[0], from: end('word') + 0.15, length: 0.75 }] };
  return { pose };
}
