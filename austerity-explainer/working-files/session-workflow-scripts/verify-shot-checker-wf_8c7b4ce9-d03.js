export const meta = {
  name: 'verify-shot-checker',
  description: 'Independent helpers try to break the shot checker: follow its advice, plant new faults, read the code, read the reports as the user; a skeptic merges',
  phases: [
    { title: 'Try to break it', detail: 'four independent checks of the shot checker' },
    { title: 'Merge', detail: 'a skeptic checks every claim and ranks the fixes' },
  ],
}

const CONTEXT = `
CONTEXT (read carefully; you are checking someone else's tool, not building the film):
The project makes short explainer films. A 3D street (a 1926 pit village) is built in Blender, props are placed by a script, and a
camera frames a "notice corner": a printed lockout notice on a wooden board, an oil-drum fire, a chair with a lantern on its seat, a pail.
A new tool checks a shot's composition automatically and says what is wrong and what to change in metres:
  - /home/user/work/paper-pop-up-film-kit/paper-film/blender/shot_facts.py   (runs inside Blender: flat-colour pictures of each prop group, camera facts, what each prop stands on, lights)
  - /home/user/work/paper-pop-up-film-kit/paper-film/tools/check_shot.py     (reads those facts, writes report.md and marked.jpg)
  - /home/user/work/paper-pop-up-film-kit/paper-film/tools/check-shot.sh     (runs both)
  - /home/user/work/paper-pop-up-film-kit/paper-film/blender/tests/break_scene.py (moves objects by name prefix: --break "NAME:dx,dy,dz;NAME2:dx,dy,dz")
  - the check file: /home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json
  - the scene script: /home/user/work/paper-pop-up-film-kit/paper-film/blender/pit-village/assemble_notice_corner.py (--view end puts the camera at the composed frame)
  - the composing rules it checks: /home/user/Music/austerity-explainer/film-kit/07 Composing a shot.md
Measured scenes and reports (all made with the current tool) are in
  S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks
  - composed-end (the good frame; its finished picture is $S/../composed-end-2.png) and seven planted faults:
    a-camera-too-high (--camera-at 3.25,16.6,3.52 --yaw 5.9 --fov 60), b-pail-in-the-air (wooden-pail:0.55,0,5.0),
    c-chair-pushed-back (kitchen-chair:0,0.45,0), d-pail-out-of-frame (wooden-pail:0.25,0,0), e-camera-tilted (--pitch 3),
    f-drum-edge-touches-chair (brazier:-0.15,0,0), g-lantern-on-the-pavement (hurricane-lantern/lantern_flame/lantern_light: -0.45,-0.7,-0.53)
  - each has a facts folder $S/NAME and a report folder $S/NAME-report (report.md, marked.jpg); $S/measure-all.sh shows the exact Blender commands.
  - $S/old-picture-report is the good frame checked against an older render with a false hard shadow (a render fault).
How to measure a scene (about 30 seconds; run Blender jobs ONE AT A TIME, never several at once; the machine has 4 cores):
  cd /home/user/work/paper-pop-up-film-kit && DISPLAY=:96 timeout 600 /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b assets/models/pit-village/street.blend \\
    --python paper-film/blender/pit-village/assemble_notice_corner.py --python paper-film/blender/tests/break_scene.py --python paper-film/blender/shot_facts.py -- \\
    --view end --check examples/notice-corner/shot-check.json --facts OUT_FOLDER [--break "..."] [--camera-at x,y,z --yaw DEG [--pitch DEG] --fov DEG] > OUT_FOLDER.log 2>&1
  then: python3 paper-film/tools/check_shot.py --check examples/notice-corner/shot-check.json --facts OUT_FOLDER [--picture PNG] --out OUT_FOLDER-report
  (the camera match makes check_shot.py take about 15 seconds). The composed camera is at Blender (2.96, 17.85, 3.1882), turn (yaw) 6.87 degrees, view 60.4 degrees top to bottom.
  Blender coordinates: x across the street (+ is right looking up the street), y up the street, z up. The street rises 4 degrees. Pavement height = y*tan(4 deg)+0.13.
Rules for you: do not edit any file outside your own new folder under $S/verify-NAME (make it). Do not touch /home/user/Music (a public repo).
Do not spend money or call any paid picture, video or speech service. Never use pkill/killall or broad kill patterns.
Report facts you checked yourself, with the numbers and file paths that show them. Say plainly what you did not check.`

const FINDINGS = {
  type: 'object',
  properties: {
    verdict: { type: 'string', description: 'two to five sentences: does the tool do its job on what you checked?' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          severity: { type: 'string', enum: ['wrong answer', 'misleading', 'minor'] },
          where: { type: 'string', description: 'file and function, or report and problem number' },
          evidence: { type: 'string', description: 'what you ran or looked at, and the numbers that show it' },
          fix: { type: 'string', description: 'the concrete change to the tool or the wording' },
        },
        required: ['title', 'severity', 'where', 'evidence', 'fix'],
      },
    },
    not_checked: { type: 'string' },
  },
  required: ['verdict', 'findings', 'not_checked'],
}

