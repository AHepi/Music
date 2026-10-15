// What this does: page 5 of chapter 2 for newcomers, "The rule" (about 95.7 to 123.5 s; plan 34, part 2, shots 5a
// and 5b in shots.json). Malina: "No spare workers, materials or machines... so no extra things get made. More
// money... and the same things to buy. So businesses can ask more... and prices go up. Most economists agree on this
// much. When new money is spent... and there are spare workers, materials and machines... it mostly gets more things
// made. When nothing is spare... it mostly pushes prices up."
//   5a  W2, the flat-out gate, held on the composed frame where page 4 stopped (page 4 runs on into it with no join
//       you can see: the same view, the same question and full guess ring until "spare"). On "spare" the question and
//       ring clear (gone before NO SPARE comes, so the two never overlap); NO SPARE; MORE MONEY, + SAME THINGS TO BUY
//       (the crates in the gateway stay as they are), → PRICES UP on "prices" with a price arrow over No. 2 that climbs
//       (reaching its top on "up"), so the page's conclusion is up about 1.2 s before the cut. Every word here ends
//       exactly on the cut to W3 (no fade a frame early, so the cut is one clean step). Live: as page 4.
//   5b  W3, both factories, held, with the rule over them. Cut on "Most"; the small name tags QUIET and FLAT OUT over
//       the two columns; MOST ECONOMISTS AGREE (small, above the rule cards); the upper rule card NEW MONEY SPENT +
//       SPARE → MOSTLY MORE THINGS MADE with a thin line to No. 1's chimney; the lower rule card NOTHING SPARE →
//       MOSTLY PRICES UP with a thin line to No. 2's chimneys; both over a soft dark band (the smoke crosses the top
//       band). Then the 2-second hold on the rule cards and the page peel. Live: No. 2's smoke and window flicker,
//       No. 1's brazier and lantern.
// The one Works set serves both views: at the cut the projector moves from W2's plate camera to W3's (setView).
// Page 16 shows the same rule cards: it imports RULE_CARDS and drawRule from here, and the tags come from works-effects.js.
import { clamp01 } from '../cinema-kit.js';
import { buildWorks, WORKS_IN_USE } from './works-effects.js';
import { buildWords, ruleCard, topShade, priceArrow, INK, TEXT_LEFT, TEXT_RIGHT } from '../graphics.js';
import { drawQuestion, LOOK } from './page-4.js';

// How this page leaves: the page peel after the 2-second hold on the rule cards.
export const join = { kind: 'peel', after: 2.0, length: 0.85 };

// The pictures shone onto the set. Until the paintings are approved, the PLATES stand in for them.
export const PICTURES = {
  w2: 'works-w2-plate.jpg',   // W2, No. 2 flat out (the same picture page 4 ends on)
  w3: 'works-w3-plate.jpg',   // W3, both gates: No. 1 quiet, No. 2 flat out
};

// The rule cards' places (pixels; plan 34: 0.06 to 0.90 across, the upper about 0.08 to 0.16 down, the lower about
// 0.16 to 0.24 down). Page 16 shows the same cards and should use these. heading is the baseline of MOST ECONOMISTS
// AGREE: the tops of its letters about 0.061 down, below a phone app's top bar and inside the checker's title area
// (at 116 they were 0.047 down; round 4 of log 34). The cards are a little shorter (140 pixels: two lines of words
// and even margins) so the lower one still ends about 0.24 down, clear of the chimney lines.
export const RULE_CARDS = { heading: 142, upper: [TEXT_LEFT, 158, TEXT_RIGHT - TEXT_LEFT, 140], lower: [TEXT_LEFT, 314, TEXT_RIGHT - TEXT_LEFT, 140], size: 46 };

