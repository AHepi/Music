export const meta = {
  name: 'round-20-fix-review',
  description: 'Seven helpers fix the problems an independent reviewer found on pages 1, 4, 5, 6, 7, 9, 10; one fresh reviewer checks the fixes',
  phases: [
    { title: 'Fix', detail: 'one helper per page applies the reviewer list' },
    { title: 'Check', detail: 'a fresh reviewer verifies every fix and looks for new problems' },
  ],
}

const KIT = '/home/user/work/paper-pop-up-film-kit'
const GUIDE_1 = '/home/user/work/chapter-2/reference/20 Guide - building a cinema page.md'
const GUIDE_2 = '/home/user/work/chapter-2/reference/21 Guide - camera rule, filling the frame, no clipping.md'

const PAGES = [
  { n: 1, window: '0.0 20.4', list: `1. 5.2-17 s: the polished steel counter fills the bottom 25-30% of every checkout frame with nothing on it. Aim the hold pose about 3-4 degrees lower or raise the camera slightly so the belt and basket sit lower in the frame (keep the tags clear of the shelves and each other).
2. 17.4 s: the folded basket shows as a thin card floating above the belt with its shadow below, as if hovering. Hide it at about 70% fold instead of 90%, or fold it away from the camera.
3. 16.3 s (minor): the right column of shelf tags reaches about x 945, into the right 140 px zone. Move that column about 10-20 px left.` },
  { n: 4, window: '74.7 95.1', list: `1. 82.3-91 s: both notice-board post feet end over a dark, torn-looking hole in the painted cobbles; the posts look sunk into a pit. Move the board to flatter cobbles (about u +-0.03) or add a small contact shadow and base plate at the feet.
2. 74.7-79.5 s: about 5 s of empty street, wet cobbles across the bottom half, nothing in it. Start the workers' file entering about 2 s earlier, or open on a tighter hold.
3. 83.7 s: "AS MUCH AS A QUARTER" is almost unreadable (dim grey on the building). Brighten it or give it a dark plate.
4. 90.5-91.3 s: the stamp handle overlaps "PARLIAMENT" at 90.5; at 91.3 the stamp still covers "RENTS" on the RENTS FROZEN card and the board is cut by the left frame edge. Lift the stamp clear quickly after the slam and shift the notice framing about 40 px right.` },
  { n: 5, window: '95.2 128.4', list: `1. 125.5-126.7 s: falling coins' contact shadows show as dark grey ovals on the front of the bundle towers, mid-air, on both towers. Show each coin's shadow only during its last 0.1 s of fall or only once landed (and only on the surface it lands on).
2. 95.2-112.9 s: the noodle shop's bottom 35-40% is dark stools and black; the ramen bowl fills only about 35% of the width. Start the hold lower and closer to the counter (for example position y -0.1 and z -0.6) so the bowl and counter fill the frame.
3. 128.4 s (minor): "TO THE BIGGEST OWNERS" sits very close to the coins on the tower top. Move the text about 30 px left or up.` },
  { n: 6, window: '128.5 155.9', list: `1. 141.4 s: after the gate zoom the bottom quarter is empty snow and tracks; the padlock and steel are small and the steel stack reaches about 95% of the frame width. Zoom about 2 degrees tighter and aim slightly lower and left.
2. 143.9 s (minor): a falling note crosses the end of "WITH NEW MONEY". Keep the notes' fall paths away from the text.
3. 141.4 s (minor): "IN PROTEST" is low-contrast grey on the sky. Brighten it.` },
  { n: 7, window: '156.0 180.2', list: `1. 156-159.6 s: the opening wide shot has empty forecourt across the bottom 40% and no subject until the barrel drops. Open tighter/lower so the frame is full.
2. 165.4-170.6 s: after the zoom out the barrel fills only about 28% of the width; the arrow tags are tiny (about 55 px tall) and sit inside the bottom 380 px. Zoom out less (for example fov 34) and raise the tag row about 120 px; make the tags bigger.
3. 173-180 s (minor): the New Zealand shot still has road and pavement in its bottom third. Aim slightly lower or move the panel's subject so the frame is fuller.` },
  { n: 9, window: '208.3 238.3', list: `1. 222.6-238.3 s: the wider start shows the mirrored painting below the picture's bottom edge (a ghostly mirrored kerb or figure bottom right, clearly at 231.6 and 236.3 s). Tilt about 1.5 degrees less in that pose, or put a soft dark gradient over the bottom 150 px.
2. 234.9-238.3 s: "WAGES" on the envelope sits at about y 1575, inside the bottom 380 px. Move the envelope up about 50 px on screen (keep it clear of the workers and the ground) or adjust the aim.
3. 231.6-238.3 s: the credit line "Clara E. Mattei, The Capital Order (2022)" is faint and tiny and almost touches the book top (about 15 px). Size 28 or larger, brighter, a dark plate or 20 px more room.
4. 219.6 s: "LOANS COST MORE" touches the top of the dial ring; the dial's 7 and 8 sit in the right 140 px zone; the bank is cut by the left edge. Move the hook text up about 40 px and shift the pan-down aim about 0.2 left.
5. 208.3-212 s: empty street with wet tracks in the bottom half before the bank and meter appear. Make the opening frame fuller (tighter or lower) or bring the first subject in earlier.` },
  { n: 10, window: '238.4 270.3', list: `1. 254.9 s: in the hundred-dot panel the unemployed dots are thin red or white outlines that barely show on the dark plate, so 5.6% does not read; the legend text is small. Fill those dots solid red and make the legend bigger.
2. 254.9 s (minor): the right edge of the dial (numbers 5 and 6) enters the right 140 px zone. Move the dial about 40 px left in the zoomed-out framing.
3. 238.4-240.5 s (minor): the dial is small (about 37% of the width) with empty road across the bottom quarter. Tighter or lower opening.
4. 247.8 s (minor): "TO BRING PRICES DOWN" is faint. Brighten it.` },
]