const LENSES = [
  { key: 'follow-the-advice', prompt: `${CONTEXT}

YOUR JOB: FOLLOW THE ADVICE AND SEE IF IT WORKS. The strongest test of a tool that says "move X by N metres" is to do exactly that and check again.
For each of these reports, take the "Fix first" advice (and, where it is short, the next one) and apply it LITERALLY to that scene, using
--break (to move props) or --camera-at/--yaw/--fov (to move the camera) on top of the scene's own planted break. Re-measure and re-check.
  1. a-camera-too-high: apply the camera fix it gives first (lower/sideways/turn) to its camera.
  2. c-chair-pushed-back: move the chair back under the lantern by the amount the facts imply (the report says one of them moved; chair y went 21.75 -> 22.20).
  3. d-pail-out-of-frame: apply its rule 12 fix (camera sideways move without turning, plus the pail move it names).
  4. f-drum-edge-touches-chair: apply "move drum about 0.08 m to the right".
  5. composed-end: apply its rule 12 fix (move the camera to the right without turning it, by the metres it gives) and check whether rule 12 then passes and whether rule 1 (lines meet at the board's edge) still passes.
For each: did the targeted problem go away? Did the fix's size (metres) turn out right, too small or too big (by how much)? Did the fix create new problems?
Measure one scene at a time. Put everything in $S/verify-follow/.` },
  { key: 'new-faults', prompt: `${CONTEXT}

YOUR JOB: PLANT NEW FAULTS THE TOOL HAS NOT SEEN, and judge whether its report finds them and gives a fix that would really work.
Make at least four new broken scenes (one fault each), for example:
  - the board (objects named notice-board*, notice* and tacks*: move all three prefixes together) moved about 0.8 m along the street away from the camera, so the street's lines no longer meet at its edge (rule 1);
  - a work prop (wooden-barrel or dustbins or coal-sacks) moved into the bottom-left foreground of the frame on the road (rule 8: nothing big where the eye enters);
  - the camera's view widened to 75 degrees top to bottom (--camera-at 2.96,17.85,3.1882 --yaw 6.87 --fov 75);
  - the gas-lamp-post moved so its post edge just touches the board's edge on screen (rule 4);
  - anything else you think the tool would miss.
First look at the scene's facts ($S/composed-end/facts.json: each group's centre, size, distance) to choose sensible moves; check positions on screen with the flat-colour picture ids.png.
For each new scene: is the planted fault reported? Is it "Fix first" (or ranked sensibly)? Would the fix work (check its size against the move you planted)? Any false alarms?
Measure one scene at a time. Put everything in $S/verify-new/.` },
  { key: 'code', prompt: `${CONTEXT}

YOUR JOB: READ THE CODE FOR MISTAKES. Read check_shot.py and shot_facts.py in full. Look for: wrong signs (left/right, up/down, nearer/further, turn direction),
wrong units (pixels vs fractions vs metres; the rules file sets pixel limits on a 1,536-wide frame), formulas that are wrong (check the geometry yourself:
pinhole camera, focal length in pixels = (height/2)/tan(vertical view/2), metres per pixel = distance/focal), crashes on unusual input, and checks that can
never fail or never pass. Try it on unusual input without Blender: copy a facts folder into $S/verify-code/ and edit the copy (remove a group's solo picture,
remove keys such as stands_on or lights, make a check file with no "reference", no "title_zone", no "stands_on", or a landscape size), then run check_shot.py on it.
Also check the ranking (which problem becomes "Fix first") and the "<<name>>" cross-references in the text. Report concrete bugs with the command that shows each.` },
  { key: 'plain-words', prompt: `${CONTEXT}

YOUR JOB: READ THE REPORTS AS THE USER WILL. The user is not a programmer. They want everyday words, one word for each thing (never a synonym), no jargon or
abbreviations (a needed technical word gets a one-sentence plain explanation), concrete numbers, and one clear next step. Read every $S/*-report/report.md and
look at every marked.jpg (open the images). For each report: could the user act on "Fix first" without help? Which sentences are confusing, contradictory,
too long, or use two words for one thing (e.g. "ground" and "pavement", "turn" and "yaw", "view" and "lens")? Are the marks on marked.jpg readable, and does
each numbered mark match the problem with that number? Is anything in the report wrong when you compare it with the picture? Give exact rewordings.` },
]

phase('Try to break it')
const results = await parallel(LENSES.map(l => () =>
  agent(l.prompt, { label: `verify:${l.key}`, phase: 'Try to break it', schema: FINDINGS }).then(r => r ? { lens: l.key, ...r } : null)))
const found = results.filter(Boolean)
log(`${found.length} of ${LENSES.length} checks returned; ${found.reduce((n, r) => n + r.findings.length, 0)} findings`)

phase('Merge')
const merged = await agent(`${CONTEXT}

You are a skeptical senior reviewer. Four helpers checked the shot checker. Their findings are below as JSON. For EVERY finding, check it yourself
(open the file, re-run the command, look at the picture or the numbers). Reject what you cannot confirm. Merge duplicates. Then rank what survives:
"must fix" (the tool gives a wrong answer or advice that would make the shot worse), "should fix" (misleading or confusing), "leave" (minor or not worth the code).
For each surviving item give the exact change to make (function and what to change, or the exact new wording).

FINDINGS:
${JSON.stringify(found, null, 1)}`, {
  label: 'skeptic', phase: 'Merge',
  schema: {
    type: 'object',
    properties: {
      summary: { type: 'string' },
      must_fix: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, evidence: { type: 'string' }, change: { type: 'string' } }, required: ['title', 'evidence', 'change'] } },
      should_fix: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, evidence: { type: 'string' }, change: { type: 'string' } }, required: ['title', 'evidence', 'change'] } },
      leave: { type: 'array', items: { type: 'string' } },
      rejected: { type: 'array', items: { type: 'string' } },
    },
    required: ['summary', 'must_fix', 'should_fix', 'leave', 'rejected'],
  },
})
return { checks: found, merged }