export async function build(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w2', 'w3'], pictures: PICTURES });
  const T = {
    first: kit.firstWordAt, spare: kit.at('spare'), more: kit.at('More'), same: kit.at('same'), prices: kit.at('prices'), up: kit.at('up'),
    most: kit.at('Most'), agree: kit.at('agree'), spent: kit.at('spent'), spare2: kit.at('spare', 2), made2: kit.at('made', 2),
    nothing: kit.at('nothing'), up2: kit.at('up', 2),
  };
  const flatOutGate = kit.stillShot(works.cameraAt('w2', 'composed'), [], { name: '5a the flat-out gate' });
  const both = kit.stillShot(works.cameraAt('w3'), [], { name: '5b both factories' });

  function pose(t) {
    const inW3 = t >= T.most;
    // in W2 the windows keep the brighter flicker page 4 gave them on "busy"; W3 always shows the factories as first described
    const still = works.set(t, { view: inW3 ? 'w3' : 'w2', painting: inW3 ? 'w3' : 'w2', no1: { state: 'quiet' }, no2: { state: 'flat out', busy: inW3 ? 0 : 1 } });
    return { camera: inW3 ? both(t) : flatOutGate(t), still, look: LOOK };
  }

  function draw2D(ctx, t) {
    topShade(ctx, 1);
    if (t < T.most) {
      // carried over from page 4, exactly as it was there, until "spare"; it has faded out (0.3 s) before NO SPARE
      // comes in, so the two are never on screen together in the same place (round 3 saw "NO SPAREPENS TO PRICES?")
      drawQuestion(ctx, t, { questionAt: T.first - 30, guessAt: T.first - 30, until: T.spare + 0.12 });
      buildWords(ctx, t, { parts: [{ text: 'NO SPARE', at: T.spare + 0.15 }], until: T.most, y: 172, size: 72, fadeOut: 0 });
      // → PRICES UP comes on "prices" with the climbing arrow (on "up" it was up only about 0.65 s before the cut)
      const pricesAt = Math.min(T.prices, T.up - 0.35);
      buildWords(ctx, t, {
        parts: [{ text: 'MORE MONEY', at: T.more }, { text: '+ SAME THINGS TO BUY', at: T.same }, { text: '→ PRICES UP', at: pricesAt, colour: INK.amber }],
        until: T.most, y: 250, size: 50, fadeOut: 0,
      });
      // the price arrow over No. 2's column climbs (prices go up), over the gable above the gate, clear of the No. 2
      // board, toward the words. It starts climbing on "prices" ("and prices go up") and reaches its top on "up": the
      // cut to both factories comes on "Most", only about 0.7 s after "up" (estimated timing)
      const column = works.screen('no-2-gate');
      if (column) priceArrow(ctx, t, { at: pricesAt, until: T.most, fadeOut: 0, drawFor: T.up - pricesAt, from: { x: Math.max(100, column.x - 330), y: 620 }, length: 430, angle: 28, word: 'PRICES' });
      return true;
    }
    // 5b: the tags over the two columns, then the rule
    works.drawTags(ctx, t, { at: T.most });
    drawRule(ctx, t, works, { agree: T.agree, spent: T.spent, spare: T.spare2, made: T.made2, nothing: T.nothing, up: T.up2 });
    return true;
  }

  return { pose, draw2D };
}

// The rule over W3, drawn the same way here and on page 16 (plan 34, T13: identical on both): MOST ECONOMISTS AGREE
// (small, above the cards), then the upper rule card NEW MONEY SPENT + SPARE → MOSTLY MORE THINGS MADE with a thin line
// to No. 1's chimney, and the lower rule card NOTHING SPARE → MOSTLY PRICES UP with a thin line to a short bar across
// No. 2's two chimneys, each part on its spoken word. times: { agree, spent, spare, made, nothing, up } (leave agree out to skip the heading).
export function drawRule(ctx, t, works, times) {
  const no1 = works.screen('no-1-chimney', { down: 4 }), no2 = works.screen('no-2-chimneys', { down: 4 });
  if (times.agree !== undefined) buildWords(ctx, t, { parts: [{ text: 'MOST ECONOMISTS AGREE', at: times.agree }], y: RULE_CARDS.heading, size: 34 });
  const [ux, uy, , uh] = RULE_CARDS.upper, [lx, ly, lw, lh] = RULE_CARDS.lower;
  ruleCard(ctx, t, {
    at: times.spent, box: RULE_CARDS.upper, size: RULE_CARDS.size,
    parts: [{ text: 'NEW MONEY SPENT', at: times.spent }, { text: '+ SPARE', at: times.spare }, { text: '→ MOSTLY MORE THINGS MADE', at: times.made, colour: INK.amber }],
    // round the lower card by the left margin, then across to No. 1's chimney below it
    line: no1 && { at: times.made + 0.2, from: [ux, uy + uh / 2], via: [[ux - 30, uy + uh / 2], [ux - 30, ly + lh + 40]], to: no1 },
  });
  ruleCard(ctx, t, {
    at: times.nothing, box: RULE_CARDS.lower, size: RULE_CARDS.size,
    parts: [{ text: 'NOTHING SPARE', at: times.nothing }, { text: '→ MOSTLY PRICES UP', at: times.up, colour: INK.amber }],
    line: no2 && { at: times.up + 0.2, from: [Math.min(lx + lw - 40, Math.max(lx + 40, no2.x)), ly + lh], to: no2 },
  });
  // the lower card's line ends on a short bar across both of No. 2's chimneys, once it has arrived
  const a = works.screen('no-2-chimney-a', { down: 4 }), b = works.screen('no-2-chimney-b', { down: 4 });
  const reached = clamp01((t - times.up - 0.7) / 0.25);
  if (no2 && a && b && reached > 0) {
    ctx.save();
    ctx.globalAlpha = reached;
    ctx.strokeStyle = INK.amber; ctx.lineWidth = 3; ctx.lineCap = 'round';
    ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(a.x, no2.y - 12); ctx.lineTo(a.x, no2.y); ctx.lineTo(b.x, no2.y); ctx.lineTo(b.x, no2.y - 12);
    ctx.stroke();
    ctx.restore();
  }
}
