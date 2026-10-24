# Confirmed review findings for page 9

- [should fix] at 234.7-238.3 s: The pay packet is an unlabelled envelope. Once the weight lands it becomes a blank tan slab (it lands face-down), so 'workers lose the power to ask for more' reads as a weight on a mat.
  Suggested fix: page-9.js: print 'WAGES' on the envelope, and flip the slapFlat fold sign (line ~183) so the printed face stays up. Check that the weight still sits on it.
  Evidence: critique/p9/still-234.90.jpg and still-235.40.jpg; page-9.js lines 183-186.

- [should fix] at 218.7-221.4 s: For 'Loans cost more, people spend less', the coin stack sits at the very bottom edge, half cut off and in the bottom button zone, so the mechanism is not shown.
  Suggested fix: page-9.js: move the coin stack up onto the pavement (screen y about 1100-1400).
  Evidence: p9-e/still-220.60.jpg

- (nice to have) Add a small credit for the 1920-21 figures ('Bank of England data') at the bars.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