const REPORT = { type: 'object', properties: {
  page: { type: 'number' }, sheet: { type: 'string' }, camera_check: { type: 'string' },
  fixed: { type: 'array', items: { type: 'string' }, description: 'one line per numbered problem: what was changed and how it was checked' },
  unsure: { type: 'array', items: { type: 'string' } },
}, required: ['page', 'sheet', 'camera_check', 'fixed', 'unsure'] }

const prompt = (p) => `You are fixing page ${p.n} of a cinematic explainer film (chapter 2, "What really causes inflation"; vertical 1080x1920, three.js). Another helper already reworked this page this round (a still camera with at most 3 moves per shot, frame filling, nothing clipping); an independent reviewer then looked at it and listed problems. Fix every one of them, and do not undo the earlier work.
Read both guides first: ${GUIDE_1} and ${GUIDE_2} (this round's rules: the camera rule, filling the frame, nothing passing through anything). The shared tools were improved since the last helper: room.clearance now also samples points across each face (not only corners), boxesOverlap ignores hidden parts, and a cut-out's set({ opacity }) now works.
Your page: ${KIT}/paper-film/scenes/inflation-chapter-2/page-${p.n}.js. Its window: ${p.window} seconds.

The reviewer's list:
${p.list}

Work in rounds: change, make 4-8 stills (folders /home/user/work/chapter-2/stills/r20b-p${p.n}-a, -b, ...), look at the full stills with the Read tool (not only the contact sheet), fix, repeat. Keep at most 3 camera moves per shot and run the camera check (it must say 0 problem(s)): cd ${KIT} && PAPER_FILM_PAGES=${p.n} timeout 300 node paper-film/tools/render-paper-film.mjs cinema-test-pages --camera /home/user/work/chapter-2/stills/r20b-p${p.n}-camera.json 3 && python3 -I paper-film/tools/camera_audit.py /home/user/work/chapter-2/stills/r20b-p${p.n}-camera.json --window ${p.window}
Only edit page-${p.n}.js (or page-${p.n}-something.js). Spend no money. Do not commit. Other helpers share the machine: one render at a time, 4-8 stills per round. Finish with 8-10 stills covering every problem moment and the page's first and last moments; report as asked.`

phase('Fix')
const reports = await parallel(PAGES.map((p) => () => agent(prompt(p), { label: `fix page ${p.n}`, phase: 'Fix', schema: REPORT, effort: 'medium' })))
const done = reports.filter(Boolean)

phase('Check')
const check = await agent(`You are a fresh, strict reviewer for pages of one film that helpers just fixed. Read ${GUIDE_2}. For each page below: the reviewer's earlier list of problems is in its brief; the helper's report says what it changed. For every listed problem, look at the full stills at that moment (render your own if needed: cd ${KIT} && PAPER_FILM_PAGES=N timeout 900 node paper-film/tools/render-paper-film.mjs cinema-test-pages /home/user/work/chapter-2/stills/r20b-check-pN --stills T1 T2 ... ; one render at a time) and say fixed or not fixed. Then look for new problems the fixes caused (clipping, words in the bottom 380 px or right 140 px, empty frames, unreadable text, camera moves over 3 per shot: run camera_audit.py per page as in the guide). Be concrete: page, time, what, smallest fix. End with a one-line verdict per page: ready or not. Do not edit files.
Briefs:
${PAGES.map((p) => `PAGE ${p.n} (window ${p.window}):\n${p.list}`).join('\n\n')}
Helper reports:
${JSON.stringify(done, null, 1)}`, { label: 'check fixes', phase: 'Check', effort: 'medium' })

return { reports: done, check }
