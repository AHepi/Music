export const meta = {
  name: 'round-20-page-fixes',
  description: 'Seven page helpers apply the camera rule, frame filling and no-clipping fixes to pages 1, 4, 5, 6, 7, 9, 10; then one reviewer checks them together',
  phases: [
    { title: 'Fix pages', detail: 'one helper per page: still camera (max 3 moves per shot), the flagged fixes, stills and camera check' },
    { title: 'Review', detail: 'one reviewer looks at every sheet and camera report' },
  ],
}

const KIT = '/home/user/work/paper-pop-up-film-kit'
const GUIDE_1 = '/home/user/work/chapter-2/reference/20 Guide - building a cinema page.md'
const GUIDE_2 = '/home/user/work/chapter-2/reference/21 Guide - camera rule, filling the frame, no clipping.md'
const BEFORE = '/home/user/work/chapter-2/feedback-20/camera-before.txt'

const PAGES = [
  { n: 1, window: '0.0 20.4', brief: `Page 1 ("So... won't creating new money just cause inflation?"): an invented politician at a lectern in a painted chamber, then a painted supermarket checkout with a basket cut-out on the conveyor belt and price tags.
The viewer's screenshots: /home/user/work/chapter-2/feedback-20/shot-1.jpg (00:01), shot-15.jpg (00:15), shot-17.jpg (00:17).
Fixes asked for:
1. "His face is weirdly over saturated compared to other faces and pop ups." Already fixed in the piece files (all three politician layers were calmed). Just check in a still that he now matches the room and the other cut-outs; say if he still looks too strong.
2. "The price tags clip other objects and the bread basket clips the conveyor belt." Re-place the price tags so every tag floats in clear air in front of the shelves (room.clearance at least 0.15 at every moment, including while they swing or pop up), not overlapping each other, the basket or the payment terminal. Make the basket stand ON the belt: its bottom edge exactly on the belt surface (room.pointAt) with clearance at least 0.03, not sunk into it. Keep the "$104.10" basket tag reading clearly.
3. The camera currently creeps for the whole 20 seconds without ever stopping. Rewrite it with kit.stillShot: probably one shot in the chamber and one at the checkout (the page already cuts between the two rooms), each still except for at most 3 meaningful moves (for example a zoom in onto the basket when "the whole basket" is said).` },
  { n: 4, window: '74.7 95.1', brief: `Page 4 (Glasgow tenements, rents, the rent strikes): camera only, plus anything that clips.
The camera check found: shot 1 has a long "pan left + zoom in" (77.5-82.6 s), drifts, another zoom in; shot 2 (92.2-95.1 s) zooms the whole time and never holds. Rewrite each shot with kit.stillShot: still, at most 3 meaningful moves each, short and clear. Keep everything that reads well now (the earlier critique fixed this page's "Homes can't be built" change; keep it working). Check nothing passes through the painted street.` },
  { n: 5, window: '95.2 128.4', brief: `Page 5 (a Tokyo noodle shop for Japan, then a City of London bank street, "THE GAINS", Bank of England study 2012): two shots.
The viewer's screenshot: /home/user/work/chapter-2/feedback-20/shot-126.jpg (02:06). Their words: "The coins disappear through the ground and the both the notes and coins have no reflection. Maybe the source image shouldn't depict a wet ground."
Fixes asked for:
1. A new painting of the bank street with a DRY pavement is ready as a painted room: '406b-bg-london-bank-dry' (files ${KIT}/assets/reliefs/inflation-chapter-2/406b-bg-london-bank-dry.jpg and -depth.png; look at the jpg first). Its composition differs from the old one: the bank is seen at an angle on the left half, with open dry flagstone pavement on the right and across the bottom. Switch the bank shot to it (kit.relief('406b-bg-london-bank-dry', { near: 6, far: 70, fov: 40 }) unless you find better numbers with relief_points.py) and re-place the towers of notes and coins and everything else on the open pavement with room.pointAt, big enough to read (fill the frame), with soft contact shadows so they sit on the ground.
2. Coins must never pass through the ground: falling coins stop exactly on the pavement surface or on top of a tower and stay there (clearance >= 0 at every moment). Check landing moments with close stills.
3. The camera: rewrite both shots with kit.stillShot (still; at most 3 meaningful moves per shot). The check found drifts in the bank shot and a long zoom in the noodle shop shot.` },
  { n: 6, window: '128.5 155.9', brief: `Page 6 (the Ruhr, Germany 1923, hyperinflation): camera only, plus anything that clips.
The camera check found 6 moves in one shot (drifts, zoom in 136.6-142.1, zoom out 143.1-145.9, more drifts, zoom out 151.7-155.5). Rewrite with kit.stillShot: still, at most 3 meaningful moves per shot; if the page truly needs more, cut to a second shot. Keep everything that reads well now.` },
  { n: 7, window: '156.0 180.2', brief: `Page 7 (the 1973 oil shock at a petrol station, then New Zealand prices with and without fuel): camera only, plus anything that clips.
The camera check found: shot 1 (156.0-171.5 s) is one long "pan down + zoom in" that never holds; shot 2 zooms in for 5.6 s. Rewrite each shot with kit.stillShot: still, at most 3 meaningful moves each. Keep the New Zealand bars panel reading well.` },
  { n: 9, window: '208.3 238.3', brief: `Page 9 (who pays: workers, wages, Mattei's argument, the book "The Capital Order"): a painted street/factory gate with a queue of workers, a pay packet (envelope) marked WAGES, an iron weight, and the book.
The viewer's screenshot: /home/user/work/chapter-2/feedback-20/shot-235.jpg (03:55). Their words: "The envelope clips the workers and the ground. Also the book probably needs to be significantly bigger because it's being treated as authority. Zooming out should fix the clipping issue and placing the book further back should leave space for the workers and envelope."
Fixes asked for:
1. The book: significantly bigger (it stands for authority: it should tower over the workers, roughly as tall as the frame's middle third or more), placed further back in the room (behind the workers and the envelope, on the floor point, standing upright, clearance >= 0.05), still clearly readable, with Mattei's name kept.
2. The envelope must not pass into the workers or the ground at any moment (clearance and boxesOverlap; put it in front of the workers, in its own space, its bottom on the ground).
3. Zoom out: the shot starts wider so workers, envelope and book all have room; then the camera holds still with at most 3 meaningful moves per shot (kit.stillShot). The check found a long pan down 210.9-220.5 s and a zoom in 222.1-237.8 s that never stops.` },
  { n: 10, window: '238.4 270.3', brief: `Page 10 (the ending, back to the politician and the question; Reserve Bank 5.6%, rate dial): camera only, plus anything that clips.
The politician's face pieces were calmed in colour this round (the viewer said "His face is weirdly over saturated compared to other faces and pop ups"); check in a still that he matches.
The camera check found drifts and a zoom in 262.0-266.7 s; it passes the 3-move count but drifts. Rewrite with kit.stillShot: still, at most 3 meaningful moves per shot. The earlier critique fixed this page's 5.6% so it holds still and the dial moves the right way; keep that.` },
]

