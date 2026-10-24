# Confirmed review findings for page 5

- [should fix] at 104.3-106 s: The subline IN TWO YEARS is orange text on the beige curtain and is almost invisible, so the screen shows only '×2 MONEY' (she does say it aloud).
  Suggested fix: page-5.js: draw it in INK.paper (white), or on the same dark scrim the chart uses, at full strength from 'two'.
  Evidence: p5-r/still-104.60.jpg

- [should fix] at 123.9-125 s: OTHER INVESTMENTS ↑ is amber text over the amber-lit bank and the stacks of notes, and it nearly disappears. It is half of the finding Malina credits to the Bank's study.
  Suggested fix: page-5.js line ~323: use INK.paper for the colour, or put one dark plate behind both SHARES and OTHER INVESTMENTS.
  Evidence: critique/p5/still-124.00.jpg

- [should fix] at 125-129 s: 'Whoever owned the most' is shown as three Edwardian plutocrats in top hats, one with a cigar, in front of 2010s London glass towers. It is a century out of period, editorialises beyond the script (guide section 5: add no claims she doesn't make), and the cut-out ends in a hard straight bottom edge that floats above the paving.
  Suggested fix: Swap the cut-out for a neutral modern one, or drop it and let the coins pour onto the taller of the two towers of notes. Whatever stays, push its bottom edge below the frame.
  Evidence: p5-d/still-126.70.jpg, critique/p5/still-126.95.jpg; page-5.js lines ~119-121.

- [should fix] at about 101.5 s: A thin orange callout leader runs up from the small money stack and ends on nothing. It is a stray mark on the kitchen wall.
  Suggested fix: page-5.js: start the callout's label together with its line, or remove that callout.
  Evidence: p5-d/still-101.50.jpg

- (nice to have) The BANK OF ENGLAND STUDY, 2012 credit is faint: draw it in INK.paper at about size 34. The chart's right axis label '8 YEARS' should read '2021' (2013 to 2021). Use the curly apostrophe ’ in BRITAIN’S.
- DECISION (from the lead): remove the `owners` cut-out (top-hatted caricature, a century out of period). Instead show "the gains went to whoever owned the most" with the money itself: coins pour onto ONE of the two towers of notes, which grows clearly taller than the other, while THE GAINS / TO THE BIGGEST OWNERS shows. No new figure.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
