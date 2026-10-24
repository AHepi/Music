# Confirmed review findings for page 10

- [must fix] at 253.7-255.6 s: While Malina says 'five point six', the unemployment figure is still counting up (it shows 4.8% at 254.5 s). It only reaches 5.6% at about 255.0 s and starts fading at 255.29 s, so the chapter's key 'who pays' number is never held still on screen.
  Suggested fix: page-10.js line ~203: finish the count on her words, e.g. ramp(t, T.to2 - 0.1, T.five2 + 0.25). Keep the figure and dots on screen until about T.thisYear + 0.2 instead of T.and - 0.1 (lines ~204-206).
  Evidence: page-10.js: jobless = lerp(3.2,5.6,smooth(ramp(t,T.to2,T.six+0.2))), until T.and-0.1. Word times: five 253.84, six 254.84, And 255.39. p10-s/still-254.50.jpg shows 4.8%.

- [should fix] at 244.9-245.4 s and 251.5-255.6 s: The interest-rate needle overshoots to about 6 (the top of the dial) just as she says 'five and a half' (spring damping 0.6 gives about 9.5% overshoot). Later, while she says unemployment rose, it slides visibly from 5.5 to about 2.6, implying rate cuts nobody mentions, right beside the 5.6% figure.
  Suggested fix: page-10.js lines 114-118: cap the value at 5.5 (v = Math.min(5.5, ...)) and move the ease to ramp(t, T.thisYear - 0.05, T.raising - 0.05).
  Evidence: page-10.js lines 114-118; p10-s/still-254.50.jpg and critique/p10-dial-crop.jpg (needle near 2.6 at 254.5 s).

- [should fix] at 238.8-259.4 s: The dial's printed label runs into its scale numbers and reads '0INTEREST RATE6'.
  Suggested fix: page-10.js line 71: label: 'INTEREST' (as on page 9), or max: 7.
  Evidence: critique/p10-dial-crop.jpg; page-10.js line 71.

- [should fix] at 259.5-270 s: The 'someone' who says 'New money causes inflation' is a stern politician with a strong blue tie, in a chamber that looks like Westminster. Blue is a major New Zealand party colour (guide line 114: no party colours), it turns 'someone' into 'a politician', and the quote is small italic text.
  Suggested fix: Recolour the tie to charcoal (a tint on that area of the cut-out). Make the quote a proper hook of about 72 px, set upright rather than italic.
  Evidence: p10-d/still-261.60.jpg; guide line 114; page-10.js lines 91-93 and 214-225.

- (nice to have) 'to bring prices down' is the only lowercase hook: set it in capitals. Add a small key under the dot panel: 'EACH DOT = 1 IN 100 WORKERS'. Add a small credit 'Stats NZ; Reserve Bank' at the figures.
- ALREADY DONE by the lead: the politician's tie is now charcoal in the shared piece politician-face.png (no change needed in your page for that). Still yours: make the quote "New money causes inflation." a proper upright hook of about 72 px instead of small italics.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
