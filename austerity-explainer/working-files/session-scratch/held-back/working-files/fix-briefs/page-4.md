# Confirmed review findings for page 4

- [must fix] at 92.2-93.4 s ('Homes can't be built'): The change from the rent-strike street to the foundation looks broken. The board tips over while the NOTICE RENT RAISED paper hangs on its own in mid-air, the women sink into the cobbles so only their heads show, and a cream foundation slab cuts in at the bottom right, all under the payoff line.
  Suggested fix: page-4.js: fade the notice and the women out (opacity or a sideways slide) before the board tips, rather than lowering them through the ground. Or cut on 'Homes' with the page's existing short fade dip, so the foundation shot starts clean.
  Evidence: p4-j/still-92.90.jpg (rendered 12:42, same time as the latest page-4.js).

- [should fix] at 83.7-84.4 s: Under the hedged UP TO +25% sits an unhedged second line, A QUARTER MORE. That partly undoes today's fact-check hedge (actual rises were up to 25% in some districts), and she says 'as much as a quarter'.
  Suggested fix: page-4.js line 258: change the text to 'AS MUCH AS A QUARTER', or delete the line.
  Evidence: critique/a-083.80.jpg; page-4.js line 258; ledger row 264.

- [should fix] at 90.3-92 s: PARLIAMENT is a muted-grey hook on the dark stone wall and can hardly be read, so the stamp lands with no clear actor.
  Suggested fix: page-4.js line 264: change colour INK.muted to INK.paper.
  Evidence: critique/a-091.60.jpg; p4-j/still-91.90.jpg

- (nice to have) HOUSEHOLDS caption sits on the lamp glow: move the counter/caption block up 60-80 px. Use the curly apostrophe ’ in CAN’T.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
