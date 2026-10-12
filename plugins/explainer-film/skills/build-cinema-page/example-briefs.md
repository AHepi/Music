# Example page briefs (chapter 2, "What really causes inflation")

What this file is: three of the briefs given to the page helpers who built chapter 2, as models for
writing briefs. A good brief gives the page window, the exact narration, the research ids, and a
beat-by-beat plan (room, pieces, models, short on-screen words), leaving room for the helper's eye.

## Page 4 (Glasgow rents)

Page window: first word 74.94 s, last word ends 93.98 s. Narration: "Homes work the same way. In
1915, workers poured into Glasgow for war work, and landlords pushed rents up... by as much as a
quarter. By November, about twenty thousand households were refusing to pay the rise. Within weeks,
Parliament froze rents. Homes can't be built in a hurry." Facts: research id C2-H04.

Plan (refine with your own eye, keep the meaning):
- The painting `403-bg-glasgow-tenements` (wet cobbles, tenements at dusk). Title GLASGOW 1915 at "1915".
- "workers poured into Glasgow": the `workers-queue` cut-out walks in along the street.
- "landlords pushed rents up... by as much as a quarter": a printed card notice (kit.card) slaps on;
  hook UP TO +25% (the source says up to a quarter, not every rent).
- "about twenty thousand households were refusing to pay the rise": the `rent-strikers` cut-out
  pops up; a counter to 20,000 with caption HOUSEHOLDS REFUSING TO PAY.
- "Parliament froze rents": the `rubber-stamp` cut-out comes down hard (shake, dust); RENTS FROZEN.
- "Homes can't be built in a hurry": a small 3D `paperHouse` built very slowly; NOT IN A HURRY.
- Gentle camera drift down the street; rain-like motes or haze welcome. Default peel join.

## Page 7 (oil 1973, then today)

Page window: first word 156.22 s, last word ends 179.07 s. Narration: "Late 1973. Prices are already
climbing when the price of oil nearly quadruples, in about three months... and almost everything made
or moved with fuel gets dearer. So sometimes the cause isn't spending. It's costs. And here? The
latest figures say prices rose four point one percent in the year to June. Leave fuel out... and
it's two point nine." Facts: C2-C14 (oil $2.90 → $11.65 a barrel), C2-N05 (4.1%; 2.9% without fuel).

Plan:
- Part A: the petrol station painting at night. Title LATE 1973.
- "nearly quadruples": a 3D `oilBarrel` drops in heavily (shake, dust); a 3D `splitFlap` flips
  $2.90 → $11.65 with caption A BARREL; hook ×4 (4.02 times).
- "almost everything made or moved with fuel gets dearer": 3D `priceTag`s flip up one after another
  like dominoes (hidden until each flips); hook DEARER.
- "isn't spending. It's costs.": NOT SPENDING (dimmed, struck) then COSTS.
- Cut on "And here?" (a 0.25 s dip to black) to the suburb painting; bars 4.1% WITH FUEL then 2.9%
  WITHOUT FUEL; small credit SOURCE: STATS NZ.

## Page 10 (today, and the ending)

Page window: first word 238.75 s, last word ends 266.32 s; the film ends at 270.33 s (no join after).
Narration: "Here, our central bank, the Reserve Bank, pushed its interest rate from a quarter of a
percent to five and a half percent by twenty twenty-three, to bring prices down. Since the end of
twenty twenty-one, unemployment has climbed from three point two percent to five point six. And
this year, the Reserve Bank is raising its interest rate again. So next time someone tells you new
money causes inflation... ask them. Spent on what? And who pays to stop it?"

Plan:
- The suburb painting graded toward dusk. Title NEW ZEALAND. A 3D `dial` (interest rate) climbing
  0.25% → 5.5% by "half", small 2023.
- Unemployment 3.2% → 5.6%: a counter over a hundred-dot panel (3 then 6 empty), echoing page 2's 1915
  panel (not people in old clothes in a modern street).
- "raising its interest rate again": the dial ticks up; RISING AGAIN.
- Cut on "So next time" to the parliament painting; the invented politician (`kit.speaker`) mouths
  "new money causes inflation"; then SPENT ON WHAT? and WHO PAYS TO STOP IT? land on their words.
- After the last word, hold, then `look.fade` 0 → 1 by the film's end. `join: { kind: 'dip', after: 99, length: 1 }`.