const REPORT = { type: 'object', properties: {
  page: { type: 'number' },
  sheet: { type: 'string', description: 'path of the final contact sheet' },
  camera_check: { type: 'string', description: 'the full camera_audit.py output for the page window' },
  shots: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, moves: { type: 'string', description: 'each move: kind, from-to word, and why it is essential' } }, required: ['name', 'moves'] } },
  fixes: { type: 'array', items: { type: 'string' }, description: 'what was changed for each fix asked for, with clearance numbers measured' },
  unsure: { type: 'array', items: { type: 'string' } },
  shared_problems: { type: 'array', items: { type: 'string' } },
}, required: ['page', 'sheet', 'camera_check', 'shots', 'fixes', 'unsure', 'shared_problems'] }

const prompt = (p) => `You are fixing page ${p.n} of a finished cinematic explainer film (chapter 2, "What really causes inflation"; vertical 1080x1920, three.js). The viewer watched it on a phone and asked for changes.
Read both guides completely first and follow them: ${GUIDE_1} and then ${GUIDE_2} (the second one is this round's rules: the camera rule, filling the frame, nothing passing through anything). The worked example of the new camera is ${KIT}/paper-film/scenes/inflation-chapter-2/page-2.js. The camera check of the film before this round is in ${BEFORE}.

Your page: ${KIT}/paper-film/scenes/inflation-chapter-2/page-${p.n}.js. Its window on the timeline: ${p.window} seconds (use these as FROM TO for camera_audit.py --window).

${p.brief}

Work in rounds: change the page, make 4-8 stills (folders /home/user/work/chapter-2/stills/r20-p${p.n}-a, -b, ...), make the contact sheet, look at it with the Read tool like a film director (is the thing she is talking about clear, lit, in focus, filling the frame? is anything clipping? are words readable and inside the safe area?), fix, repeat. Run the camera check; it must say 0 problem(s). Finish with a final round of 8-12 stills covering every beat including the first and last moments of the window, and report as asked. Only edit page-${p.n}.js (or page-${p.n}-something.js). Spend no money. Do not commit.`

phase('Fix pages')
const reports = await parallel(PAGES.map((p) => () => agent(prompt(p), { label: `page ${p.n}`, phase: 'Fix pages', schema: REPORT, effort: 'medium' })))
const done = reports.filter(Boolean)
const missing = PAGES.filter((p, i) => !reports[i]).map((p) => p.n)
if (missing.length) log(`No report from page(s): ${missing.join(', ')}`)

phase('Review')
const review = await agent(`You are checking pages of one film that several helpers just fixed in parallel. Read ${GUIDE_2} (this round's rules). For each report below, look at its final contact sheet with the Read tool (and single stills where needed) and read its camera check. Judge strictly against the viewer's words quoted in the guide:
- Does the camera hold still except for at most 3 meaningful moves per shot, each matching the grammar (zoom in/out, pan left/right/up/down, move up/down) and landing a point she makes? Run the camera check yourself for each page: cd ${KIT} && PAPER_FILM_PAGES=N timeout 300 node paper-film/tools/render-paper-film.mjs cinema-test-pages --camera /home/user/work/chapter-2/stills/r20-review-pN.json 3 && python3 -I paper-film/tools/camera_audit.py /home/user/work/chapter-2/stills/r20-review-pN.json --window FROM TO (windows: ${PAGES.map((p) => `page ${p.n}: ${p.window}`).join('; ')}). Run them one at a time.
- Does anything pass into the painting, the floor or another thing (tags, basket, envelope, coins)?
- Does the frame feel full (no big empty dark areas), is the subject big enough, are words readable and clear of the phone-button zones?
- Did each page get the fixes its brief asked for (page 1: tags, basket; page 5: dry street, coins landing; page 9: big book further back, envelope clear, wider start)?
List every problem: page, time, what, smallest fix. Then a short plain verdict per page: ready or not. Do not edit files.
Reports:
${JSON.stringify(done, null, 1)}`, { label: 'review', phase: 'Review', effort: 'medium' })

return { reports: done, missing, review }
